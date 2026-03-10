"""Favorite endpoints for posts."""
from flask import Blueprint, request, jsonify
from bson import ObjectId

from storage.favorite_store import FavoriteStore
from storage.post_store import PostStore
from utils import jwt_required, check_post_visibility, is_following_user

bp = Blueprint('favorites', __name__)

favorite_store = FavoriteStore()
post_store = PostStore()


@bp.route('/api/posts/<post_id>/favorite', methods=['POST'])
@jwt_required
def toggle_favorite_post(post_id):
    """Favorite or unfavorite a post."""
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

    # Toggle favorite
    is_favorited = favorite_store.toggle_favorite(ObjectId(user_id), post_id_obj)

    # Update post stats
    if is_favorited:
        post_store.increment_stat(post_id_obj, 'favorites_count')
    else:
        post_store.decrement_stat(post_id_obj, 'favorites_count')

    # Get favorite count
    favorites_count = favorite_store.count_favorites_by_post(post_id_obj)

    return jsonify({
        'success': True,
        'data': {
            'is_favorited': is_favorited,
            'favorites_count': favorites_count
        }
    })


@bp.route('/api/posts/<post_id>/favorites', methods=['GET'])
def get_post_favorites(post_id):
    """Get favorites for a post."""
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

    # Get favorites
    favorites = favorite_store.get_favorites_by_post(post_id_obj, limit=limit)

    # Convert ObjectIds to strings
    for favorite in favorites:
        favorite['_id'] = str(favorite['_id'])
        favorite['user_id'] = str(favorite['user_id'])
        favorite['post_id'] = str(favorite['post_id'])

    # Get total count
    total = favorite_store.count_favorites_by_post(post_id_obj)

    return jsonify({
        'success': True,
        'data': {
            'favorites': favorites,
            'total': total,
            'limit': limit,
            'skip': skip
        }
    })


@bp.route('/api/users/<user_id>/favorites', methods=['GET'])
def get_user_favorites(user_id):
    """Get posts favorited by a user."""
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

    # Get favorites
    favorites = favorite_store.get_favorites_by_user(user_id_obj, limit=limit)

    # Convert ObjectIds to strings
    for favorite in favorites:
        favorite['_id'] = str(favorite['_id'])
        favorite['user_id'] = str(favorite['user_id'])
        favorite['post_id'] = str(favorite['post_id'])

    # Get total count
    total = favorite_store.count_favorites_by_user(user_id_obj)

    return jsonify({
        'success': True,
        'data': {
            'favorites': favorites,
            'total': total,
            'limit': limit,
            'skip': skip
        }
    })