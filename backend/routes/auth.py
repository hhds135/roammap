"""Authentication endpoints: register and login."""
from flask import Blueprint, request, jsonify
from datetime import datetime
import uuid
from werkzeug.security import generate_password_hash, check_password_hash

from models import find_user_by_username, load_users, save_users
from utils import generate_token, jwt_required

bp = Blueprint('auth', __name__)


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
    if find_user_by_username(username):
        return jsonify({'error': 'Username already exists'}), 409

    # Create new user
    users = load_users()
    new_user = {
        'id': str(uuid.uuid4()),
        'username': username,
        'password_hash': generate_password_hash(password),
        'created_at': datetime.now().isoformat()
    }

    users.append(new_user)
    save_users(users)

    user_info = {k: v for k, v in new_user.items() if k != 'password_hash'}
    return jsonify({'message': 'Registration successful', 'user': user_info}), 201


@bp.route('/api/auth/login', methods=['POST'])
def login():
    """User login endpoint."""
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400

    username = data['username'].strip()
    password = data['password']

    user = find_user_by_username(username)
    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'Invalid username or password'}), 401

    token = generate_token(user['id'], user['username'])

    user_info = {k: v for k, v in user.items() if k != 'password_hash'}
    return jsonify({
        'message': 'Login successful',
        'user': user_info,
        'token': token
    })
