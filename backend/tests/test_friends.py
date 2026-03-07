"""Tests for friend system functionality."""
import pytest


def test_search_users(client, registered_user, multiple_registered_users):
    """Test searching for users."""
    user_data, token = registered_user
    headers = {'Authorization': f'Bearer {token}'}

    # Search for users
    response = client.get('/api/users/search?q=user', headers=headers)
    assert response.status_code == 200

    response_data = response.get_json()
    assert 'users' in response_data
    assert isinstance(response_data['users'], list)


def test_search_users_without_auth_fails(client):
    """Test that searching users fails without authentication."""
    response = client.get('/api/users/search?q=test')
    assert response.status_code == 401


def test_send_friend_request(client, registered_user, multiple_registered_users):
    """Test sending a friend request."""
    user_data, token = registered_user
    headers = {'Authorization': f'Bearer {token}'}

    # Get another user's ID
    other_user_data, _ = multiple_registered_users[0]
    other_user_id = other_user_data.get('id')

    # Send friend request
    response = client.post('/api/friends/request', json={'receiver_id': other_user_id}, headers=headers)
    assert response.status_code == 200

    response_data = response.get_json()
    assert 'message' in response_data


def test_send_friend_request_to_self_fails(client, registered_user):
    """Test that sending friend request to self fails."""
    user_data, token = registered_user
    headers = {'Authorization': f'Bearer {token}'}

    user_id = user_data.get('id')

    # Use receiver_id (correct API parameter)
    response = client.post('/api/friends/request', json={'receiver_id': user_id}, headers=headers)
    assert response.status_code == 400
    assert 'error' in response.get_json()


def test_send_friend_request_without_auth_fails(client):
    """Test that sending friend request fails without authentication."""
    # Use receiver_id (correct API parameter)
    response = client.post('/api/friends/request', json={'receiver_id': 'some-id'})
    assert response.status_code == 401


def test_accept_friend_request(client, registered_user, multiple_registered_users):
    """Test accepting a friend request."""
    # First user sends request
    user_data, token = registered_user
    headers = {'Authorization': f'Bearer {token}'}

    other_user_data, other_token = multiple_registered_users[0]
    
    # First user sends request to second user
    client.post('/api/friends/request', json={'receiver_id': other_user_data.get('id')}, headers=headers)

    # Second user accepts request from first user
    other_headers = {'Authorization': f'Bearer {other_token}'}
    response = client.put(f'/api/friends/request/{user_data.get("id")}', json={'action': 'accept'}, headers=other_headers)
    assert response.status_code == 200


def test_reject_friend_request(client, registered_user, multiple_registered_users):
    """Test rejecting a friend request."""
    # First user sends request
    user_data, token = registered_user
    headers = {'Authorization': f'Bearer {token}'}

    other_user_data, other_token = multiple_registered_users[0]
    
    # First user sends request to second user
    client.post('/api/friends/request', json={'receiver_id': other_user_data.get('id')}, headers=headers)

    # Second user rejects request from first user
    other_headers = {'Authorization': f'Bearer {other_token}'}
    response = client.put(f'/api/friends/request/{user_data.get("id")}', json={'action': 'reject'}, headers=other_headers)
    assert response.status_code == 200


def test_get_friends(client, registered_user):
    """Test getting friends list."""
    user_data, token = registered_user
    headers = {'Authorization': f'Bearer {token}'}

    response = client.get('/api/friends', headers=headers)
    assert response.status_code == 200

    response_data = response.get_json()
    assert 'friends' in response_data
    assert isinstance(response_data['friends'], list)


def test_get_friends_without_auth_fails(client):
    """Test that getting friends fails without authentication."""
    response = client.get('/api/friends')
    assert response.status_code == 401


def test_get_friend_requests(client, registered_user):
    """Test getting friend requests."""
    user_data, token = registered_user
    headers = {'Authorization': f'Bearer {token}'}

    response = client.get('/api/friends/requests', headers=headers)
    assert response.status_code == 200

    response_data = response.get_json()
    assert 'requests' in response_data
    assert isinstance(response_data['requests'], list)


def test_get_friend_requests_without_auth_fails(client):
    """Test that getting friend requests fails without authentication."""
    response = client.get('/api/friends/requests')
    assert response.status_code == 401


def test_delete_friend(client, registered_user, multiple_registered_users):
    """Test deleting a friend."""
    user_data, token = registered_user
    headers = {'Authorization': f'Bearer {token}'}

    # Get a friend ID (use another test user)
    other_user_data, _ = multiple_registered_users[0]
    friend_id = other_user_data.get('id')

    # Delete friend
    response = client.delete(f'/api/friends/{friend_id}', headers=headers)
    assert response.status_code in [200, 400]  # 400 if not friends


def test_delete_friend_without_auth_fails(client):
    """Test that deleting friend fails without authentication."""
    response = client.delete('/api/friends/some-id')
    assert response.status_code == 401


def test_get_friend_corners(client, registered_user, multiple_registered_users):
    """Test getting friend's corners."""
    user_data, token = registered_user
    headers = {'Authorization': f'Bearer {token}'}

    # Get a friend ID
    other_user_data, _ = multiple_registered_users[0]
    friend_id = other_user_data.get('id')

    response = client.get(f'/api/friends/{friend_id}/corners', headers=headers)
    # API returns 200 (success), 403 (not friends), or 404 (user not found)
    assert response.status_code in [200, 403, 404]

    response_data = response.get_json()
    # Response should have either 'corners' or 'error' key
    assert 'corners' in response_data or 'error' in response_data


def test_get_friend_corners_without_auth_fails(client):
    """Test that getting friend's corners fails without authentication."""
    response = client.get('/api/friends/some-id/corners')
    assert response.status_code == 401
