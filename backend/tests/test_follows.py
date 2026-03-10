"""Tests for follow system and feed endpoints."""
import pytest
import io
from bson import ObjectId
from werkzeug.datastructures import FileStorage

import uuid


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


# ==================== Follow Function Tests ====================

class TestFollowUser:
    """Test follow user functionality."""

    def test_follow_user_success(self, api_client, multiple_registered_users):
        """Test successful user follow."""
        user1, token1 = multiple_registered_users[0]
        user2, token2 = multiple_registered_users[1]

        # user1 follows user2
        response, data = api_client.post(
            f'/api/follows/{user2["id"]}',
            auth_token=token1
        )

        assert response.status_code == 200
        assert data['success'] is True
        assert data['data']['follower_id'] == user1['id']
        assert data['data']['following_id'] == user2['id']
        assert data['data']['is_following'] is True

    def test_follow_without_auth_fails(self, api_client):
        """Test that following without authentication fails."""
        fake_id = str(ObjectId())

        response = api_client.client.post(f'/api/follows/{fake_id}')

        assert response.status_code == 401

    def test_follow_yourself_fails(self, api_client, registered_user):
        """Test that following yourself fails."""
        user_dict, token = registered_user

        response, data = api_client.post(
            f'/api/follows/{user_dict["id"]}',
            auth_token=token
        )

        assert response.status_code == 400
        assert 'Cannot follow yourself' in data['error']

    def test_follow_nonexistent_user_fails(self, api_client, registered_user):
        """Test that following a non-existent user fails."""
        user_dict, token = registered_user
        fake_id = str(ObjectId())

        response, data = api_client.post(
            f'/api/follows/{fake_id}',
            auth_token=token
        )

        assert response.status_code == 404
        assert 'User not found' in data['error']

    def test_duplicate_follow_is_idempotent(self, api_client, multiple_registered_users):
        """Test that following the same user twice is idempotent."""
        user1, token1 = multiple_registered_users[0]
        user2, token2 = multiple_registered_users[1]

        # First follow
        api_client.post(
            f'/api/follows/{user2["id"]}',
            auth_token=token1
        )

        # Second follow (should still succeed)
        response, data = api_client.post(
            f'/api/follows/{user2["id"]}',
            auth_token=token1
        )

        assert response.status_code == 200
        assert 'Already following' in data['message']


class TestUnfollowUser:
    """Test unfollow user functionality."""

    def test_unfollow_user_success(self, api_client, multiple_registered_users):
        """Test successful user unfollow."""
        user1, token1 = multiple_registered_users[0]
        user2, token2 = multiple_registered_users[1]

        # First follow
        api_client.post(
            f'/api/follows/{user2["id"]}',
            auth_token=token1
        )

        # Then unfollow
        response, data = api_client.delete(
            f'/api/follows/{user2["id"]}',
            auth_token=token1
        )

        assert response.status_code == 200
        assert data['success'] is True
        assert data['data']['is_following'] is False

    def test_unfollow_without_auth_fails(self, api_client):
        """Test that unfollowing without authentication fails."""
        fake_id = str(ObjectId())

        response = api_client.client.delete(f'/api/follows/{fake_id}')

        assert response.status_code == 401

    def test_unfollow_nonexistent_user_fails(self, api_client, registered_user):
        """Test that unfollowing a non-existent user fails."""
        user_dict, token = registered_user
        fake_id = str(ObjectId())

        response, data = api_client.delete(
            f'/api/follows/{fake_id}',
            auth_token=token
        )

        assert response.status_code == 404
        assert 'User not found' in data['error']

    def test_unfollow_already_not_following(self, api_client, multiple_registered_users):
        """Test that unfollowing when not following still succeeds (idempotent)."""
        user1, token1 = multiple_registered_users[0]
        user2, token2 = multiple_registered_users[1]

        # Unfollow without following first
        response, data = api_client.delete(
            f'/api/follows/{user2["id"]}',
            auth_token=token1
        )

        assert response.status_code == 200


class TestGetFollowingList:
    """Test get following list functionality."""

    def test_get_following_list_empty(self, api_client, registered_user):
        """Test getting following list when user follows nobody."""
        user_dict, token = registered_user

        response, data = api_client.get_json(
            f'/api/users/{user_dict["id"]}/following',
            auth_token=token
        )

        assert response.status_code == 200
        assert data['success'] is True
        assert len(data['data']['following']) == 0
        assert data['data']['total'] == 0

    def test_get_following_list_success(self, api_client, multiple_registered_users):
        """Test getting following list with users."""
        user1, token1 = multiple_registered_users[0]
        user2, token2 = multiple_registered_users[1]
        user3, token3 = multiple_registered_users[2]

        # user1 follows user2 and user3
        api_client.post(
            f'/api/follows/{user2["id"]}',
            auth_token=token1
        )
        api_client.post(
            f'/api/follows/{user3["id"]}',
            auth_token=token1
        )

        # Get following list
        response, data = api_client.get_json(
            f'/api/users/{user1["id"]}/following',
            auth_token=token1
        )

        assert response.status_code == 200
        assert data['success'] is True
        assert len(data['data']['following']) == 2
        assert data['data']['total'] == 2

    def test_get_following_list_pagination(self, api_client, multiple_registered_users):
        """Test following list pagination."""
        user1, token1 = multiple_registered_users[0]
        user2, token2 = multiple_registered_users[1]
        user3, token3 = multiple_registered_users[2]

        # user1 follows user2 and user3
        api_client.post(
            f'/api/follows/{user2["id"]}',
            auth_token=token1
        )
        api_client.post(
            f'/api/follows/{user3["id"]}',
            auth_token=token1
        )

        # Get first page with limit=1
        response, data = api_client.get_json(
            f'/api/users/{user1["id"]}/following',
            auth_token=token1,
            query_params={'limit': 1, 'skip': 0}
        )

        assert response.status_code == 200
        assert len(data['data']['following']) == 1
        assert data['data']['limit'] == 1

    def test_get_following_list_nonexistent_user(self, api_client):
        """Test getting following list for non-existent user."""
        fake_id = str(ObjectId())

        response = api_client.client.get(f'/api/users/{fake_id}/following')

        assert response.status_code == 404


class TestGetFollowersList:
    """Test get followers list functionality."""

    def test_get_followers_list_empty(self, api_client, registered_user):
        """Test getting followers list when user has no followers."""
        user_dict, token = registered_user

        response, data = api_client.get_json(
            f'/api/users/{user_dict["id"]}/followers',
            auth_token=token
        )

        assert response.status_code == 200
        assert data['success'] is True
        assert len(data['data']['followers']) == 0
        assert data['data']['total'] == 0

    def test_get_followers_list_success(self, api_client, multiple_registered_users):
        """Test getting followers list with users."""
        user1, token1 = multiple_registered_users[0]
        user2, token2 = multiple_registered_users[1]
        user3, token3 = multiple_registered_users[2]

        # user2 and user3 follow user1
        api_client.post(
            f'/api/follows/{user1["id"]}',
            auth_token=token2
        )
        api_client.post(
            f'/api/follows/{user1["id"]}',
            auth_token=token3
        )

        # Get followers list
        response, data = api_client.get_json(
            f'/api/users/{user1["id"]}/followers',
            auth_token=token1
        )

        assert response.status_code == 200
        assert data['success'] is True
        assert len(data['data']['followers']) == 2
        assert data['data']['total'] == 2

    def test_get_followers_list_pagination(self, api_client, multiple_registered_users):
        """Test followers list pagination."""
        user1, token1 = multiple_registered_users[0]
        user2, token2 = multiple_registered_users[1]
        user3, token3 = multiple_registered_users[2]

        # user2 and user3 follow user1
        api_client.post(
            f'/api/follows/{user1["id"]}',
            auth_token=token2
        )
        api_client.post(
            f'/api/follows/{user1["id"]}',
            auth_token=token3
        )

        # Get first page with limit=1
        response, data = api_client.get_json(
            f'/api/users/{user1["id"]}/followers',
            auth_token=token1,
            query_params={'limit': 1, 'skip': 0}
        )

        assert response.status_code == 200
        assert len(data['data']['followers']) == 1


class TestFollowStatus:
    """Test follow status functionality."""

    def test_get_follow_status_not_logged_in(self, api_client, multiple_registered_users):
        """Test getting follow status when not logged in."""
        user2, token2 = multiple_registered_users[1]

        response, data = api_client.get_json(
            f'/api/follows/{user2["id"]}/status'
        )

        assert response.status_code == 200
        assert data['success'] is True
        assert data['data']['is_following'] is False
        assert data['data']['is_followed_by'] is False

    def test_get_follow_status_following(self, api_client, multiple_registered_users):
        """Test getting follow status when following."""
        user1, token1 = multiple_registered_users[0]
        user2, token2 = multiple_registered_users[1]

        # user1 follows user2
        api_client.post(
            f'/api/follows/{user2["id"]}',
            auth_token=token1
        )

        # Check status
        response, data = api_client.get_json(
            f'/api/follows/{user2["id"]}/status',
            auth_token=token1
        )

        assert response.status_code == 200
        assert data['data']['is_following'] is True
        assert data['data']['is_followed_by'] is False

    def test_get_follow_status_mutual_following(self, api_client, multiple_registered_users):
        """Test getting follow status when mutually following."""
        user1, token1 = multiple_registered_users[0]
        user2, token2 = multiple_registered_users[1]

        # user1 follows user2
        api_client.post(
            f'/api/follows/{user2["id"]}',
            auth_token=token1
        )

        # user2 follows user1
        api_client.post(
            f'/api/follows/{user1["id"]}',
            auth_token=token2
        )

        # Check status from user1's perspective
        response, data = api_client.get_json(
            f'/api/follows/{user2["id"]}/status',
            auth_token=token1
        )

        assert response.status_code == 200
        assert data['data']['is_following'] is True
        assert data['data']['is_followed_by'] is True


# ==================== Feed Tests ====================

class TestFollowingFeed:
    """Test following feed functionality."""

    def test_get_following_feed_empty(self, api_client, registered_user):
        """Test getting following feed when following nobody."""
        user_dict, token = registered_user

        response, data = api_client.get_json(
            '/api/feed/following',
            auth_token=token
        )

        assert response.status_code == 200
        assert data['success'] is True
        assert len(data['data']['posts']) == 0

    def test_get_following_feed_success(self, api_client, multiple_registered_users):
        """Test getting following feed with posts."""
        user1, token1 = multiple_registered_users[0]
        user2, token2 = multiple_registered_users[1]

        # user1 follows user2
        api_client.post(
            f'/api/follows/{user2["id"]}',
            auth_token=token1
        )

        # user2 creates a post
        image_file = create_test_image_file('test.png')
        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token2
        )

        file_id = upload_data['data']['file_id']

        api_client.post_json('/api/posts', {
            'title': 'Test Post',
            'media_type': 'image',
            'media_files': [file_id],
            'visibility': 'public'
        }, auth_token=token2)

        # user1 gets following feed
        response, data = api_client.get_json(
            '/api/feed/following',
            auth_token=token1
        )

        assert response.status_code == 200
        assert data['success'] is True
        assert len(data['data']['posts']) == 1

    def test_get_following_feed_exclude_own_posts(self, api_client, multiple_registered_users):
        """Test getting following feed excluding own posts."""
        user1, token1 = multiple_registered_users[0]
        user2, token2 = multiple_registered_users[1]

        # user1 follows user2
        api_client.post(
            f'/api/follows/{user2["id"]}',
            auth_token=token1
        )

        # user1 creates a post
        image_file = create_test_image_file('test.png')
        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token1
        )

        file_id = upload_data['data']['file_id']

        api_client.post_json('/api/posts', {
            'title': 'My Post',
            'media_type': 'image',
            'media_files': [file_id],
            'visibility': 'public'
        }, auth_token=token1)

        # user1 gets following feed excluding own posts
        response, data = api_client.get_json(
            '/api/feed/following',
            auth_token=token1,
            query_params={'include_own': 'false'}
        )

        assert response.status_code == 200
        assert len(data['data']['posts']) == 0

    def test_get_following_feed_pagination(self, api_client, multiple_registered_users):
        """Test following feed pagination."""
        user1, token1 = multiple_registered_users[0]
        user2, token2 = multiple_registered_users[1]

        # user1 follows user2
        api_client.post(
            f'/api/follows/{user2["id"]}',
            auth_token=token1
        )

        # user2 creates multiple posts
        image_file = create_test_image_file('test.png')
        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token2
        )

        file_id = upload_data['data']['file_id']

        for i in range(3):
            api_client.post_json('/api/posts', {
                'title': f'Test Post {i}',
                'media_type': 'image',
                'media_files': [file_id],
                'visibility': 'public'
            }, auth_token=token2)

        # Get first page
        response, data = api_client.get_json(
            '/api/feed/following',
            auth_token=token1,
            query_params={'limit': 2, 'skip': 0}
        )

        assert response.status_code == 200
        assert len(data['data']['posts']) == 2
        assert data['data']['limit'] == 2

    def test_get_following_feed_without_auth_fails(self, api_client):
        """Test that getting following feed without auth fails."""
        response = api_client.client.get('/api/feed/following')

        assert response.status_code == 401


class TestPublicFeed:
    """Test public feed functionality."""

    def test_get_public_feed_success(self, api_client, registered_user):
        """Test getting public feed."""
        user_dict, token = registered_user

        # Create a public post
        image_file = create_test_image_file('test.png')
        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token
        )

        file_id = upload_data['data']['file_id']

        api_client.post_json('/api/posts', {
            'title': 'Public Post',
            'media_type': 'image',
            'media_files': [file_id],
            'visibility': 'public'
        }, auth_token=token)

        # Get public feed
        response, data = api_client.get_json('/api/feed/public')

        assert response.status_code == 200
        assert data['success'] is True
        assert len(data['data']['posts']) >= 1

    def test_get_public_feed_without_auth(self, api_client, registered_user):
        """Test that public feed can be accessed without auth."""
        user_dict, token = registered_user

        # Create a public post
        image_file = create_test_image_file('test.png')
        _, upload_data = api_client.post_multipart(
            '/api/media/upload',
            data={'media_type': 'image'},
            files={'file': image_file},
            auth_token=token
        )

        file_id = upload_data['data']['file_id']

        api_client.post_json('/api/posts', {
            'title': 'Public Post',
            'media_type': 'image',
            'media_files': [file_id],
            'visibility': 'public'
        }, auth_token=token)

        # Get public feed without auth
        response, data = api_client.get_json('/api/feed/public')

        assert response.status_code == 200


class TestFeedStatus:
    """Test feed status functionality."""

    def test_get_feed_status_success(self, api_client, multiple_registered_users):
        """Test getting feed status."""
        user1, token1 = multiple_registered_users[0]
        user2, token2 = multiple_registered_users[1]

        # user1 follows user2
        api_client.post(
            f'/api/follows/{user2["id"]}',
            auth_token=token1
        )

        # Get feed status
        response, data = api_client.get_json(
            '/api/feed/status',
            auth_token=token1
        )

        assert response.status_code == 200
        assert data['success'] is True
        assert data['data']['following_count'] == 1

    def test_get_feed_status_without_auth_fails(self, api_client):
        """Test that getting feed status without auth fails."""
        response = api_client.client.get('/api/feed/status')

        assert response.status_code == 401