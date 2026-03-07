"""Tests for authentication endpoints."""


def test_register_with_valid_data(client):
    """Test user registration with valid data."""
    response = client.post('/api/auth/register', json={
        'username': 'newuser',
        'password': 'password123'
    })
    assert response.status_code == 201


def test_register_returns_user_data(client):
    """Test that registration returns user data without password."""
    response = client.post('/api/auth/register', json={
        'username': 'newuser2',
        'password': 'password123'
    })
    data = response.get_json()
    assert 'user' in data
    assert 'id' in data['user']
    assert 'username' in data['user']
    assert 'password_hash' not in data['user']


def test_register_short_username_fails(client):
    """Test that registration with short username fails."""
    response = client.post('/api/auth/register', json={
        'username': 'ab',
        'password': 'password123'
    })
    assert response.status_code == 400
    assert 'error' in response.get_json()


def test_register_short_password_fails(client):
    """Test that registration with short password fails."""
    response = client.post('/api/auth/register', json={
        'username': 'testuser3',
        'password': '12345'
    })
    assert response.status_code == 400
    assert 'error' in response.get_json()


def test_register_missing_fields_fails(client):
    """Test that registration with missing fields fails."""
    response = client.post('/api/auth/register', json={
        'username': 'testuser4'
    })
    assert response.status_code == 400
    assert 'error' in response.get_json()


def test_register_duplicate_username_fails(client):
    """Test that duplicate username registration fails."""
    # First registration
    client.post('/api/auth/register', json={
        'username': 'duplicate',
        'password': 'password123'
    })

    # Second registration with same username
    response = client.post('/api/auth/register', json={
        'username': 'duplicate',
        'password': 'differentpass'
    })
    assert response.status_code == 409
    assert 'error' in response.get_json()


def test_login_with_valid_credentials(client):
    """Test login with valid credentials."""
    # Register first
    client.post('/api/auth/register', json={
        'username': 'loginuser',
        'password': 'password123'
    })

    # Login
    response = client.post('/api/auth/login', json={
        'username': 'loginuser',
        'password': 'password123'
    })
    assert response.status_code == 200


def test_login_returns_token(client):
    """Test that login returns JWT token."""
    # Register first
    client.post('/api/auth/register', json={
        'username': 'tokenuser',
        'password': 'password123'
    })

    # Login
    response = client.post('/api/auth/login', json={
        'username': 'tokenuser',
        'password': 'password123'
    })
    data = response.get_json()
    assert 'token' in data
    assert 'user' in data


def test_login_invalid_credentials_fails(client):
    """Test login with invalid credentials fails."""
    response = client.post('/api/auth/login', json={
        'username': 'nonexistent',
        'password': 'wrongpassword'
    })
    assert response.status_code == 401
    assert 'error' in response.get_json()


def test_login_missing_fields_fails(client):
    """Test login with missing fields fails."""
    response = client.post('/api/auth/login', json={
        'username': 'testuser5'
    })
    assert response.status_code == 400
    assert 'error' in response.get_json()


def test_jwt_token_works_for_protected_route(client):
    """Test that JWT token provides access to protected routes."""
    # Register and login
    client.post('/api/auth/register', json={
        'username': 'jwtuser',
        'password': 'password123'
    })
    login_response = client.post('/api/auth/login', json={
        'username': 'jwtuser',
        'password': 'password123'
    })

    token = login_response.get_json()['token']

    # Try to access protected route with token
    response = client.get('/api/friends', headers={
        'Authorization': f'Bearer {token}'
    })
    # Should not return 401 for unauthorized access
    # The endpoint should return 200 with empty friends list
    assert response.status_code == 200


def test_protected_route_without_token_fails(client):
    """Test that protected route fails without token."""
    response = client.get('/api/friends')
    assert response.status_code == 401
    assert 'error' in response.get_json()
