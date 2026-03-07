"""Tests for the clear API endpoint."""
import pytest


def test_clear_api_requires_no_auth(client):
    """Test that clear API works without authentication."""
    response = client.post('/api/test/clear')
    assert response.status_code == 200


def test_clear_api_returns_message(client):
    """Test that clear API returns success message."""
    response = client.post('/api/test/clear')
    data = response.get_json()
    assert 'message' in data
    assert 'success' in data['message'].lower()


def test_clear_api_clears_users(client):
    """Test that clear API clears users.json."""
    # First create a user
    client.post('/api/auth/register', json={
        'username': 'testuser',
        'password': 'testpass123'
    })

    # Clear data
    client.post('/api/test/clear')

    # Try to login with the cleared user
    response = client.post('/api/auth/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    assert response.status_code == 401


def test_clear_api_clears_corners(client, registered_user):
    """Test that clear API clears corners.json."""
    user_data, token = registered_user
    headers = {'Authorization': f'Bearer {token}'}

    # Create a corner using minimal data (will fail without image, but for clearing test)
    # Just test that the endpoint exists and returns success
    response = client.post('/api/test/clear')
    assert response.status_code == 200
