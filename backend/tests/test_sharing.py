"""Tests for sharing functionality."""
import pytest


def test_get_shared_corner_with_valid_share_id(client, registered_user, image_file):
    """Test getting a shared corner with valid share_id."""
    user_data, token = registered_user
    headers = {'Authorization': f'Bearer {token}'}

    # First create a corner
    data = {
        'title': 'Share Test Corner',
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
    share_id = create_response.get_json()['corner']['share_id']

    # Get shared corner (no auth required for shared link)
    response = client.get(f'/api/share/{share_id}')
    assert response.status_code == 200

    response_data = response.get_json()
    assert 'corner' in response_data


def test_get_shared_corner_with_invalid_share_id(client):
    """Test getting a shared corner with invalid share_id."""
    response = client.get('/api/share/nonexistent-share-id')
    assert response.status_code == 404
    assert 'error' in response.get_json()


def test_generate_share_link(client, registered_user, image_file):
    """Test generating a share link for a corner."""
    user_data, token = registered_user
    headers = {'Authorization': f'Bearer {token}'}

    # First create a corner
    data = {
        'title': 'Share Link Test Corner',
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

    # Generate share link
    response = client.post(f'/api/corners/{corner_id}/share-link', headers=headers)
    assert response.status_code == 200

    response_data = response.get_json()
    assert 'share_id' in response_data
    assert 'share_url' in response_data


def test_generate_share_link_without_auth_fails(client):
    """Test that generating share link fails without authentication."""
    response = client.post('/api/corners/nonexistent-id/share-link')
    assert response.status_code == 401


def test_generate_share_link_for_nonexistent_corner_fails(client, registered_user):
    """Test that generating share link for nonexistent corner fails."""
    user_data, token = registered_user
    headers = {'Authorization': f'Bearer {token}'}

    response = client.post('/api/corners/nonexistent-id/share-link', headers=headers)
    assert response.status_code == 404
    assert 'error' in response.get_json()


def test_share_link_access_without_auth(client, registered_user, image_file):
    """Test that share link can be accessed without authentication."""
    user_data, token = registered_user
    headers = {'Authorization': f'Bearer {token}'}

    # First create a corner
    data = {
        'title': 'Public Share Test Corner',
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
    share_id = create_response.get_json()['corner']['share_id']

    # Access share link without auth
    response = client.get(f'/api/share/{share_id}')
    assert response.status_code == 200

    response_data = response.get_json()
    assert 'corner' in response_data
    assert response_data['corner']['title'] == 'Public Share Test Corner'
