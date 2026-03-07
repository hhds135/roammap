"""Authentication fixtures for JWT token generation and user registration."""
import pytest
import sys
import os
import jwt
from datetime import datetime, timedelta

# Add parent directory to path to import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app import app, generate_token


@pytest.fixture
def sample_token():
    """
    Sample JWT token for testing.

    Returns:
        str: A valid JWT token with test user data
    """
    payload = {
        'exp': datetime.utcnow() + timedelta(days=1),
        'iat': datetime.utcnow(),
        'user_id': 'test-user-123',
        'username': 'testuser'
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')


@pytest.fixture
def auth_headers(sample_token):
    """
    Authorization headers with Bearer token.

    Args:
        sample_token: JWT token fixture

    Returns:
        dict: Authorization headers dictionary
    """
    return {'Authorization': f'Bearer {sample_token}'}


@pytest.fixture
def registered_user(client):
    """
    Creates a registered user and returns user data and token.

    Args:
        client: Flask test client fixture

    Returns:
        tuple: (user_dict, token) where user_dict contains id, username, etc.
    """
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    user_input = {
        'username': f'testuser_{unique_id}',
        'password': 'password123',
        'email': f'testuser_{unique_id}@example.com'
    }

    # Register the user
    response = client.post('/api/auth/register', json=user_input)
    response_data = response.get_json()
    
    # Get the user data from server response (includes id)
    user_dict = response_data.get('user', {})

    # Login to get token
    login_response = client.post('/api/auth/login', json={
        'username': user_input['username'],
        'password': user_input['password']
    })
    login_data = login_response.get_json()
    token = login_data.get('token')

    return user_dict, token


@pytest.fixture
def multiple_registered_users(client):
    """
    Creates multiple test users and returns their data.

    Args:
        client: Flask test client fixture

    Returns:
        list: List of tuples (user_dict, token) for each user
    """
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    users_info = []

    for i in range(3):
        user_input = {
            'username': f'user{i+1}_{unique_id}',
            'password': 'password123',
            'email': f'user{i+1}_{unique_id}@example.com'
        }

        # Register the user
        response = client.post('/api/auth/register', json=user_input)
        response_data = response.get_json()
        
        # Get the user data from server response (includes id)
        user_dict = response_data.get('user', {})

        # Login to get token
        login_response = client.post('/api/auth/login', json={
            'username': user_input['username'],
            'password': user_input['password']
        })
        login_data = login_response.get_json()
        token = login_data.get('token')

        users_info.append((user_dict, token))

    return users_info
