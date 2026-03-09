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
            'interest_tags': updated_user.get('interest_tags', [])
        }
    })
