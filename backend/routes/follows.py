"""Follow system endpoints."""
from flask import Blueprint, request, jsonify
from bson import ObjectId

from storage.user_store import UserStore
from utils import jwt_required, jwt_optional

bp = Blueprint('follows', __name__)
user_store = UserStore()

# Maximum number of users a user can follow
MAX_FOLLOWING = 1000


@bp.route('/api/follows/<user_id>', methods=['POST'])
@jwt_required
def follow_user(user_id):
    """
    Follow a specific user.

    Args:
        user_id: ID of the user to follow (URL path parameter)

    Returns:
        JSON with follow status
    """
    current_user_id = request.user_id

    try:
        target_user_obj = ObjectId(user_id)
        current_user_obj = ObjectId(current_user_id)
    except Exception:
        return jsonify({'error': 'Invalid user ID'}), 400

    # Cannot follow yourself
    if current_user_id == user_id:
        return jsonify({'error': 'Cannot follow yourself'}), 400

    # Check if target user exists
    target_user = user_store.get_user_by_id(target_user_obj)
    if not target_user:
        return jsonify({'error': 'User not found'}), 404

    # Check if already following
    if user_store.is_following(current_user_obj, target_user_obj):
        return jsonify({
            'success': True,
            'message': 'Already following user',
            'data': {
                'follower_id': current_user_id,
                'following_id': user_id,
                'is_following': True
            }
        })

    # Check max following limit
    current_user = user_store.get_user_by_id(current_user_obj)
    following_count = len(current_user.get('following', []))
    if following_count >= MAX_FOLLOWING:
        return jsonify({'error': f'Maximum following limit reached ({MAX_FOLLOWING})'}), 400

    # Follow user
    success = user_store.follow(current_user_obj, target_user_obj)
    if not success:
        return jsonify({'error': 'Failed to follow user'}), 500

    return jsonify({
        'success': True,
        'message': 'Successfully followed user',
        'data': {
            'follower_id': current_user_id,
            'following_id': user_id,
            'is_following': True
        }
    })


@bp.route('/api/follows/<user_id>', methods=['DELETE'])
@jwt_required
def unfollow_user(user_id):
    """
    Unfollow a specific user.

    Args:
        user_id: ID of the user to unfollow (URL path parameter)

    Returns:
        JSON with follow status
    """
    current_user_id = request.user_id

    try:
        target_user_obj = ObjectId(user_id)
        current_user_obj = ObjectId(current_user_id)
    except Exception:
        return jsonify({'error': 'Invalid user ID'}), 400

    # Check if target user exists
    target_user = user_store.get_user_by_id(target_user_obj)
    if not target_user:
        return jsonify({'error': 'User not found'}), 404

    # Unfollow user
    success = user_store.unfollow(current_user_obj, target_user_obj)
    if not success:
        return jsonify({
            'success': True,
            'message': 'Already not following user',
            'data': {
                'follower_id': current_user_id,
                'following_id': user_id,
                'is_following': False
            }
        })

    return jsonify({
        'success': True,
        'message': 'Successfully unfollowed user',
        'data': {
            'follower_id': current_user_id,
            'following_id': user_id,
            'is_following': False
        }
    })


@bp.route('/api/users/<user_id>/following', methods=['GET'])
@jwt_optional
def get_following(user_id):
    """
    Get list of all users followed by a specific user.

    Args:
        user_id: User ID (URL path parameter)

    Query parameters:
        - limit: Number of users per page (default 20)
        - skip: Number of users to skip (for pagination)

    Returns:
        JSON with following list
    """
    try:
        user_obj = ObjectId(user_id)
    except Exception:
        return jsonify({'error': 'Invalid user ID'}), 400

    # Check if user exists
    user = user_store.get_user_by_id(user_obj)
    if not user:
        return jsonify({'error': 'User not found'}), 404

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

    # Get following list
    following = user_store.get_following(user_obj)

    # Apply pagination
    total = len(following)
    paginated_following = following[skip:skip + limit]

    # Format response
    following_list = []
    for f_user in paginated_following:
        following_list.append({
            'user_id': str(f_user['_id']),
            'username': f_user.get('username', ''),
            'interest_tags': f_user.get('interest_tags', [])
        })

    return jsonify({
        'success': True,
        'data': {
            'following': following_list,
            'total': total,
            'limit': limit,
            'skip': skip
        }
    })


@bp.route('/api/users/<user_id>/followers', methods=['GET'])
@jwt_optional
def get_followers(user_id):
    """
    Get list of all users following a specific user (followers).

    Args:
        user_id: User ID (URL path parameter)

    Query parameters:
        - limit: Number of users per page (default 20)
        - skip: Number of users to skip (for pagination)

    Returns:
        JSON with followers list
    """
    try:
        user_obj = ObjectId(user_id)
    except Exception:
        return jsonify({'error': 'Invalid user ID'}), 400

    # Check if user exists
    user = user_store.get_user_by_id(user_obj)
    if not user:
        return jsonify({'error': 'User not found'}), 404

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

    # Get followers list
    followers = user_store.get_followers(user_obj)

    # Apply pagination
    total = len(followers)
    paginated_followers = followers[skip:skip + limit]

    # Format response
    followers_list = []
    for f_user in paginated_followers:
        followers_list.append({
            'user_id': str(f_user['_id']),
            'username': f_user.get('username', ''),
            'interest_tags': f_user.get('interest_tags', [])
        })

    return jsonify({
        'success': True,
        'data': {
            'followers': followers_list,
            'total': total,
            'limit': limit,
            'skip': skip
        }
    })


@bp.route('/api/follows/<user_id>/status', methods=['GET'])
@jwt_optional
def get_follow_status(user_id):
    """
    Check if current user is following a specific user.

    Args:
        user_id: ID of the user to check (URL path parameter)

    Returns:
        JSON with follow status
    """
    try:
        target_user_obj = ObjectId(user_id)
    except Exception:
        return jsonify({'error': 'Invalid user ID'}), 400

    # Check if target user exists
    target_user = user_store.get_user_by_id(target_user_obj)
    if not target_user:
        return jsonify({'error': 'User not found'}), 404

    # Get current user ID
    current_user_id = getattr(request, 'user_id', None)

    if not current_user_id:
        # Not logged in
        return jsonify({
            'success': True,
            'data': {
                'is_following': False,
                'is_followed_by': False
            }
        })

    try:
        current_user_obj = ObjectId(current_user_id)
    except Exception:
        return jsonify({'error': 'Invalid current user ID'}), 400

    # Check follow status
    is_following = user_store.is_following(current_user_obj, target_user_obj)
    is_followed_by = user_store.is_following(target_user_obj, current_user_obj)

    return jsonify({
        'success': True,
        'data': {
            'is_following': is_following,
            'is_followed_by': is_followed_by
        }
    })