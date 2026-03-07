"""Tests for corner CRUD operations."""
import pytest
from werkzeug.datastructures import ImmutableMultiDict
from tests.conftest import make_test_file_upload


def test_create_corner_with_auth(client, registered_user, image_file):
    """Test corner creation with authentication."""
    user_data, token = registered_user
    headers = {'Authorization': f'Bearer {token}'}

    # Use ImmutableMultiDict for form data with files in Flask 3.x
    data = ImmutableMultiDict([
        ('title', 'Test Corner'),
        ('description', 'Test Description'),
        ('latitude', '40.7128'),
        ('longitude', '-74.0060'),
        ('address', 'Test Address'),
        ('tags', 'test,tag'),
        ('visibility', 'public'),
        ('specific_friends', ''),
        ('exclude_friends', '')
    ])

    # Create multipart form data for file upload
    body, content_type = make_test_file_upload(image_file)
    
    # Merge form data with file data
    full_body = body
    for key, value in data.items(multi=True):
        file_part = (
            f'\r\n------WebKitFormBoundary7MA4YWxkTrZu0gW\r\n'
            f'Content-Disposition: form-data; name="{key}"\r\n\r\n'
            f'{value}\r\n'
        ).encode('utf-8')
        full_body = file_part + full_body
    
    # Add closing boundary
    full_body += b'------WebKitFormBoundary7MA4YWxkTrZu0gW--\r\n'

    upload_headers = {**headers, 'Content-Type': content_type}
    response = client.post('/api/corners', data=full_body, headers=upload_headers)
    assert response.status_code == 201

    response_data = response.get_json()
    assert 'corner' in response_data
    assert response_data['corner']['title'] == 'Test Corner'


def test_create_corner_without_auth_fails(client):
    """Test that corner creation fails without authentication."""
    data = {
        'title': 'Test Corner',
        'description': 'Test Description',
        'latitude': '40.7128',
        'longitude': '-74.0060',
    }

    # Create a test image file
    import io
    from werkzeug.datastructures import FileStorage
    png_data = (
        b'\x89PNG\r\n\x1a\n'
        b'\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x02\x00\x00\x00'
        b'\x90wS\xde'
        b'\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0\x00\x00\x00\x03\x00\x01'
        b' \xf8\xa6\x05\x00'
        b'\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    file_obj = io.BytesIO(png_data)
    image_file = FileStorage(stream=file_obj, filename='test.jpg', content_type='image/jpeg')
    files = {'image': image_file}

    response = client.post('/api/corners', data=data, files=files)
    assert response.status_code == 401


def test_create_corner_missing_fields_fails(client, registered_user, image_file):
    """Test that corner creation fails with missing required fields."""
    user_data, token = registered_user
    headers = {'Authorization': f'Bearer {token}'}

    data = {
        'title': 'Test Corner',
        # Missing description, latitude, longitude
    }

    files = {'image': image_file}

    response = client.post('/api/corners', data=data, files=files, headers=headers)
    assert response.status_code == 400
    assert 'error' in response.get_json()


def test_create_corner_invalid_coordinates_fails(client, registered_user, image_file):
    """Test that corner creation fails with invalid coordinates."""
    user_data, token = registered_user
    headers = {'Authorization': f'Bearer {token}'}

    data = {
        'title': 'Test Corner',
        'description': 'Test Description',
        'latitude': 'invalid',
        'longitude': 'invalid',
    }

    files = {'image': image_file}

    response = client.post('/api/corners', data=data, files=files, headers=headers)
    assert response.status_code == 400
    assert 'error' in response.get_json()


def test_create_corner_without_image_fails(client, registered_user):
    """Test that corner creation fails without image."""
    user_data, token = registered_user
    headers = {'Authorization': f'Bearer {token}'}

    data = {
        'title': 'Test Corner',
        'description': 'Test Description',
        'latitude': '40.7128',
        'longitude': '-74.0060',
    }

    response = client.post('/api/corners', data=data, headers=headers)
    assert response.status_code == 400
    assert 'error' in response.get_json()


def test_get_corners_list(client, registered_user):
    """Test getting list of corners."""
    user_data, token = registered_user
    headers = {'Authorization': f'Bearer {token}'}

    response = client.get('/api/corners', headers=headers)
    assert response.status_code == 200

    response_data = response.get_json()
    assert 'corners' in response_data
    assert isinstance(response_data['corners'], list)


def test_get_corners_without_auth(client):
    """Test getting corners without authentication (should return public corners)."""
    response = client.get('/api/corners')
    assert response.status_code == 200

    response_data = response.get_json()
    assert 'corners' in response_data


def test_get_corner_detail(client, registered_user, image_file):
    """Test getting corner detail."""
    user_data, token = registered_user
    headers = {'Authorization': f'Bearer {token}'}

    # First create a corner
    data = {
        'title': 'Detail Test Corner',
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

    # Get corner detail
    response = client.get(f'/api/corners/{corner_id}', headers=headers)
    assert response.status_code == 200

    response_data = response.get_json()
    assert 'corner' in response_data
    assert response_data['corner']['id'] == corner_id


def test_get_nonexistent_corner_fails(client, registered_user):
    """Test that getting nonexistent corner fails."""
    user_data, token = registered_user
    headers = {'Authorization': f'Bearer {token}'}

    response = client.get('/api/corners/nonexistent-id', headers=headers)
    assert response.status_code == 404
    assert 'error' in response.get_json()


def test_update_corner(client, registered_user, image_file):
    """Test updating a corner."""
    user_data, token = registered_user
    headers = {'Authorization': f'Bearer {token}'}

    # First create a corner
    data = {
        'title': 'Original Title',
        'description': 'Original Description',
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

    # Update the corner
    update_data = {
        'title': 'Updated Title',
        'description': 'Updated Description',
        'latitude': '40.7128',
        'longitude': '-74.0060',
        'address': 'Updated Address',
        'tags': 'updated,tag',
        'visibility': 'public',
        'specific_friends': '',
        'exclude_friends': ''
    }

    update_response = client.put(
        f'/api/corners/{corner_id}',
        data={**update_data},
        files=files,
        headers=headers
    )
    assert update_response.status_code == 200

    update_response_data = update_response.get_json()
    assert 'corner' in update_response_data
    assert update_response_data['corner']['title'] == 'Updated Title'


def test_update_nonexistent_corner_fails(client, registered_user, image_file):
    """Test that updating nonexistent corner fails."""
    user_data, token = registered_user
    headers = {'Authorization': f'Bearer {token}'}

    update_data = {
        'title': 'Updated Title',
        'description': 'Updated Description',
        'latitude': '40.7128',
        'longitude': '-74.0060',
    }

    files = {'image': image_file}

    response = client.put(
        '/api/corners/nonexistent-id',
        data=update_data,
        files=files,
        headers=headers
    )
    assert response.status_code == 404


def test_delete_corner(client, registered_user, image_file):
    """Test deleting a corner."""
    user_data, token = registered_user
    headers = {'Authorization': f'Bearer {token}'}

    # First create a corner
    data = {
        'title': 'Delete Test Corner',
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

    # Delete the corner
    response = client.delete(f'/api/corners/{corner_id}', headers=headers)
    assert response.status_code == 200

    # Verify corner is deleted
    get_response = client.get(f'/api/corners/{corner_id}', headers=headers)
    assert get_response.status_code == 404


def test_delete_nonexistent_corner_fails(client, registered_user):
    """Test that deleting nonexistent corner fails."""
    user_data, token = registered_user
    headers = {'Authorization': f'Bearer {token}'}

    response = client.delete('/api/corners/nonexistent-id', headers=headers)
    assert response.status_code == 404


def test_delete_others_corner_fails(client, registered_user, multiple_registered_users, image_file):
    """Test that deleting someone else's corner fails."""
    user_data, token = registered_user
    headers = {'Authorization': f'Bearer {token}'}

    # Create corner with first user
    data = {
        'title': 'Owner Corner',
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

    # Try to delete with another user
    other_user_data, other_token = multiple_registered_users[0]
    other_headers = {'Authorization': f'Bearer {other_token}'}

    response = client.delete(f'/api/corners/{corner_id}', headers=other_headers)
    assert response.status_code == 403
    assert 'error' in response.get_json()
