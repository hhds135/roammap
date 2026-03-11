"""View history tracking endpoints - 浏览历史追踪."""
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from bson import ObjectId

from storage.view_history_store import ViewHistoryStore
from storage.post_store import PostStore
from storage.user_store import UserStore
from storage.connection import MongoDBConnection, get_db
from utils import jwt_required, jwt_optional
from config import Config

bp = Blueprint('view_history', __name__)

# Initialize MongoDB connection if not already connected
try:
    if get_db() is None:
        conn = MongoDBConnection()
        conn.connect()
except Exception:
    pass

view_history_store = ViewHistoryStore()
post_store = PostStore()
user_store = UserStore()

# View history TTL in days
VIEW_HISTORY_TTL_DAYS = 30


@bp.route('/api/posts/<post_id>/view', methods=['POST'])
@jwt_required
def record_post_view(post_id):
    """
    记录用户浏览帖子的行为。

    Args:
        post_id: 帖子 ID

    Request body (JSON):
        - view_duration: 浏览时长(毫秒,可选)

    Returns:
        JSON with view record data
    """
    current_user_id = request.user_id

    try:
        post_obj = ObjectId(post_id)
        current_user_obj = ObjectId(current_user_id)
    except Exception:
        return jsonify({'error': 'Invalid post ID or user ID'}), 400

    # Check if post exists
    post = post_store.get_post_by_id(post_obj)
    if not post:
        return jsonify({'error': 'Post not found'}), 404

    # Get view duration from request body
    data = request.get_json() or {}
    view_duration = int(data.get('view_duration', 0))

    if view_duration < 0:
        return jsonify({'error': 'view_duration must be non-negative'}), 400

    # Record view
    try:
        view_id = view_history_store.create_view(
            user_id=current_user_obj,
            post_id=post_obj,
            view_duration=view_duration
        )

        return jsonify({
            'success': True,
            'message': 'View recorded successfully',
            'data': {
                'view_id': str(view_id),
                'post_id': post_id,
                'user_id': current_user_id,
                'view_duration': view_duration,
                'created_at': datetime.utcnow().isoformat()
            }
        }), 201

    except Exception as e:
        return jsonify({'error': f'Failed to record view: {str(e)}'}), 500


@bp.route('/api/users/<user_id>/view-history', methods=['GET'])
@jwt_required
def get_user_view_history(user_id):
    """
    获取用户的浏览历史记录。

    Args:
        user_id: 用户 ID

    Query parameters:
        - limit: 每页数量(默认 20)
        - skip: 跳过数量(用于分页)
        - min_duration: 最小浏览时长过滤(毫秒,默认 1000)

    Returns:
        JSON with view history list
    """
    current_user_id = request.user_id

    try:
        user_obj = ObjectId(user_id)
    except Exception:
        return jsonify({'error': 'Invalid user ID'}), 400

    # Users can only view their own history
    if current_user_id != user_id:
        return jsonify({'error': 'Access denied'}), 403

    # Get pagination parameters
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

    try:
        min_duration = int(request.args.get('min_duration', 1000))
    except ValueError:
        min_duration = 1000

    # Get view history
    views = view_history_store.get_views_by_user(user_obj, limit=limit + skip)

    # Filter by minimum duration and apply pagination
    filtered_views = [
        v for v in views
        if v.get('view_duration', 0) >= min_duration
    ]
    paginated_views = filtered_views[skip:skip + limit]

    # Get total count
    total = len(filtered_views)

    # Expand post information
    result = []
    for view in paginated_views:
        post = post_store.get_post_by_id(view['post_id'])
        if post:
            view_data = {
                'view_id': str(view['_id']),
                'post_id': str(view['post_id']),
                'post_title': post.get('title', ''),
                'post_description': post.get('description', ''),
                'media_type': post.get('media_type'),
                'view_duration': view.get('view_duration', 0),
                'created_at': view.get('created_at')
            }
            result.append(view_data)

    return jsonify({
        'success': True,
        'data': {
            'view_history': result,
            'total': total,
            'limit': limit,
            'skip': skip
        }
    })


@bp.route('/api/posts/trending-views', methods=['GET'])
@jwt_optional
def get_trending_posts():
    """
    获取浏览次数最多的热门帖子。

    Query parameters:
        - time_range: 时间范围(1h, 6h, 24h, 7d,默认 24h)
        - limit: 返回数量(默认 10)

    Returns:
        JSON with trending posts
    """
    # Get time range parameter
    time_range = request.args.get('time_range', '24h')

    # Parse time range
    time_mapping = {
        '1h': 1,
        '6h': 6,
        '24h': 24,
        '7d': 168  # 7 * 24
    }

    if time_range not in time_mapping:
        return jsonify({'error': 'Invalid time_range. Use: 1h, 6h, 24h, or 7d'}), 400

    hours = time_mapping[time_range]

    # Get limit parameter
    try:
        limit = int(request.args.get('limit', 10))
        limit = min(limit, 50)
    except ValueError:
        limit = 10

    # Get current user ID for visibility filtering
    current_user_id = getattr(request, 'user_id', None)

    # Calculate cutoff time
    from utils import is_following_user

    cutoff_time = datetime.utcnow() - timedelta(hours=hours)

    # Get trending posts by view count
    trending = view_history_store.get_trending_posts(
        hours=hours,
        limit=limit
    )

    # Expand post information and filter by visibility
    result = []
    for item in trending:
        post = post_store.get_post_by_id(item['_id'])
        if post and post.get('visibility') == 'public':
            post_data = {
                '_id': str(post['_id']),
                'user_id': str(post['user_id']),
                'title': post.get('title', ''),
                'description': post.get('description', ''),
                'media_type': post.get('media_type'),
                'media_files': [str(fid) for fid in post.get('media_files', [])],
                'view_count': item['view_count'],
                'total_duration': item.get('total_duration', 0),
                'created_at': post.get('created_at'),
                'stats': post.get('stats', {})
            }

            # Get creator username
            creator = user_store.get_user_by_id(post['user_id'])
            if creator:
                post_data['username'] = creator.get('username', '')

            result.append(post_data)

    return jsonify({
        'success': True,
        'data': {
            'posts': result,
            'time_range': time_range,
            'total': len(result)
        }
    })


@bp.route('/api/posts/<post_id>/view-stats', methods=['GET'])
@jwt_optional
def get_post_view_stats(post_id):
    """
    获取帖子的浏览统计信息。

    Args:
        post_id: 帖子 ID

    Returns:
        JSON with view statistics
    """
    try:
        post_obj = ObjectId(post_id)
    except Exception:
        return jsonify({'error': 'Invalid post ID'}), 400

    # Check if post exists
    post = post_store.get_post_by_id(post_obj)
    if not post:
        return jsonify({'error': 'Post not found'}), 404

    # Get view statistics
    total_views = view_history_store.get_view_count_by_post(post_obj)
    views = view_history_store.get_views_by_post(post_obj, limit=1000)

    # Calculate total duration
    total_duration = sum(v.get('view_duration', 0) for v in views)

    # Calculate average duration
    avg_duration = total_duration / total_views if total_views > 0 else 0

    return jsonify({
        'success': True,
        'data': {
            'post_id': post_id,
            'total_views': total_views,
            'total_duration_ms': total_duration,
            'average_duration_ms': round(avg_duration, 2)
        }
    })