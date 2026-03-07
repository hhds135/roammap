"""Tests for comment functionality."""
import pytest


def test_add_comment(client, registered_user, image_file):
    """Test adding a comment to a corner."""
    user_data, token = registered_user
    headers = {'Authorization': f'Bearer {token}'}

    # First create a corner
    data = {
        'title': 'Comment Test Corner',
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

    # Add a comment
    comment_data = {
        'content': 'This is a test comment'
    }
    response = client.post(f'/api/corners/{corner_id}/comment', json=comment_data, headers=headers)
    assert response.status_code == 201

    response_data = response.get_json()
    assert 'corner' in response_data
    assert len(response_data['corner']['comments']) == 1
    assert response_data['corner']['comments'][0]['content'] == 'This is a test comment'


def test_add_comment_empty_content_fails(client, registered_user, image_file):
    """Test that adding comment with empty content fails."""
    user_data, token = registered_user
    headers = {'Authorization': f'Bearer {token}'}

    # First create a corner
    data = {
        'title': 'Comment Test Corner',
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

    # Add empty comment
    comment_data = {
        'content': ''
    }
    response = client.post(f'/api/corners/{corner_id}/comment', json=comment_data, headers=headers)
    assert response.status_code == 400
    assert 'error' in response.get_json()


def test_add_comment_without_auth_fails(client):
    """Test that adding comment fails without authentication."""
    comment_data = {
        'content': 'This is a test comment'
    }
    response = client.post('/api/corners/nonexistent-id/comment', json=comment_data)
    assert response.status_code == 401


def test_delete_comment(client, registered_user, image_file):
    """Test deleting a comment."""
    user_data, token = registered_user
    headers = {'Authorization': f'Bearer {token}'}

    # First create a corner
    data = {
        'title': 'Delete Comment Test Corner',
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

    # Add a comment
    comment_data = {
        'content': 'This is a test comment'
    }
    add_response = client.post(f'/api/corners/{corner_id}/comment', json=comment_data, headers=headers)
    comment_id = add_response.get_json()['corner']['comments'][0]['id']

    # Delete the comment
    response = client.delete(f'/api/corners/{corner_id}/comments/{comment_id}', headers=headers)
    assert response.status_code == 200

    response_data = response.get_json()
    assert 'corner' in response_data
    assert len(response_data['corner']['comments']) == 0


def test_delete_nonexistent_comment_fails(client, registered_user):
    """Test that deleting nonexistent comment fails."""
    user_data, token = registered_user
    headers = {'Authorization': f'Bearer {token}'}

    response = client.delete('/api/corners/nonexistent-id/comments/nonexistent-comment-id', headers=headers)
    assert response.status_code == 404


def test_delete_others_comment_fails(client, registered_user, multiple_registered_users, image_file):
    """Test that deleting someone else's comment fails."""
    user_data, token = registered_user
    headers = {'Authorization': f'Bearer {token}'}

    # First create a corner
    data = {
        'title': 'Delete Others Comment Test Corner',
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

    # Add a comment with first user
    comment_data = {
        'content': 'This is a test comment'
    }
    add_response = client.post(f'/api/corners/{corner_id}/comment', json=comment_data, headers=headers)
    comment_id = add_response.get_json()['corner']['comments'][0]['id']

    # Try to delete with another user
    other_user_data, other_token = multiple_registered_users[0]
    other_headers = {'Authorization': f'Bearer {other_token}'}

    response = client.delete(f'/api/corners/{corner_id}/comments/{comment_id}', headers=other_headers)
    assert response.status_code == 403
    assert 'error' in response.get_json()
