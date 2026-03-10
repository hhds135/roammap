"""Feed system endpoints - 信息流管理."""
from flask import Blueprint, request, jsonify
from bson import ObjectId

from storage.post_store import PostStore
from storage.user_store import UserStore
from utils import jwt_required, jwt_optional, check_post_visibility, is_following_user

bp = Blueprint('feed', __name__)
post_store = PostStore()
user_store = UserStore()


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