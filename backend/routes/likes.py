"""Like endpoints for posts."""
from flask import Blueprint, request, jsonify
from bson import ObjectId

from storage.like_store import LikeStore
from storage.post_store import PostStore
from utils import jwt_required, check_post_visibility, is_following_user

bp = Blueprint('likes', __name__)

like_store = LikeStore()
post_store = PostStore()


@bp.route('/api/posts/<post_id>/like', methods=['POST'])
@jwt_required
def toggle_like_post(post_id):
    """Like or unlike a post."""
    user_id = request.user_id

    try:
        post_id_obj = ObjectId(post_id)
    except Exception:
        return jsonify({'error': 'Invalid post ID'}), 400

    # Get post
    post = post_store.get_post_by_id(post_id_obj)
    if not post:
        return jsonify({'error': 'Post not found'}), 404

    # Check visibility
    if not check_post_visibility(user_id, post, is_following_user):
        return jsonify({'error': 'Access denied'}), 403

    # Toggle like
    is_liked = like_store.toggle_like(ObjectId(user_id), post_id_obj)

    # Update post stats
    if is_liked:
        post_store.increment_stat(post_id_obj, 'likes_count')
    else:
        post_store.decrement_stat(post_id_obj, 'likes_count')

    # Get like count
    likes_count = like_store.count_likes_by_post(post_id_obj)

    return jsonify({
        'success': True,
        'data': {
            'is_liked': is_liked,
            'likes_count': likes_count
        }
    })


@bp.route('/api/posts/<post_id>/likes', methods=['GET'])
def get_post_likes(post_id):
    """Get likes for a post."""
    try:
        post_id_obj = ObjectId(post_id)
    except Exception:
        return jsonify({'error': 'Invalid post ID'}), 400

    # Get post
    post = post_store.get_post_by_id(post_id_obj)
    if not post:
        return jsonify({'error': 'Post not found'}), 404

    # Get pagination params
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

    # Get likes
    likes = like_store.get_likes_by_post(post_id_obj, limit=limit)

    # Convert ObjectIds to strings
    for like in likes:
        like['_id'] = str(like['_id'])
        like['user_id'] = str(like['user_id'])
        like['post_id'] = str(like['post_id'])

    # Get total count
    total = like_store.count_likes_by_post(post_id_obj)

    return jsonify({
        'success': True,
        'data': {
            'likes': likes,
            'total': total,
            'limit': limit,
            'skip': skip
        }
    })


@bp.route('/api/users/<user_id>/likes', methods=['GET'])
def get_user_likes(user_id):
    """Get posts liked by a user."""
    try:
        user_id_obj = ObjectId(user_id)
    except Exception:
        return jsonify({'error': 'Invalid user ID'}), 400

    # Get pagination params
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

    # Get likes
    likes = like_store.get_likes_by_user(user_id_obj, limit=limit)

    # Convert ObjectIds to strings
    for like in likes:
        like['_id'] = str(like['_id'])
        like['user_id'] = str(like['user_id'])
        like['post_id'] = str(like['post_id'])

    # Get total count
    total = like_store.count_likes_by_user(user_id_obj)

    return jsonify({
        'success': True,
        'data': {
            'likes': likes,
            'total': total,
            'limit': limit,
            'skip': skip
        }
    })