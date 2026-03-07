"""Utility functions for JWT, authentication, and file handling."""
import jwt
from datetime import datetime
from functools import wraps
from flask import request, jsonify
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
