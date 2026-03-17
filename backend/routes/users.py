"""User management endpoints."""
from flask import Blueprint, request, jsonify
from bson import ObjectId

from storage.user_store import UserStore
from utils import jwt_required

bp = Blueprint('users', __name__)
user_store = UserStore()

# Interest tags limits
MAX_INTEREST_TAGS = 10
MAX_TAG_LENGTH = 20

# Profile limits
MAX_NICKNAME_LENGTH = 30
MIN_NICKNAME_LENGTH = 1


def validate_interest_tags(tags):
    """
    Validate interest tags.
    
    Args:
        tags: List of tags to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not isinstance(tags, list):
        return False, 'interest_tags must be an array'
    
    if len(tags) > MAX_INTEREST_TAGS:
        return False, f'Maximum {MAX_INTEREST_TAGS} interest tags allowed'
    
    for tag in tags:
        if not isinstance(tag, str):
            return False, 'Each tag must be a string'
        if len(tag) > MAX_TAG_LENGTH:
            return False, f'Tag "{tag}" exceeds maximum length of {MAX_TAG_LENGTH} characters'
        if not tag.strip():
            return False, 'Tags cannot be empty or whitespace only'
    
    return True, None


@bp.route('/api/users/<user_id>/interests', methods=['GET'])
def get_user_interests(user_id):
    """
    Get a user's interest tags.
    
    Args:
        user_id: User ObjectId
        
    Returns:
        JSON with interest tags list
    """
    try:
        user_id_obj = ObjectId(user_id)
    except Exception:
        return jsonify({'error': 'Invalid user ID'}), 400
    
    # Get user
    user = user_store.get_user_by_id(user_id_obj)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Get interest tags
    interest_tags = user.get('interest_tags', [])
    
    return jsonify({
        'success': True,
        'data': {
            'user_id': user_id,
            'username': user.get('username', ''),
            'nickname': user.get('nickname', ''),
            'avatar_id': user.get('avatar_id', ''),
            'interest_tags': interest_tags
        }
    })


@bp.route('/api/users/<user_id>/interests', methods=['PUT'])
@jwt_required
def update_user_interests(user_id):
    """
    Update a user's interest tags.
    
    Only the user themselves can update their interest tags.
    
    Args:
        user_id: User ObjectId
        
    Request body:
        - interest_tags: List of interest tag strings
        
    Returns:
        JSON with updated interest tags
    """
    current_user_id = request.user_id
    
    # Check if user is updating their own tags
    if current_user_id != user_id:
        return jsonify({'error': 'Access denied. You can only update your own interest tags'}), 403
    
    data = request.get_json()
    if not data or 'interest_tags' not in data:
        return jsonify({'error': 'interest_tags field is required'}), 400
    
    # Validate tags
    tags = data['interest_tags']
    is_valid, error = validate_interest_tags(tags)
    if not is_valid:
        return jsonify({'error': error}), 400
    
    try:
        user_id_obj = ObjectId(user_id)
    except Exception:
        return jsonify({'error': 'Invalid user ID'}), 400
    
    # Get user to verify exists
    user = user_store.get_user_by_id(user_id_obj)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Update interest tags
    try:
        if not user_store.update_user(user_id_obj, {'interest_tags': tags}):
            return jsonify({'error': 'Failed to update interest tags'}), 500
    except Exception as e:
        return jsonify({'error': f'Failed to update interest tags: {str(e)}'}), 500
    
    # Get updated user
    updated_user = user_store.get_user_by_id(user_id_obj)
    
    return jsonify({
        'success': True,
        'data': {
            'user_id': user_id,
            'username': updated_user.get('username', ''),
            'nickname': updated_user.get('nickname', ''),
            'avatar_id': updated_user.get('avatar_id', ''),
            'interest_tags': updated_user.get('interest_tags', [])
        }
    })


def validate_nickname(nickname):
    """
    Validate nickname.
    
    Args:
        nickname: Nickname to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not isinstance(nickname, str):
        return False, 'Nickname must be a string'
    
    nickname = nickname.strip()
    
    if len(nickname) < MIN_NICKNAME_LENGTH:
        return False, 'Nickname cannot be empty'
    
    if len(nickname) > MAX_NICKNAME_LENGTH:
        return False, f'Nickname cannot exceed {MAX_NICKNAME_LENGTH} characters'
    
    return True, None


@bp.route('/api/users/<user_id>/profile', methods=['PUT'])
@jwt_required
def update_user_profile(user_id):
    """
    Update a user's profile (nickname and avatar).
    
    Only the user themselves can update their profile.
    
    Args:
        user_id: User ObjectId
        
    Request body:
        - nickname: Display name (optional)
        - avatar_id: GridFS file ID for avatar image (optional)
        
    Returns:
        JSON with updated profile
    """
    current_user_id = request.user_id
    
    # Check if user is updating their own profile
    if current_user_id != user_id:
        return jsonify({'error': 'Access denied. You can only update your own profile'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400
    
    # Validate and prepare updates
    updates = {}
    
    if 'nickname' in data:
        nickname = data['nickname']
        is_valid, error = validate_nickname(nickname)
        if not is_valid:
            return jsonify({'error': error}), 400
        updates['nickname'] = nickname.strip()
    
    if 'avatar_id' in data:
        avatar_id = data['avatar_id']
        if avatar_id is not None and avatar_id != '':
            if not isinstance(avatar_id, str):
                return jsonify({'error': 'avatar_id must be a string'}), 400
            # Validate that it's a valid ObjectId
            try:
                ObjectId(avatar_id)
            except Exception:
                return jsonify({'error': 'avatar_id must be a valid file ID'}), 400
        updates['avatar_id'] = avatar_id or ''
    
    if not updates:
        return jsonify({'error': 'No valid fields to update'}), 400
    
    try:
        user_id_obj = ObjectId(user_id)
    except Exception:
        return jsonify({'error': 'Invalid user ID'}), 400
    
    # Get user to verify exists
    user = user_store.get_user_by_id(user_id_obj)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Update profile
    try:
        if not user_store.update_user(user_id_obj, updates):
            return jsonify({'error': 'Failed to update profile'}), 500
    except Exception as e:
        return jsonify({'error': f'Failed to update profile: {str(e)}'}), 500
    
    # Get updated user
    updated_user = user_store.get_user_by_id(user_id_obj)
    
    return jsonify({
        'success': True,
        'data': {
            'user_id': user_id,
            'username': updated_user.get('username', ''),
            'nickname': updated_user.get('nickname', ''),
            'avatar_id': updated_user.get('avatar_id', ''),
            'interest_tags': updated_user.get('interest_tags', [])
        }
    })


@bp.route('/api/users/search', methods=['GET'])
@jwt_required
def search_users():
    """
    Search users by username.
    
    Query parameters:
        - q: Search query string (required)
        - limit: Maximum number of results (default: 20)
    
    Returns:
        JSON with matching users
    """
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'error': 'Missing search query'}), 400
    
    try:
        limit = int(request.args.get('limit', 20))
        limit = min(limit, 100)
    except ValueError:
        limit = 20
    
    # Use regex for fuzzy search on username
    import re
    regex = re.compile(query, re.IGNORECASE)
    
    try:
        users = list(user_store.collection.find({
            'username': regex
        }).limit(limit))
    except Exception as e:
        return jsonify({'error': f'Failed to search users: {str(e)}'}), 500
    
    # Convert to response format
    result = []
    for user in users:
        user_data = {
            '_id': str(user['_id']),
            'username': user.get('username', ''),
            'interest_tags': user.get('interest_tags', []),
            'followers_count': len(user.get('followers', [])),
            'following_count': len(user.get('following', []))
        }
        result.append(user_data)
    
    return jsonify({
        'success': True,
        'data': {
            'users': result,
            'total': len(result)
        }
    })
