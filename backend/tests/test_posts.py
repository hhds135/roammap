"""Tests for posts and media endpoints."""
import pytest
import io
from bson import ObjectId
from werkzeug.datastructures import FileStorage

import uuid
from storage.corner_store import CornerStore

def create_test_image_file(filename='test.png'):
    """Create a test image file as FileStorage."""
    # Minimal valid PNG data (1x1 pixel)
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
    return FileStorage(stream=file_obj, filename=filename, content_type='image/png')


def create_test_video_file(filename='test.mp4'):
    """Create a test video file as FileStorage."""
    # Fake MP4 data
    mp4_data = b'\x00\x00\x00\x1cftypmp42\x00\x00\x00\x00mp42isom'
    file_obj = io.BytesIO(mp4_data)
    return FileStorage(stream=file_obj, filename=filename, content_type='video/mp4')


# ==================== Media Upload Tests ====================

class TestMediaUpload:
    """Test media upload functionality."""

    def test_upload_image_success(self, api_client, registered_user):
        """Test successful image upload."""
        # registered_user is a tuple (user_dict, token)
        user_dict, token = registered_user

        # Create test image file
        image_file = create_test_image_file('test_image.png')

        # Upload image
        response, data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token
        )

        assert response.status_code == 201
        assert data['success'] is True
        assert 'file_id' in data['data']
        assert data['data']['media_type'] == 'image'

    def test_upload_video_success(self, api_client, registered_user):
        """Test successful video upload."""
        # registered_user is a tuple (user_dict, token)
        user_dict, token = registered_user

        # Create test video file
        video_file = create_test_video_file('test_video.mp4')

        # Upload video
        response, data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'video'},
            files={'file': video_file},
            auth_token=token
        )

        assert response.status_code == 201
        assert data['success'] is True
        assert data['data']['media_type'] == 'video'

    def test_upload_without_auth_fails(self, api_client):
        """Test that upload fails without authentication."""
        image_file = create_test_image_file('test.png')

        response, data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file}
        )

        assert response.status_code == 401

    def test_upload_missing_media_type_fails(self, api_client, registered_user):
        """Test that upload fails without media_type."""
        user_dict, token = registered_user

        image_file = create_test_image_file('test.png')

        response, data = api_client.post_multipart(
            '/api/media/upload',
            data={},  # No media_type
            files={'file': image_file},
            auth_token=token
        )

        assert response.status_code == 400
        assert 'error' in data

    def test_upload_invalid_media_type_fails(self, api_client, registered_user):
        """Test that upload fails with invalid media_type."""
        user_dict, token = registered_user

        image_file = create_test_image_file('test.png')

        response, data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'invalid_type'},
            files={'file': image_file},
            auth_token=token
        )

        assert response.status_code == 400

    def test_upload_invalid_image_extension_fails(self, api_client, registered_user):
        """Test that upload fails with invalid image extension."""
        user_dict, token = registered_user

        # Try to upload a .exe file as image
        exe_data = b'MZ fake exe data'
        exe_file = FileStorage(stream=io.BytesIO(exe_data), filename='test.exe', content_type='application/octet-stream')

        response, data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': exe_file},
            auth_token=token
        )

        assert response.status_code == 400

    def test_get_media_success(self, api_client, registered_user):
        """Test getting media file by ID."""
        user_dict, token = registered_user

        image_file = create_test_image_file('test.png')

        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token
        )

        file_id = upload_data['data']['file_id']

        # Get media file
        response = api_client.client.get(f'/api/media/{file_id}')
        assert response.status_code == 200
        assert response.content_type.startswith('image/')

    def test_get_media_not_found(self, api_client, registered_user):
        """Test getting non-existent media file."""
        user_dict, token = registered_user

        # Try to get non-existent file
        fake_id = str(ObjectId())
        response = api_client.client.get(f'/api/media/{fake_id}', headers={
            'Authorization': f'Bearer {token}'
        })
        assert response.status_code == 404

    def test_delete_media_success(self, api_client, registered_user):
        """Test deleting own media file."""
        user_dict, token = registered_user

        image_file = create_test_image_file('test.png')

        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token
        )

        file_id = upload_data['data']['file_id']

        # Delete media file
        response, data = api_client.delete(f'/api/media/{file_id}', auth_token=token)
        assert response.status_code == 200
        assert data['success'] is True

    def test_delete_other_user_media_fails(self, api_client, multiple_registered_users):
        """Test that deleting other user's media fails."""
        # Login as user 1 and upload
        user1, token1 = multiple_registered_users[0]

        image_file = create_test_image_file('test.png')

        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token1
        )

        file_id = upload_data['data']['file_id']

        # Login as user 2 and try to delete
        user2, token2 = multiple_registered_users[1]

        response, data = api_client.delete(f'/api/media/{file_id}', auth_token=token2)
        assert response.status_code == 403
        assert 'error' in data


# ==================== Post Creation Tests ====================

class TestPostCreation:
    """Test post creation functionality."""

    def test_create_post_with_image_success(self, api_client, registered_user):
        """Test successful post creation with image."""
        user_dict, token = registered_user

        # Upload image first
        image_file = create_test_image_file('test.png')

        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token
        )

        file_id = upload_data['data']['file_id']

        # Create post
        _, post_data = api_client.post_json('/api/posts', {
            'title': 'Test Post',
            'description': 'Test description',
            'media_type': 'image',
            'media_files': [file_id],
            'visibility': 'public'
        }, auth_token=token)

        assert post_data['success'] is True
        assert post_data['data']['title'] == 'Test Post'
        assert post_data['data']['media_type'] == 'image'

    def test_create_post_with_video_success(self, api_client, registered_user):
        """Test successful post creation with video."""
        user_dict, token = registered_user

        # Upload video first
        video_file = create_test_video_file('test.mp4')

        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'video'},
            files={'file': video_file},
            auth_token=token
        )

        file_id = upload_data['data']['file_id']

        # Create post
        _, post_data = api_client.post_json('/api/posts', {
            'title': 'Test Video Post',
            'description': 'Test video description',
            'media_type': 'video',
            'media_files': [file_id],
            'visibility': 'public'
        }, auth_token=token)

        assert post_data['success'] is True
        assert post_data['data']['media_type'] == 'video'

    def test_create_post_without_auth_fails(self, api_client):
        """Test that post creation fails without authentication."""
        response, data = api_client.post_json('/api/posts', {
            'title': 'Test Post',
            'media_type': 'image',
            'media_files': ['fake_id']
        })

        assert response.status_code == 401

    def test_create_post_missing_title_fails(self, api_client, registered_user):
        """Test that post creation fails without title."""
        user_dict, token = registered_user

        response, data = api_client.post_json('/api/posts', {
            'description': 'Test description',
            'media_type': 'image',
            'media_files': ['fake_id']
        }, auth_token=token)

        assert response.status_code == 400
        assert 'Missing required field: title' in data['error']

    def test_create_post_missing_media_files_fails(self, api_client, registered_user):
        """Test that post creation fails without media_files."""
        user_dict, token = registered_user

        response, data = api_client.post_json('/api/posts', {
            'title': 'Test Post',
            'media_type': 'image'
        }, auth_token=token)

        assert response.status_code == 400
        assert 'Missing required field: media_files' in data['error']

    def test_create_post_invalid_media_type_fails(self, api_client, registered_user):
        """Test that post creation fails with invalid media_type."""
        user_dict, token = registered_user

        response, data = api_client.post_json('/api/posts', {
            'title': 'Test Post',
            'media_type': 'invalid',
            'media_files': ['fake_id']
        }, auth_token=token)

        assert response.status_code == 400
        assert 'media_type must be' in data['error']

    def test_create_post_invalid_visibility_fails(self, api_client, registered_user):
        """Test that post creation fails with invalid visibility."""
        user_dict, token = registered_user

        response, data = api_client.post_json('/api/posts', {
            'title': 'Test Post',
            'media_type': 'image',
            'media_files': ['fake_id'],
            'visibility': 'invalid_visibility'
        }, auth_token=token)

        assert response.status_code == 400
        assert 'visibility must be' in data['error']

    def test_create_post_with_nonexistent_file_fails(self, api_client, registered_user):
        """Test that post creation fails with non-existent media file."""
        user_dict, token = registered_user

        response, data = api_client.post_json('/api/posts', {
            'title': 'Test Post',
            'media_type': 'image',
            'media_files': [str(ObjectId())],  # Non-existent file ID
        }, auth_token=token)

        assert response.status_code == 404
        assert 'Media file not found' in data['error']

    def test_create_post_with_tags_success(self, api_client, registered_user):
        """Test post creation with tags."""
        user_dict, token = registered_user

        # Upload image
        image_file = create_test_image_file('test.png')

        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token
        )

        file_id = upload_data['data']['file_id']

        # Create post with tags
        _, post_data = api_client.post_json('/api/posts', {
            'title': 'Test Post with Tags',
            'description': 'Test description',
            'media_type': 'image',
            'media_files': [file_id],
            'tags': ['美食', '咖啡', '周末'],
            'visibility': 'public'
        }, auth_token=token)

        assert post_data['success'] is True
        assert '美食' in post_data['data']['tags']


# ==================== Post Retrieval Tests ====================

class TestPostRetrieval:
    """Test post retrieval functionality."""

    def test_get_public_post_success(self, api_client, registered_user):
        """Test getting a public post without authentication."""
        user_dict, token = registered_user

        image_file = create_test_image_file('test.png')

        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token
        )

        file_id = upload_data['data']['file_id']

        _, post_data = api_client.post_json('/api/posts', {
            'title': 'Public Post',
            'media_type': 'image',
            'media_files': [file_id],
            'visibility': 'public'
        }, auth_token=token)

        post_id = post_data['data']['_id']

        # Get post without auth
        response, data = api_client.get_json(f'/api/posts/{post_id}')
        assert response.status_code == 200
        assert data['success'] is True
        assert data['data']['title'] == 'Public Post'

    def test_get_private_post_as_creator_success(self, api_client, registered_user):
        """Test getting a private post as the creator."""
        user_dict, token = registered_user

        image_file = create_test_image_file('test.png')

        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token
        )

        file_id = upload_data['data']['file_id']

        _, post_data = api_client.post_json('/api/posts', {
            'title': 'Private Post',
            'media_type': 'image',
            'media_files': [file_id],
            'visibility': 'private'
        }, auth_token=token)

        post_id = post_data['data']['_id']

        # Get post as creator
        response, data = api_client.get_json(f'/api/posts/{post_id}', auth_token=token)
        assert response.status_code == 200
        assert data['data']['title'] == 'Private Post'

    def test_get_private_post_as_other_user_fails(self, api_client, multiple_registered_users):
        """Test that getting another user's private post fails."""
        # User 1 creates private post
        user1, token1 = multiple_registered_users[0]

        image_file = create_test_image_file('test.png')

        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token1
        )

        file_id = upload_data['data']['file_id']

        _, post_data = api_client.post_json('/api/posts', {
            'title': 'Private Post',
            'media_type': 'image',
            'media_files': [file_id],
            'visibility': 'private'
        }, auth_token=token1)

        post_id = post_data['data']['_id']

        # User 2 tries to get post
        user2, token2 = multiple_registered_users[1]

        response, data = api_client.get_json(f'/api/posts/{post_id}', auth_token=token2)
        assert response.status_code == 403
        assert 'error' in data

    def test_get_post_not_found(self, api_client, registered_user):
        """Test getting non-existent post."""
        user_dict, token = registered_user

        fake_id = str(ObjectId())
        response, data = api_client.get_json(f'/api/posts/{fake_id}', auth_token=token)
        assert response.status_code == 404
        assert 'Post not found' in data['error']


# ==================== Post Update Tests ====================

class TestPostUpdate:
    """Test post update functionality."""

    def test_update_post_title_success(self, api_client, registered_user):
        """Test updating post title."""
        user_dict, token = registered_user

        image_file = create_test_image_file('test.png')

        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token
        )

        file_id = upload_data['data']['file_id']

        _, post_data = api_client.post_json('/api/posts', {
            'title': 'Original Title',
            'media_type': 'image',
            'media_files': [file_id],
            'visibility': 'public'
        }, auth_token=token)

        post_id = post_data['data']['_id']

        # Update title
        _, update_data = api_client.put_json(f'/api/posts/{post_id}', {
            'title': 'Updated Title'
        }, auth_token=token)

        assert update_data['success'] is True
        assert update_data['data']['title'] == 'Updated Title'

    def test_update_post_visibility_success(self, api_client, registered_user):
        """Test updating post visibility."""
        user_dict, token = registered_user

        image_file = create_test_image_file('test.png')

        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token
        )

        file_id = upload_data['data']['file_id']

        _, post_data = api_client.post_json('/api/posts', {
            'title': 'Test Post',
            'media_type': 'image',
            'media_files': [file_id],
            'visibility': 'public'
        }, auth_token=token)

        post_id = post_data['data']['_id']

        # Update visibility
        _, update_data = api_client.put_json(f'/api/posts/{post_id}', {
            'visibility': 'private'
        }, auth_token=token)

        assert update_data['success'] is True
        assert update_data['data']['visibility'] == 'private'

    def test_update_other_user_post_fails(self, api_client, multiple_registered_users):
        """Test that updating another user's post fails."""
        # User 1 creates post
        user1, token1 = multiple_registered_users[0]

        image_file = create_test_image_file('test.png')

        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token1
        )

        file_id = upload_data['data']['file_id']

        _, post_data = api_client.post_json('/api/posts', {
            'title': 'User 1 Post',
            'media_type': 'image',
            'media_files': [file_id],
            'visibility': 'public'
        }, auth_token=token1)

        post_id = post_data['data']['_id']

        # User 2 tries to update
        user2, token2 = multiple_registered_users[1]

        response, data = api_client.put_json(f'/api/posts/{post_id}', {
            'title': 'Hacked Title'
        }, auth_token=token2)

        assert response.status_code == 403
        assert 'error' in data


# ==================== Post Delete Tests ====================

class TestPostDelete:
    """Test post delete functionality."""

    def test_delete_post_success(self, api_client, registered_user):
        """Test deleting own post."""
        user_dict, token = registered_user

        image_file = create_test_image_file('test.png')

        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token
        )

        file_id = upload_data['data']['file_id']

        _, post_data = api_client.post_json('/api/posts', {
            'title': 'Post to Delete',
            'media_type': 'image',
            'media_files': [file_id],
            'visibility': 'public'
        }, auth_token=token)

        post_id = post_data['data']['_id']

        # Delete post
        response, data = api_client.delete(f'/api/posts/{post_id}', auth_token=token)
        assert response.status_code == 200
        assert data['success'] is True

        # Verify post is deleted
        response, data = api_client.get_json(f'/api/posts/{post_id}', auth_token=token)
        assert response.status_code == 404

    def test_delete_other_user_post_fails(self, api_client, multiple_registered_users):
        """Test that deleting another user's post fails."""
        # User 1 creates post
        user1, token1 = multiple_registered_users[0]

        image_file = create_test_image_file('test.png')

        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token1
        )

        file_id = upload_data['data']['file_id']

        _, post_data = api_client.post_json('/api/posts', {
            'title': 'User 1 Post',
            'media_type': 'image',
            'media_files': [file_id],
            'visibility': 'public'
        }, auth_token=token1)

        post_id = post_data['data']['_id']

        # User 2 tries to delete
        user2, token2 = multiple_registered_users[1]

        response, data = api_client.delete(f'/api/posts/{post_id}', auth_token=token2)
        assert response.status_code == 403
        assert 'error' in data


# ==================== Post List Tests ====================

class TestPostList:
    """Test post list functionality."""

    def test_get_posts_list_success(self, api_client, registered_user):
        """Test getting posts list."""
        user_dict, token = registered_user

        image_file = create_test_image_file('test.png')

        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token
        )

        file_id = upload_data['data']['file_id']

        # Create multiple posts
        for i in range(3):
            api_client.post_json('/api/posts', {
                'title': f'Test Post {i}',
                'media_type': 'image',
                'media_files': [file_id],
                'visibility': 'public'
            }, auth_token=token)

        # Get posts list
        response, data = api_client.get_json('/api/posts')
        assert response.status_code == 200
        assert data['success'] is True
        assert 'posts' in data['data']
        assert 'total' in data['data']

    def test_get_posts_with_pagination(self, api_client, registered_user):
        """Test posts list with pagination."""
        user_dict, token = registered_user

        image_file = create_test_image_file('test.png')

        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token
        )

        file_id = upload_data['data']['file_id']

        # Create posts
        for i in range(5):
            api_client.post_json('/api/posts', {
                'title': f'Test Post {i}',
                'media_type': 'image',
                'media_files': [file_id],
                'visibility': 'public'
            }, auth_token=token)

        # Get first page
        response, data = api_client.get_json('/api/posts', query_params={'limit': 2, 'skip': 0})
        assert len(data['data']['posts']) == 2
        assert data['data']['limit'] == 2
        assert data['data']['skip'] == 0

        # Get second page
        response, data = api_client.get_json('/api/posts', query_params={'limit': 2, 'skip': 2})
        assert len(data['data']['posts']) == 2
        assert data['data']['skip'] == 2

    def test_get_posts_by_user(self, api_client, multiple_registered_users):
        """Test getting posts by specific user."""
        # User 1 creates posts
        user1, token1 = multiple_registered_users[0]

        image_file = create_test_image_file('test.png')

        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token1
        )

        file_id = upload_data['data']['file_id']

        user1_id = user1['id']

        # User 1 creates 2 posts
        api_client.post_json('/api/posts', {
            'title': 'User 1 Post 1',
            'media_type': 'image',
            'media_files': [file_id],
            'visibility': 'public'
        }, auth_token=token1)

        api_client.post_json('/api/posts', {
            'title': 'User 1 Post 2',
            'media_type': 'image',
            'media_files': [file_id],
            'visibility': 'public'
        }, auth_token=token1)

        # Get posts by user 1
        response, data = api_client.get_json('/api/posts', query_params={'user_id': user1_id})
        assert response.status_code == 200
        assert data['data']['total'] >= 2


# ==================== User Interest Tags Tests ====================

class TestUserInterestTags:
    """Test user interest tags functionality."""

    def test_get_user_interests_success(self, api_client, registered_user):
        """Test getting user interest tags."""
        user_dict, token = registered_user
        user_id = user_dict['id']

        response, data = api_client.get_json(f'/api/users/{user_id}/interests')
        assert response.status_code == 200
        assert data['success'] is True
        assert 'interest_tags' in data['data']

    def test_update_user_interests_success(self, api_client, registered_user):
        """Test updating user interest tags."""
        user_dict, token = registered_user
        user_id = user_dict['id']

        # Update interests
        _, update_data = api_client.put_json(f'/api/users/{user_id}/interests', {
            'interest_tags': ['美食', '旅行', '摄影']
        }, auth_token=token)

        assert update_data['success'] is True
        assert '美食' in update_data['data']['interest_tags']
        assert '旅行' in update_data['data']['interest_tags']

    def test_update_other_user_interests_fails(self, api_client, multiple_registered_users):
        """Test that updating another user's interests fails."""
        # Login as user 1
        user1, token1 = multiple_registered_users[0]

        user2_id = multiple_registered_users[1][0]['id']

        # Try to update user 2's interests
        response, data = api_client.put_json(f'/api/users/{user2_id}/interests', {
            'interest_tags': ['美食']
        }, auth_token=token1)

        assert response.status_code == 403
        assert 'error' in data

    def test_update_interests_too_many_tags_fails(self, api_client, registered_user):
        """Test that updating with too many tags fails."""
        user_dict, token = registered_user
        user_id = user_dict['id']

        # Try to update with 15 tags (max is 10)
        response, data = api_client.put_json(f'/api/users/{user_id}/interests', {
            'interest_tags': [f'tag{i}' for i in range(15)]
        }, auth_token=token)

        assert response.status_code == 400
        assert 'Maximum' in data['error']

    def test_update_interests_long_tag_fails(self, api_client, registered_user):
        """Test that updating with too long tag fails."""
        user_dict, token = registered_user
        user_id = user_dict['id']

        # Try to update with tag longer than 20 characters
        response, data = api_client.put_json(f'/api/users/{user_id}/interests', {
            'interest_tags': ['ThisIsAVeryLongTagNameThatExceedsLimit']
        }, auth_token=token)

        assert response.status_code == 400
        assert 'exceeds maximum length' in data['error']


# ==================== Post Likes Tests ====================

class TestPostLikes:
    """Test post like functionality."""

    def test_like_post_success(self, api_client, registered_user):
        """Test liking a post."""
        user_dict, token = registered_user

        # Upload image
        image_file = create_test_image_file('test.png')
        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token
        )

        file_id = upload_data['data']['file_id']

        # Create post
        _, post_data = api_client.post_json('/api/posts', {
            'title': 'Test Post',
            'media_type': 'image',
            'media_files': [file_id],
            'visibility': 'public'
        }, auth_token=token)

        post_id = post_data['data']['_id']

        # Like post
        response, data = api_client.post(f'/api/posts/{post_id}/like', auth_token=token)
        assert response.status_code == 200
        assert data['success'] is True
        assert data['data']['is_liked'] is True
        assert data['data']['likes_count'] == 1

    def test_unlike_post_success(self, api_client, registered_user):
        """Test unliking a post."""
        user_dict, token = registered_user

        # Upload image
        image_file = create_test_image_file('test.png')
        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token
        )

        file_id = upload_data['data']['file_id']

        # Create post
        _, post_data = api_client.post_json('/api/posts', {
            'title': 'Test Post',
            'media_type': 'image',
            'media_files': [file_id],
            'visibility': 'public'
        }, auth_token=token)

        post_id = post_data['data']['_id']

        # Like post
        api_client.post(f'/api/posts/{post_id}/like', auth_token=token)

        # Unlike post
        response, data = api_client.post(f'/api/posts/{post_id}/like', auth_token=token)
        assert response.status_code == 200
        assert data['data']['is_liked'] is False
        assert data['data']['likes_count'] == 0

    def test_like_post_without_auth_fails(self, api_client, registered_user):
        """Test that liking without auth fails."""
        user_dict, token = registered_user

        # Upload image
        image_file = create_test_image_file('test.png')
        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token
        )

        file_id = upload_data['data']['file_id']

        # Create post
        _, post_data = api_client.post_json('/api/posts', {
            'title': 'Test Post',
            'media_type': 'image',
            'media_files': [file_id],
            'visibility': 'public'
        }, auth_token=token)

        post_id = post_data['data']['_id']

        # Try to like without auth
        response, data = api_client.post(f'/api/posts/{post_id}/like')
        assert response.status_code == 401

    def test_like_private_post_as_creator(self, api_client, registered_user):
        """Test liking own private post."""
        user_dict, token = registered_user

        # Upload image
        image_file = create_test_image_file('test.png')
        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token
        )

        file_id = upload_data['data']['file_id']

        # Create private post
        _, post_data = api_client.post_json('/api/posts', {
            'title': 'Private Post',
            'media_type': 'image',
            'media_files': [file_id],
            'visibility': 'private'
        }, auth_token=token)

        post_id = post_data['data']['_id']

        # Like own post
        response, data = api_client.post(f'/api/posts/{post_id}/like', auth_token=token)
        assert response.status_code == 200
        assert data['data']['is_liked'] is True

    def test_like_private_post_as_other_user_fails(self, api_client, multiple_registered_users):
        """Test that liking other user's private post fails."""
        user1, token1 = multiple_registered_users[0]

        # Upload image
        image_file = create_test_image_file('test.png')
        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token1
        )

        file_id = upload_data['data']['file_id']

        # Create private post
        _, post_data = api_client.post_json('/api/posts', {
            'title': 'Private Post',
            'media_type': 'image',
            'media_files': [file_id],
            'visibility': 'private'
        }, auth_token=token1)

        post_id = post_data['data']['_id']

        # User 2 tries to like
        user2, token2 = multiple_registered_users[1]
        response, data = api_client.post(f'/api/posts/{post_id}/like', auth_token=token2)
        assert response.status_code == 403

    def test_get_post_likes(self, api_client, registered_user):
        """Test getting post likes."""
        user_dict, token = registered_user

        # Upload image
        image_file = create_test_image_file('test.png')
        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token
        )

        file_id = upload_data['data']['file_id']

        # Create post
        _, post_data = api_client.post_json('/api/posts', {
            'title': 'Test Post',
            'media_type': 'image',
            'media_files': [file_id],
            'visibility': 'public'
        }, auth_token=token)

        post_id = post_data['data']['_id']

        # Like post
        api_client.post(f'/api/posts/{post_id}/like', auth_token=token)

        # Get likes
        response, data = api_client.get_json(f'/api/posts/{post_id}/likes')
        assert response.status_code == 200
        assert data['success'] is True
        assert data['data']['total'] == 1


# ==================== Post Comments Tests ====================

class TestPostComments:
    """Test post comment functionality."""

    def test_add_comment_success(self, api_client, registered_user):
        """Test adding a comment to a post."""
        user_dict, token = registered_user

        # Upload image
        image_file = create_test_image_file('test.png')
        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token
        )

        file_id = upload_data['data']['file_id']

        # Create post
        _, post_data = api_client.post_json('/api/posts', {
            'title': 'Test Post',
            'media_type': 'image',
            'media_files': [file_id],
            'visibility': 'public'
        }, auth_token=token)

        post_id = post_data['data']['_id']

        # Add comment
        response, data = api_client.post_json(f'/api/posts/{post_id}/comments', {
            'content': 'Test comment'
        }, auth_token=token)

        assert response.status_code == 201
        assert data['success'] is True
        assert data['data']['content'] == 'Test comment'

    def test_add_comment_without_auth_fails(self, api_client, registered_user):
        """Test that adding comment without auth fails."""
        user_dict, token = registered_user

        # Upload image
        image_file = create_test_image_file('test.png')
        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token
        )

        file_id = upload_data['data']['file_id']

        # Create post
        _, post_data = api_client.post_json('/api/posts', {
            'title': 'Test Post',
            'media_type': 'image',
            'media_files': [file_id],
            'visibility': 'public'
        }, auth_token=token)

        post_id = post_data['data']['_id']

        # Try to add comment without auth
        response, data = api_client.post_json(f'/api/posts/{post_id}/comments', {
            'content': 'Test comment'
        })
        assert response.status_code == 401

    def test_add_empty_comment_fails(self, api_client, registered_user):
        """Test that adding empty comment fails."""
        user_dict, token = registered_user

        # Upload image
        image_file = create_test_image_file('test.png')
        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token
        )

        file_id = upload_data['data']['file_id']

        # Create post
        _, post_data = api_client.post_json('/api/posts', {
            'title': 'Test Post',
            'media_type': 'image',
            'media_files': [file_id],
            'visibility': 'public'
        }, auth_token=token)

        post_id = post_data['data']['_id']

        # Try to add empty comment
        response, data = api_client.post_json(f'/api/posts/{post_id}/comments', {
            'content': ''
        }, auth_token=token)
        assert response.status_code == 400

    def test_get_post_comments(self, api_client, registered_user):
        """Test getting post comments."""
        user_dict, token = registered_user

        # Upload image
        image_file = create_test_image_file('test.png')
        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token
        )

        file_id = upload_data['data']['file_id']

        # Create post
        _, post_data = api_client.post_json('/api/posts', {
            'title': 'Test Post',
            'media_type': 'image',
            'media_files': [file_id],
            'visibility': 'public'
        }, auth_token=token)

        post_id = post_data['data']['_id']

        # Add comment
        api_client.post_json(f'/api/posts/{post_id}/comments', {
            'content': 'Test comment'
        }, auth_token=token)

        # Get comments
        response, data = api_client.get_json(f'/api/posts/{post_id}/comments')
        assert response.status_code == 200
        assert data['success'] is True
        assert data['data']['total'] == 1

    def test_update_comment_success(self, api_client, registered_user):
        """Test updating own comment."""
        user_dict, token = registered_user

        # Upload image
        image_file = create_test_image_file('test.png')
        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token
        )

        file_id = upload_data['data']['file_id']

        # Create post
        _, post_data = api_client.post_json('/api/posts', {
            'title': 'Test Post',
            'media_type': 'image',
            'media_files': [file_id],
            'visibility': 'public'
        }, auth_token=token)

        post_id = post_data['data']['_id']

        # Add comment
        _, comment_data = api_client.post_json(f'/api/posts/{post_id}/comments', {
            'content': 'Test comment'
        }, auth_token=token)

        comment_id = comment_data['data']['_id']

        # Update comment
        response, data = api_client.put_json(f'/api/posts/{post_id}/comments/{comment_id}', {
            'content': 'Updated comment'
        }, auth_token=token)

        assert response.status_code == 200
        assert data['data']['content'] == 'Updated comment'

    def test_update_other_user_comment_fails(self, api_client, multiple_registered_users):
        """Test that updating other user's comment fails."""
        user1, token1 = multiple_registered_users[0]

        # Upload image
        image_file = create_test_image_file('test.png')
        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token1
        )

        file_id = upload_data['data']['file_id']

        # Create post
        _, post_data = api_client.post_json('/api/posts', {
            'title': 'Test Post',
            'media_type': 'image',
            'media_files': [file_id],
            'visibility': 'public'
        }, auth_token=token1)

        post_id = post_data['data']['_id']

        # Add comment
        _, comment_data = api_client.post_json(f'/api/posts/{post_id}/comments', {
            'content': 'Test comment'
        }, auth_token=token1)

        comment_id = comment_data['data']['_id']

        # User 2 tries to update
        user2, token2 = multiple_registered_users[1]
        response, data = api_client.put_json(f'/api/posts/{post_id}/comments/{comment_id}', {
            'content': 'Updated comment'
        }, auth_token=token2)
        assert response.status_code == 403

    def test_delete_comment_success(self, api_client, registered_user):
        """Test deleting own comment."""
        user_dict, token = registered_user

        # Upload image
        image_file = create_test_image_file('test.png')
        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token
        )

        file_id = upload_data['data']['file_id']

        # Create post
        _, post_data = api_client.post_json('/api/posts', {
            'title': 'Test Post',
            'media_type': 'image',
            'media_files': [file_id],
            'visibility': 'public'
        }, auth_token=token)

        post_id = post_data['data']['_id']

        # Add comment
        _, comment_data = api_client.post_json(f'/api/posts/{post_id}/comments', {
            'content': 'Test comment'
        }, auth_token=token)

        comment_id = comment_data['data']['_id']

        # Delete comment
        response, data = api_client.delete(f'/api/posts/{post_id}/comments/{comment_id}', auth_token=token)
        assert response.status_code == 200
        assert data['success'] is True


# ==================== Post Favorites Tests ====================

class TestPostFavorites:
    """Test post favorite functionality."""

    def test_favorite_post_success(self, api_client, registered_user):
        """Test favoriting a post."""
        user_dict, token = registered_user

        # Upload image
        image_file = create_test_image_file('test.png')
        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token
        )

        file_id = upload_data['data']['file_id']

        # Create post
        _, post_data = api_client.post_json('/api/posts', {
            'title': 'Test Post',
            'media_type': 'image',
            'media_files': [file_id],
            'visibility': 'public'
        }, auth_token=token)

        post_id = post_data['data']['_id']

        # Favorite post
        response, data = api_client.post(f'/api/posts/{post_id}/favorite', auth_token=token)
        assert response.status_code == 200
        assert data['success'] is True
        assert data['data']['is_favorited'] is True
        assert data['data']['favorites_count'] == 1

    def test_unfavorite_post_success(self, api_client, registered_user):
        """Test unfavoriting a post."""
        user_dict, token = registered_user

        # Upload image
        image_file = create_test_image_file('test.png')
        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token
        )

        file_id = upload_data['data']['file_id']

        # Create post
        _, post_data = api_client.post_json('/api/posts', {
            'title': 'Test Post',
            'media_type': 'image',
            'media_files': [file_id],
            'visibility': 'public'
        }, auth_token=token)

        post_id = post_data['data']['_id']

        # Favorite post
        api_client.post(f'/api/posts/{post_id}/favorite', auth_token=token)

        # Unfavorite post
        response, data = api_client.post(f'/api/posts/{post_id}/favorite', auth_token=token)
        assert response.status_code == 200
        assert data['data']['is_favorited'] is False
        assert data['data']['favorites_count'] == 0

    def test_favorite_post_without_auth_fails(self, api_client, registered_user):
        """Test that favoriting without auth fails."""
        user_dict, token = registered_user

        # Upload image
        image_file = create_test_image_file('test.png')
        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token
        )

        file_id = upload_data['data']['file_id']

        # Create post
        _, post_data = api_client.post_json('/api/posts', {
            'title': 'Test Post',
            'media_type': 'image',
            'media_files': [file_id],
            'visibility': 'public'
        }, auth_token=token)

        post_id = post_data['data']['_id']

        # Try to favorite without auth
        response, data = api_client.post(f'/api/posts/{post_id}/favorite')
        assert response.status_code == 401

    def test_get_post_favorites(self, api_client, registered_user):
        """Test getting post favorites."""
        user_dict, token = registered_user

        # Upload image
        image_file = create_test_image_file('test.png')
        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token
        )

        file_id = upload_data['data']['file_id']

        # Create post
        _, post_data = api_client.post_json('/api/posts', {
            'title': 'Test Post',
            'media_type': 'image',
            'media_files': [file_id],
            'visibility': 'public'
        }, auth_token=token)

        post_id = post_data['data']['_id']

        # Favorite post
        api_client.post(f'/api/posts/{post_id}/favorite', auth_token=token)

        # Get favorites
        response, data = api_client.get_json(f'/api/posts/{post_id}/favorites')
        assert response.status_code == 200
        assert data['success'] is True
        assert data['data']['total'] == 1


# ==================== Followers Visibility Tests ====================

class TestFollowersVisibility:
    """Test followers-only visibility."""

    def test_get_followers_only_post_as_follower(self, api_client, multiple_registered_users, user_store):
        """Test that followers can view followers-only posts."""
        user1, token1 = multiple_registered_users[0]
        user2, token2 = multiple_registered_users[1]

        # User 2 follows User 1 using user_store
        user_store.follow(ObjectId(user2['id']), ObjectId(user1['id']))

        # Upload image
        image_file = create_test_image_file('test.png')
        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token1
        )

        file_id = upload_data['data']['file_id']

        # Create followers-only post
        _, post_data = api_client.post_json('/api/posts', {
            'title': 'Followers Only',
            'media_type': 'image',
            'media_files': [file_id],
            'visibility': 'followers'
        }, auth_token=token1)

        post_id = post_data['data']['_id']

        # User 2 can view post
        response, data = api_client.get_json(f'/api/posts/{post_id}', auth_token=token2)
        assert response.status_code == 200
        assert data['success'] is True

    def test_get_followers_only_post_as_non_follower_fails(self, api_client, multiple_registered_users):
        """Test that non-followers cannot view followers-only posts."""
        user1, token1 = multiple_registered_users[0]
        user3, token3 = multiple_registered_users[2]

        # Upload image
        image_file = create_test_image_file('test.png')
        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token1
        )

        file_id = upload_data['data']['file_id']

        # Create followers-only post
        _, post_data = api_client.post_json('/api/posts', {
            'title': 'Followers Only',
            'media_type': 'image',
            'media_files': [file_id],
            'visibility': 'followers'
        }, auth_token=token1)

        post_id = post_data['data']['_id']

        # User 3 does not follow User 1
        response, data = api_client.get_json(f'/api/posts/{post_id}', auth_token=token3)
        assert response.status_code == 403

    def test_get_followers_only_post_as_creator(self, api_client, registered_user):
        """Test that creator can view own followers-only post."""
        user_dict, token = registered_user

        # Upload image
        image_file = create_test_image_file('test.png')
        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token
        )

        file_id = upload_data['data']['file_id']

        # Create followers-only post
        _, post_data = api_client.post_json('/api/posts', {
            'title': 'Followers Only',
            'media_type': 'image',
            'media_files': [file_id],
            'visibility': 'followers'
        }, auth_token=token)

        post_id = post_data['data']['_id']

        # Creator can view
        response, data = api_client.get_json(f'/api/posts/{post_id}', auth_token=token)
        assert response.status_code == 200


# ==================== Corner Association Tests ====================

class TestCornerAssociation:
    """Test post-corner associations."""

    def test_create_post_with_corners(self, api_client, registered_user, corner_store):
        """Test creating a post with corner references."""
        user_dict, token = registered_user

        # Create corners using store with unique names
        unique_id = str(uuid.uuid4())[:8]
        corner1_id = corner_store.create_corner(
            name=f'Corner 1_{unique_id}',
            description='Test corner',
            latitude=31.2304,
            longitude=121.4737,
            address='Test address 1'
        )

        corner2_id = corner_store.create_corner(
            name=f'Corner 2_{unique_id}',
            description='Test corner',
            latitude=31.2404,
            longitude=121.4837,
            address='Test address 2'
        )

        # Upload image
        image_file = create_test_image_file('test.png')
        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token
        )

        file_id = upload_data['data']['file_id']

        # Create post with corners
        _, post_data = api_client.post_json('/api/posts', {
            'title': 'Post with Corners',
            'media_type': 'image',
            'media_files': [file_id],
            'corner_ids': [str(corner1_id), str(corner2_id)],
            'visibility': 'public'
        }, auth_token=token)

        assert len(post_data['data']['corner_ids']) == 2
        assert len(post_data['data']['corners']) == 2

    def test_create_post_with_nonexistent_corner_fails(self, api_client, registered_user):
        """Test that creating post with nonexistent corner fails."""
        user_dict, token = registered_user

        # Upload image
        image_file = create_test_image_file('test.png')
        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token
        )

        file_id = upload_data['data']['file_id']

        # Try to create post with nonexistent corner
        response, data = api_client.post_json('/api/posts', {
            'title': 'Post with Corners',
            'media_type': 'image',
            'media_files': [file_id],
            'corner_ids': [str(ObjectId())],
            'visibility': 'public'
        }, auth_token=token)

        assert response.status_code == 404

# ==================== Route Functionality Tests ====================

class TestRouteFunctionality:
    """Test route functionality in posts."""

    def test_create_post_with_route(self, api_client, registered_user, corner_store):
        """Test creating a post with a route."""
        user_dict, token = registered_user

        # Create corners using store with unique names
        unique_id = str(uuid.uuid4())[:8]
        corner1_id = corner_store.create_corner(
            name=f'Corner 1_{unique_id}',
            description='Test corner',
            latitude=31.2304,
            longitude=121.4737,
            address='Test address 1'
        )

        corner2_id = corner_store.create_corner(
            name=f'Corner 2_{unique_id}',
            description='Test corner',
            latitude=31.2404,
            longitude=121.4837,
            address='Test address 2'
        )

        # Upload image
        image_file = create_test_image_file('test.png')
        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token
        )

        file_id = upload_data['data']['file_id']

        # Create post with route
        _, post_data = api_client.post_json('/api/posts', {
            'title': 'Post with Route',
            'media_type': 'image',
            'media_files': [file_id],
            'corner_ids': [str(corner1_id), str(corner2_id)],
            'route': {
                'route_name': 'Test Route',
                'corner_ids': [str(corner1_id), str(corner2_id)]
            },
            'visibility': 'public'
        }, auth_token=token)

        assert 'route' in post_data['data']
        assert post_data['data']['route']['route_name'] == 'Test Route'
        assert len(post_data['data']['route']['corner_ids']) == 2

    def test_create_post_with_invalid_route_corner_fails(self, api_client, registered_user, corner_store):
        """Test that creating post with route corner not in corner_ids fails."""
        user_dict, token = registered_user

        # Create corner with unique name
        unique_id = str(uuid.uuid4())[:8]
        corner1_id = corner_store.create_corner(
            name=f'Corner 1_{unique_id}',
            description='Test corner',
            latitude=31.2304,
            longitude=121.4737,
            address='Test address 1'
        )

        # Upload image
        image_file = create_test_image_file('test.png')
        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token
        )

        file_id = upload_data['data']['file_id']

        # Try to create post with route corner not in corner_ids
        response, data = api_client.post_json('/api/posts', {
            'title': 'Post with Route',
            'media_type': 'image',
            'media_files': [file_id],
            'corner_ids': [str(corner1_id)],
            'route': {
                'route_name': 'Test Route',
                'corner_ids': [str(corner1_id), str(ObjectId())]
            },
            'visibility': 'public'
        }, auth_token=token)

        assert response.status_code == 400

    def test_create_post_with_route_missing_name_fails(self, api_client, registered_user, corner_store):
        """Test that creating post with route missing name fails."""
        user_dict, token = registered_user

        # Create corner with unique name
        unique_id = str(uuid.uuid4())[:8]
        corner1_id = corner_store.create_corner(
            name=f'Corner 1_{unique_id}',
            description='Test corner',
            latitude=31.2304,
            longitude=121.4737,
            address='Test address 1'
        )

        # Upload image
        image_file = create_test_image_file('test.png')
        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token
        )

        file_id = upload_data['data']['file_id']

        # Try to create post with route missing name
        response, data = api_client.post_json('/api/posts', {
            'title': 'Post with Route',
            'media_type': 'image',
            'media_files': [file_id],
            'corner_ids': [str(corner1_id)],
            'route': {
                'corner_ids': [str(corner1_id)]
            },
            'visibility': 'public'
        }, auth_token=token)

        assert response.status_code == 400

    def test_create_post_with_route_single_corner_fails(self, api_client, registered_user, corner_store):
        """Test that creating post with route containing only 1 corner fails."""
        # Create test corner with unique name
        import time
        unique_id = str(int(time.time()))
        corner_id = corner_store.create_corner(
            name=f"Single Corner Route {unique_id}",
            description="Test corner",
            latitude=31.2304,
            longitude=121.4737,
            address="Address"
        )

        # Get user token
        user_dict, token = registered_user

        # Upload media using correct method
        image_file = create_test_image_file('test.png')
        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token
        )

        file_id = upload_data['data']['file_id']

        # Try to create post with route containing only 1 corner
        response, data = api_client.post_json('/api/posts', {
            'title': 'Post with Single Corner Route',
            'media_type': 'image',
            'media_files': [file_id],
            'corner_ids': [str(corner_id)],
            'route': {
                'route_name': 'Single Corner Route',
                'corner_ids': [str(corner_id)]
            },
            'visibility': 'public'
        }, auth_token=token)

        assert response.status_code == 400
        assert 'error' in data
        assert 'at least 2 corners' in data['error'].lower()

    def test_create_post_with_route_empty_corners_fails(self, api_client, registered_user, corner_store):
        """Test that creating post with route containing no corners fails."""
        # Create test corner with unique name
        import time
        unique_id = str(int(time.time()) + 1)
        corner_id = corner_store.create_corner(
            name=f"Empty Corner Route {unique_id}",
            description="Test corner",
            latitude=31.2304,
            longitude=121.4737,
            address="Address"
        )

        # Get user token
        user_dict, token = registered_user

        # Upload media using correct method
        image_file = create_test_image_file('test.png')
        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token
        )

        file_id = upload_data['data']['file_id']

        # Try to create post with route containing no corners
        response, data = api_client.post_json('/api/posts', {
            'title': 'Post with Empty Route',
            'media_type': 'image',
            'media_files': [file_id],
            'corner_ids': [str(corner_id)],
            'route': {
                'route_name': 'Empty Route',
                'corner_ids': []
            },
            'visibility': 'public'
        }, auth_token=token)

        assert response.status_code == 400
        assert 'error' in data
        assert 'at least 2 corners' in data['error'].lower()
