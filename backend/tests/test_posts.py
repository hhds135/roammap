"""Tests for posts and media endpoints."""
import pytest
import io
from bson import ObjectId
from werkzeug.datastructures import FileStorage


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
