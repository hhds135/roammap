"""Authentication endpoints: register and login."""
from flask import Blueprint, request, jsonify
from datetime import datetime
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

from storage.user_store import UserStore
from storage.connection import MongoDBConnection, get_db
from utils import generate_token

bp = Blueprint('auth', __name__)

# Initialize MongoDB connection
try:
    if get_db() is None:
        conn = MongoDBConnection()
        conn.connect()
except Exception:
    pass

user_store = UserStore()


@bp.route('/api/auth/register', methods=['POST'])
def register():
    """User registration endpoint."""
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400

    username = data['username'].strip()
    password = data['password']

    if len(username) < 3:
        return jsonify({'error': 'Username must be at least 3 characters'}), 400

    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400

    # Check if username already exists
    existing_user = user_store.get_user_by_username(username)
    if existing_user:
        return jsonify({'error': 'Username already exists'}), 409

    # Create new user in MongoDB
    try:
        password_hash = generate_password_hash(password)
        user_id = user_store.create_user(
            username=username,
            password_hash=password_hash,
            interest_tags=data.get('interest_tags', [])
        )
    except Exception as e:
        return jsonify({'error': f'Failed to create user: {str(e)}'}), 500

    # Return user info (convert ObjectId to string)
    user_info = {
        'id': str(user_id),
        'username': username,
        'interest_tags': data.get('interest_tags', [])
    }
    
    return jsonify({'message': 'Registration successful', 'user': user_info}), 201


@bp.route('/api/auth/login', methods=['POST'])
def login():
    """User login endpoint."""
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400

    username = data['username'].strip()
    password = data['password']

    user = user_store.get_user_by_username(username)
    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'Invalid username or password'}), 401

    # Generate JWT token with ObjectId as string
    token = generate_token(str(user['_id']), user['username'])

    user_info = {
        'id': str(user['_id']),
        'username': user['username'],
        'interest_tags': user.get('interest_tags', [])
    }
    
    return jsonify({
        'message': 'Login successful',
        'user': user_info,
        'token': token
    })
