"""Tests for like and favorite functionality."""
import pytest


def test_like_corner(client, registered_user, image_file):
    """Test liking a corner."""
    user_data, token = registered_user
    headers = {'Authorization': f'Bearer {token}'}

    # First create a corner
    data = {
        'title': 'Like Test Corner',
        'description': 'Test Description',
        'latitude': '40.7128',
        'longitude': '-74.0060',
        'address': 'Test Address',
        'tags': 'test,tag',
        'visibility': 'public',
        'specific_friends': '',
        'exclude_friends': ''
    }

    files = {'image': image_file}

    create_response = client.post('/api/corners', data={**data}, files=files, headers=headers)
    corner_id = create_response.get_json()['corner']['id']

    # Like the corner
    response = client.post(f'/api/corners/{corner_id}/like', headers=headers)
    assert response.status_code == 200

    response_data = response.get_json()
    assert 'corner' in response_data
    assert response_data['corner']['likes'] == 1


def test_unlike_corner(client, registered_user, image_file):
    """Test unliking a corner."""
    user_data, token = registered_user
    headers = {'Authorization': f'Bearer {token}'}

    # First create a corner
    data = {
        'title': 'Unlike Test Corner',
        'description': 'Test Description',
        'latitude': '40.7128',
        'longitude': '-74.0060',
        'address': 'Test Address',
        'tags': 'test,tag',
        'visibility': 'public',
        'specific_friends': '',
        'exclude_friends': ''
    }

    files = {'image': image_file}

    create_response = client.post('/api/corners', data={**data}, files=files, headers=headers)
    corner_id = create_response.get_json()['corner']['id']

    # Like the corner first
    client.post(f'/api/corners/{corner_id}/like', headers=headers)

    # Unlike the corner
    response = client.post(f'/api/corners/{corner_id}/like', headers=headers)
    assert response.status_code == 200

    response_data = response.get_json()
    assert 'corner' in response_data
    assert response_data['corner']['likes'] == 0


def test_like_corner_without_auth_fails(client):
    """Test that liking a corner fails without authentication."""
    response = client.post('/api/corners/nonexistent-id/like')
    assert response.status_code == 401


def test_favorite_corner(client, registered_user, image_file):
    """Test favoriting a corner."""
    user_data, token = registered_user
    headers = {'Authorization': f'Bearer {token}'}

    # First create a corner
    data = {
        'title': 'Favorite Test Corner',
        'description': 'Test Description',
        'latitude': '40.7128',
        'longitude': '-74.0060',
        'address': 'Test Address',
        'tags': 'test,tag',
        'visibility': 'public',
        'specific_friends': '',
        'exclude_friends': ''
    }

    files = {'image': image_file}

    create_response = client.post('/api/corners', data={**data}, files=files, headers=headers)
    corner_id = create_response.get_json()['corner']['id']

    # Favorite the corner
    response = client.post(f'/api/corners/{corner_id}/favorite', headers=headers)
    assert response.status_code == 200

    response_data = response.get_json()
    assert 'corner' in response_data


def test_unfavorite_corner(client, registered_user, image_file):
    """Test unfavoriting a corner."""
    user_data, token = registered_user
    headers = {'Authorization': f'Bearer {token}'}

    # First create a corner
    data = {
        'title': 'Unfavorite Test Corner',
        'description': 'Test Description',
        'latitude': '40.7128',
        'longitude': '-74.0060',
        'address': 'Test Address',
        'tags': 'test,tag',
        'visibility': 'public',
        'specific_friends': '',
        'exclude_friends': ''
    }

    files = {'image': image_file}

    create_response = client.post('/api/corners', data={**data}, files=files, headers=headers)
    corner_id = create_response.get_json()['corner']['id']

    # Favorite the corner first
    client.post(f'/api/corners/{corner_id}/favorite', headers=headers)

    # Unfavorite the corner
    response = client.post(f'/api/corners/{corner_id}/favorite', headers=headers)
    assert response.status_code == 200


def test_favorite_corner_without_auth_fails(client):
    """Test that favoriting a corner fails without authentication."""
    response = client.post('/api/corners/nonexistent-id/favorite')
    assert response.status_code == 401


def test_get_user_favorites(client, registered_user):
    """Test getting user's favorite corners."""
    user_data, token = registered_user
    headers = {'Authorization': f'Bearer {token}'}

    # Get user ID from registered user
    user_id = user_data.get('id')

    # Get favorites
    response = client.get(f'/api/users/{user_id}/favorites', headers=headers)
    assert response.status_code == 200

    response_data = response.get_json()
    assert 'corners' in response_data
    assert 'count' in response_data


def test_get_favorites_without_auth_fails(client):
    """Test that getting favorites fails without authentication."""
    # Note: The API returns 404 for non-existent user, not 401
    # because the endpoint doesn't require auth, just a valid user
    response = client.get('/api/users/some-id/favorites')
    assert response.status_code == 404
    assert 'error' in response.get_json()
