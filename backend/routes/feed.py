"""Feed system endpoints - 信息流管理."""
from flask import Blueprint, request, jsonify
from bson import ObjectId

from storage.post_store import PostStore
from storage.user_store import UserStore
from storage.corner_store import CornerStore
from utils import jwt_required, jwt_optional, check_post_visibility, is_following_user
from services.recommendation_service import get_recommendation_service

bp = Blueprint('feed', __name__)
post_store = PostStore()
user_store = UserStore()
corner_store = CornerStore()
recommendation_service = get_recommendation_service()


def expand_post_feed_data(post):
    """
    扩展帖子数据以用于信息流展示。

    Args:
        post: Post document

    Returns:
        dict: Expanded post data
    """
    if not post:
        return None

    expanded = dict(post)
    expanded['_id'] = str(post['_id'])
    expanded['user_id'] = str(post['user_id'])

    # Get creator info
    creator = user_store.get_user_by_id(post['user_id'])
    if creator:
        expanded['username'] = creator.get('username', '')
    else:
        expanded['username'] = ''

    # Generate media URLs
    media_urls = []
    for file_id in post.get('media_files', []):
        media_urls.append(f'/api/media/{str(file_id)}')
    expanded['media_urls'] = media_urls

    # Convert ObjectIds to strings
    expanded['corner_ids'] = [str(cid) for cid in post.get('corner_ids', [])]
    expanded['media_files'] = [str(fid) for fid in post.get('media_files', [])]

    # Convert route corner_ids to strings
    if 'route' in expanded and expanded['route'] and 'corner_ids' in expanded['route']:
        expanded['route']['corner_ids'] = [str(cid) for cid in expanded['route']['corner_ids']]

    return expanded


@bp.route('/api/feed/following', methods=['GET'])
@jwt_required
def get_following_feed():
    """
    获取当前用户关注的所有用户发布的最新帖子。

    Query parameters:
        - limit: 每页数量（默认 20）
        - skip: 跳过数量（用于分页）
        - include_own: 是否包含自己的帖子（默认 true）

    Returns:
        JSON with posts list
    """
    current_user_id = request.user_id

    # Get query parameters
    try:
        limit = int(request.args.get('limit', 20))
        limit = min(limit, 100)
    except ValueError:
        limit = 20

    try:
        skip = int(request.args.get('skip', 0))
        if skip < 0:
            skip = 0
    except ValueError:
        skip = 0

    include_own = request.args.get('include_own', 'true').lower() == 'true'

    try:
        current_user_obj = ObjectId(current_user_id)
    except Exception:
        return jsonify({'error': 'Invalid user ID'}), 400

    # Get current user's following list
    current_user = user_store.get_user_by_id(current_user_obj)
    if not current_user:
        return jsonify({'error': 'User not found'}), 404

    following_ids = current_user.get('following', [])

    # Build user IDs to query (following users + optionally self)
    user_ids_to_query = list(following_ids)
    if include_own:
        user_ids_to_query.append(current_user_obj)

    if not user_ids_to_query:
        return jsonify({
            'success': True,
            'data': {
                'posts': [],
                'total': 0,
                'limit': limit,
                'skip': skip
            }
        })

    # Query posts by users
    # Use aggregation pipeline for better performance
    try:
        pipeline = [
            {
                '$match': {
                    'user_id': {'$in': user_ids_to_query},
                    'visibility': {'$in': ['public', 'followers']}
                }
            },
            {'$sort': {'created_at': -1}},
            {'$skip': skip},
            {'$limit': limit}
        ]

        posts = list(post_store.collection.aggregate(pipeline))

        # Get total count
        total_count = post_store.collection.count_documents({
            'user_id': {'$in': user_ids_to_query},
            'visibility': {'$in': ['public', 'followers']}
        })

        # Filter posts by visibility for current user
        filtered_posts = []
        for post in posts:
            if check_post_visibility(current_user_id, post, is_following_user):
                filtered_posts.append(expand_post_feed_data(post))

    except Exception as e:
        return jsonify({'error': f'Failed to get feed: {str(e)}'}), 500

    return jsonify({
        'success': True,
        'data': {
            'posts': filtered_posts,
            'total': total_count,
            'limit': limit,
            'skip': skip
        }
    })


@bp.route('/api/feed/status', methods=['GET'])
@jwt_required
def get_feed_status():
    """
    获取当前用户的关注状态摘要。

    Returns:
        JSON with status summary
    """
    current_user_id = request.user_id

    try:
        current_user_obj = ObjectId(current_user_id)
    except Exception:
        return jsonify({'error': 'Invalid user ID'}), 400

    # Get user data
    user = user_store.get_user_by_id(current_user_obj)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Get following and followers counts
    following_count = len(user.get('following', []))
    followers_count = len(user.get('followers', []))

    # Note: unread_posts_count is not implemented yet
    # This would require tracking user's last read timestamp
    return jsonify({
        'success': True,
        'data': {
            'following_count': following_count,
            'followers_count': followers_count,
            'unread_posts_count': 0,
            'last_checked_at': None
        }
    })


@bp.route('/api/feed/public', methods=['GET'])
@jwt_optional
def get_public_feed():
    """
    获取公开帖子流（无需登录）。

    Query parameters:
        - limit: 每页数量（默认 20）
        - skip: 跳过数量（用于分页）

    Returns:
        JSON with public posts
    """
    # Get query parameters
    try:
        limit = int(request.args.get('limit', 20))
        limit = min(limit, 100)
    except ValueError:
        limit = 20

    try:
        skip = int(request.args.get('skip', 0))
        if skip < 0:
            skip = 0
    except ValueError:
        skip = 0

    # Get current user ID for visibility filtering
    current_user_id = getattr(request, 'user_id', None)

    try:
        # Query public posts
        sort_field = 'created_at'
        sort_order = -1

        posts = post_store.find(
            {'visibility': 'public'},
            limit=limit,
            skip=skip,
            sort=[(sort_field, sort_order)]
        )

        # Get total count
        total = post_store.collection.count_documents({'visibility': 'public'})

        # Expand post data
        expanded_posts = []
        for post in posts:
            if check_post_visibility(current_user_id, post, is_following_user):
                expanded_posts.append(expand_post_feed_data(post))

    except Exception as e:
        return jsonify({'error': f'Failed to get public feed: {str(e)}'}), 500

    return jsonify({
        'success': True,
        'data': {
            'posts': expanded_posts,
            'total': total,
            'limit': limit,
            'skip': skip
        }
    })


@bp.route('/api/feed', methods=['GET'])
@jwt_optional
def get_comprehensive_feed():
    """
    获取综合信息流,混合推荐帖子和关注用户的帖子.

    Query parameters:
        - type: 信息流类型 (all, recommendation, following, 默认 all)
        - lat: 用户当前纬度(可选)
        - lng: 用户当前经度(可选)
        - limit: 返回帖子数量(默认 20)

    Returns:
        JSON with feed posts
    """
    current_user_id = getattr(request, 'user_id', None)

    # Get query parameters
    feed_type = request.args.get('type', 'all')

    try:
        limit = int(request.args.get('limit', 20))
        limit = min(limit, 100)
    except ValueError:
        limit = 20

    # Get user location
    user_location = None
    lat = request.args.get('lat')
    lng = request.args.get('lng')

    if lat and lng:
        try:
            user_location = (float(lat), float(lng))
            # Validate coordinates
            if not (-90 <= user_location[0] <= 90 and -180 <= user_location[1] <= 180):
                return jsonify({'error': 'Invalid coordinates'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid coordinates format'}), 400

    posts = []

    # Get posts based on feed type
    if feed_type == 'all':
        # Mix recommendation and following posts
        limit_per_type = limit // 2

        # Get recommendation posts
        try:
            recommend_posts = recommendation_service.recommend_feed(
                user_id=current_user_id,
                user_location=user_location,
                limit=limit_per_type
            )
        except Exception:
            recommend_posts = []

        # Get following posts
        following_posts = []
        if current_user_id:
            try:
                current_user_obj = ObjectId(current_user_id)
                current_user = user_store.get_user_by_id(current_user_obj)
                if current_user:
                    following_ids = current_user.get('following', [])
                    user_ids_to_query = list(following_ids) + [current_user_obj]

                    pipeline = [
                        {
                            '$match': {
                                'user_id': {'$in': user_ids_to_query},
                                'visibility': {'$in': ['public', 'followers']}
                            }
                        },
                        {'$sort': {'created_at': -1}},
                        {'$limit': limit_per_type}
                    ]
                    following_posts = list(post_store.collection.aggregate(pipeline))
            except Exception:
                pass

        # Mix and deduplicate
        post_dict = {}
        for post in recommend_posts:
            post_dict[str(post['_id'])] = post
        for post in following_posts:
            post_dict[str(post['_id'])] = post

        posts = list(post_dict.values())[:limit]

    elif feed_type == 'recommendation':
        # Only recommendation posts
        try:
            posts = recommendation_service.recommend_feed(
                user_id=current_user_id,
                user_location=user_location,
                limit=limit
            )
        except Exception as e:
            return jsonify({'error': f'Failed to get recommendations: {str(e)}'}), 500

    elif feed_type == 'following':
        # Only following posts
        if not current_user_id:
            return jsonify({
                'success': True,
                'data': {
                    'posts': [],
                    'feed_type': 'following',
                    'message': 'Login required to view following feed'
                }
            })

        try:
            current_user_obj = ObjectId(current_user_id)
            current_user = user_store.get_user_by_id(current_user_obj)
            if not current_user:
                return jsonify({'error': 'User not found'}), 404

            following_ids = current_user.get('following', [])
            user_ids_to_query = list(following_ids) + [current_user_obj]

            if not user_ids_to_query:
                posts = []
            else:
                pipeline = [
                    {
                        '$match': {
                            'user_id': {'$in': user_ids_to_query},
                            'visibility': {'$in': ['public', 'followers']}
                        }
                    },
                    {'$sort': {'created_at': -1}},
                    {'$limit': limit}
                ]
                posts = list(post_store.collection.aggregate(pipeline))
        except Exception as e:
            return jsonify({'error': f'Failed to get following feed: {str(e)}'}), 500

    else:
        return jsonify({'error': 'Invalid feed type. Must be "all", "recommendation", or "following"'}), 400

    # Enrich posts with related data
    enriched_posts = []
    if posts:
        # Batch query users
        user_ids = list(set([post['user_id'] for post in posts if 'user_id' in post]))
        users = {}
        if user_ids:
            users_list = list(user_store.collection.find({"_id": {"$in": user_ids}}))
            users = {str(u['_id']): u for u in users_list}

        # Batch query corners
        corner_ids = set()
        for post in posts:
            for cid in post.get('corner_ids', []):
                corner_ids.add(cid)
        corners = {}
        if corner_ids:
            corners_list = list(corner_store.collection.find({"_id": {"$in": list(corner_ids)}}))
            corners = {str(c['_id']): c for c in corners_list}

        # Enrich each post
        for post in posts:
            post_data = {
                '_id': str(post['_id']),
                'user_id': str(post['user_id']),
                'title': post.get('title', ''),
                'description': post.get('description', ''),
                'media_type': post.get('media_type'),
                'media_files': [str(fid) for fid in post.get('media_files', [])],
                'tags': post.get('tags', []),
                'visibility': post.get('visibility'),
                'created_at': post.get('created_at'),
                'stats': post.get('stats', {})
            }

            # Add username
            user = users.get(str(post['user_id']))
            post_data['username'] = user.get('username', '') if user else ''

            # Add corner information
            post_corners = []
            for cid in post.get('corner_ids', []):
                corner = corners.get(str(cid))
                if corner:
                    post_corners.append({
                        'corner_id': str(cid),
                        'name': corner.get('name', '')
                    })
            post_data['corners'] = post_corners

            # Add route if exists
            if 'route' in post and post['route']:
                route_data = post['route'].copy()
                route_data['corner_ids'] = [str(cid) for cid in route_data.get('corner_ids', [])]
                post_data['route'] = route_data

            # Check visibility
            if check_post_visibility(current_user_id, post, is_following_user):
                enriched_posts.append(post_data)

    # Build response
    response_data = {
        'success': True,
        'data': {
            'posts': enriched_posts,
            'feed_type': feed_type
        }
    }

    # Add user location if provided
    if user_location:
        response_data['data']['user_location'] = {
            'lat': user_location[0],
            'lng': user_location[1]
        }

    return jsonify(response_data)