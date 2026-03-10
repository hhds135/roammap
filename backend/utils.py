"""Utility functions for JWT, authentication, and file handling."""
import jwt
from datetime import datetime
from functools import wraps
from flask import request, jsonify
from bson import ObjectId
from config import Config


def generate_token(user_id, username):
    """
    Generate JWT token.

    Args:
        user_id: User ID to encode in token
        username: Username to encode in token

    Returns:
        str: Encoded JWT token
    """
    payload = {
        'exp': datetime.utcnow() + Config.JWT_EXPIRATION_DELTA,
        'iat': datetime.utcnow(),
        'user_id': user_id,
        'username': username
    }
    return jwt.encode(payload, Config.SECRET_KEY, algorithm=Config.JWT_ALGORITHM)


def decode_token(token):
    """
    Decode JWT token.

    Args:
        token: JWT token string to decode

    Returns:
        dict: Decoded payload or error dict
    """
    try:
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=[Config.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return {'error': 'Token expired'}
    except jwt.InvalidTokenError:
        return {'error': 'Invalid token'}


def jwt_required(f):
    """
    Decorator that requires valid JWT authentication.

    Routes decorated with this function will require a valid JWT token
    in the Authorization header (Bearer scheme).
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Get token from Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]

        if not token:
            return jsonify({'error': 'Missing authentication token'}), 401

        # Verify token
        payload = decode_token(token)
        if 'error' in payload:
            return jsonify({'error': payload['error']}), 401

        # Add user info to request context
        request.user_id = payload['user_id']
        request.username = payload['username']

        return f(*args, **kwargs)
    return decorated


def jwt_optional(f):
    """
    Decorator that optionally accepts JWT authentication.

    Routes decorated with this function will work without authentication,
    but if a token is provided, it must be valid.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Get token from Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]

        # If token provided, verify it
        if token:
            payload = decode_token(token)
            if payload and 'error' in payload:
                # Invalid token provided
                return jsonify({'error': payload['error']}), 401
            elif payload and 'error' not in payload:
                # Valid token, extract user info
                request.user_id = payload['user_id']
                request.username = payload['username']
        # If no token provided, continue without setting user_id/username

        return f(*args, **kwargs)
    return decorated


def allowed_file(filename):
    """
    Check if file extension is allowed.

    Args:
        filename: Name of the file to check

    Returns:
        bool: True if file extension is allowed, False otherwise
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


# Import here to avoid circular imports
def _get_user_store():
    """Lazy import of UserStore to avoid circular imports."""
    from storage.user_store import UserStore
    return UserStore()


def is_following_user(follower_id: str, following_id: str) -> bool:
    """
    Check if a user is following another user.

    Args:
        follower_id: User who might be following (string ID)
        following_id: User who might be followed (string ID)

    Returns:
        bool: True if following
    """
    try:
        follower_obj = ObjectId(follower_id)
        following_obj = ObjectId(following_id)
        user_store = _get_user_store()
        result = user_store.is_following(follower_obj, following_obj)
        return result
    except Exception as e:
        # Log the exception for debugging
        import logging
        logging.error(f"is_following_user error: {e}", exc_info=True)
        return False


def check_post_visibility(user_id: str, post: dict, is_following_func) -> bool:
    """
    Validate user can view a post based on visibility settings.

    Args:
        user_id: Current user ID (None if not logged in)
        post: Post document
        is_following_func: Function to check follow relationship

    Returns:
        bool: True if user can view the post
    """
    visibility = post.get('visibility', 'public')
    post_user_id = str(post.get('user_id'))

    # Public posts are visible to everyone
    if visibility == 'public':
        return True

    # Non-public posts require authentication
    if user_id is None:
        return False

    # Private posts are only visible to creator
    if visibility == 'private':
        return user_id == post_user_id

    # Followers-only posts visible to creator and followers
    if visibility == 'followers':
        # Creator can always view
        if user_id == post_user_id:
            return True
        # Check if user follows the post creator
        return is_following_func(user_id, post_user_id)

    # Default to not visible for unknown visibility values
    return False


def post_visibility_required(f):
    """
    Decorator to check post visibility before accessing a post.

    Usage:
        @bp.route('/api/posts/<post_id>', methods=['GET'])
        @post_visibility_required
        def get_post(post):
            return jsonify({'success': True, 'data': post})

    The decorated function receives the post dict as first argument.
    """
    from functools import wraps
    from storage.post_store import PostStore

    @wraps(f)
    def decorated_function(post_id, *args, **kwargs):
        # Get current user ID (from JWT)
        user_id = getattr(request, 'user_id', None)

        # Get post
        try:
            post_obj = ObjectId(post_id)
        except Exception:
            return jsonify({'error': 'Invalid post ID'}), 400

        post_store = PostStore()
        post = post_store.get_post_by_id(post_obj)
        if not post:
            return jsonify({'error': 'Post not found'}), 404

        # Check visibility
        if not check_post_visibility(user_id, post, is_following_user):
            return jsonify({'error': 'Access denied'}), 403

        # Pass post to the decorated function
        return f(post, *args, **kwargs)

    return decorated_function
