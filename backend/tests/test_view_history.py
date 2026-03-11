"""Tests for view history tracking functionality."""
import pytest
from bson import ObjectId


@pytest.fixture(scope='function')
def cleanup_view_history_data(view_history_store, post_store, user_store):
    """Clean up test data before and after each view history test."""
    # Clean up before test
    try:
        view_history_store.collection.delete_many({})
        post_store.collection.delete_many({})
        user_store.collection.delete_many({'username': {'$regex': 'test', '$options': 'i'}})
    except Exception:
        pass
    
    yield
    
    # Clean up after test
    try:
        view_history_store.collection.delete_many({})
        post_store.collection.delete_many({})
        user_store.collection.delete_many({'username': {'$regex': 'test', '$options': 'i'}})
    except Exception:
        pass


class TestRecordPostView:
    """Test post view recording functionality."""

    def test_record_view_success(self, api_client, registered_user, post_store, cleanup_view_history_data):
        """Test successful view recording."""
        user_dict, token = registered_user
        user_id = ObjectId(user_dict['id'])

        # Create a post
        post_id = post_store.create_post(
            user_id=user_id,
            title="Test Post View",
            description="Test post",
            media_type="image",
            media_files=[],
            tags=["test"],
            visibility="public"
        )

        # Record view
        view_data = {
            'view_duration': 5000
        }

        response, data = api_client.post_json(
            f'/api/posts/{post_id}/view',
            data=view_data,
            auth_token=token
        )

        assert response.status_code == 201
        assert data['success'] is True
        assert 'view_id' in data['data']
        assert data['data']['post_id'] == str(post_id)
        assert data['data']['view_duration'] == 5000

    def test_record_view_without_auth_fails(self, api_client, post_store, registered_user, cleanup_view_history_data):
        """Test that recording view without authentication fails."""
        user_dict, token = registered_user
        user_id = ObjectId(user_dict['id'])

        # Create a post
        post_id = post_store.create_post(
            user_id=user_id,
            title="Test Post No Auth",
            description="Test post",
            media_type="image",
            media_files=[],
            tags=["test"],
            visibility="public"
        )

        # Record view without auth
        view_data = {'view_duration': 5000}

        response = api_client.client.post(
            f'/api/posts/{post_id}/view',
            json=view_data
        )

        assert response.status_code == 401

    def test_record_view_invalid_post_id(self, api_client, registered_user, cleanup_view_history_data):
        """Test that recording view for invalid post ID returns error."""
        user_dict, token = registered_user
        fake_id = str(ObjectId())

        view_data = {'view_duration': 5000}

        response, data = api_client.post_json(
            f'/api/posts/{fake_id}/view',
            data=view_data,
            auth_token=token
        )

        assert response.status_code == 404
        assert 'not found' in data['error'].lower()

    def test_record_view_negative_duration(self, api_client, registered_user, post_store, cleanup_view_history_data):
        """Test that negative duration returns error."""
        user_dict, token = registered_user
        user_id = ObjectId(user_dict['id'])

        # Create a post
        post_id = post_store.create_post(
            user_id=user_id,
            title="Test Post Negative",
            description="Test post",
            media_type="image",
            media_files=[],
            tags=["test"],
            visibility="public"
        )

        # Record view with negative duration
        view_data = {'view_duration': -1000}

        response, data = api_client.post_json(
            f'/api/posts/{post_id}/view',
            data=view_data,
            auth_token=token
        )

        assert response.status_code == 400
        assert 'non-negative' in data['error'].lower()

    def test_record_view_default_duration(self, api_client, registered_user, post_store, cleanup_view_history_data):
        """Test that default duration (0) is used when not provided."""
        user_dict, token = registered_user
        user_id = ObjectId(user_dict['id'])

        # Create a post
        post_id = post_store.create_post(
            user_id=user_id,
            title="Test Post Default",
            description="Test post",
            media_type="image",
            media_files=[],
            tags=["test"],
            visibility="public"
        )

        # Record view without duration
        response, data = api_client.post_json(
            f'/api/posts/{post_id}/view',
            data={},
            auth_token=token
        )

        assert response.status_code == 201
        assert data['data']['view_duration'] == 0


class TestGetUserViewHistory:
    """Test user view history retrieval functionality."""

    def test_get_view_history_success(self, api_client, registered_user, post_store, view_history_store, cleanup_view_history_data):
        """Test successful view history retrieval."""
        user_dict, token = registered_user
        user_id = ObjectId(user_dict['id'])

        # Create posts
        post1_id = post_store.create_post(
            user_id=user_id,
            title="Post 1 History",
            description="Post 1",
            media_type="image",
            media_files=[],
            tags=["test"],
            visibility="public"
        )

        post2_id = post_store.create_post(
            user_id=user_id,
            title="Post 2 History",
            description="Post 2",
            media_type="image",
            media_files=[],
            tags=["test"],
            visibility="public"
        )

        # Record views
        view_history_store.create_view(user_id, post1_id, view_duration=3000)
        view_history_store.create_view(user_id, post2_id, view_duration=5000)

        # Get view history
        response, data = api_client.get_json(
            f'/api/users/{user_dict["id"]}/view-history',
            auth_token=token
        )

        assert response.status_code == 200
        assert data['success'] is True
        assert 'view_history' in data['data']
        assert len(data['data']['view_history']) >= 2

    def test_get_view_history_access_denied(self, api_client, registered_user, cleanup_view_history_data):
        """Test that users can only view their own history."""
        user_dict, token = registered_user
        fake_id = str(ObjectId())

        # Try to view another user's history
        response, data = api_client.get_json(
            f'/api/users/{fake_id}/view-history',
            auth_token=token
        )

        assert response.status_code == 403
        assert 'access denied' in data['error'].lower()

    def test_get_view_history_pagination(self, api_client, registered_user, post_store, view_history_store, cleanup_view_history_data):
        """Test view history pagination."""
        user_dict, token = registered_user
        user_id = ObjectId(user_dict['id'])

        # Create posts
        for i in range(5):
            post_id = post_store.create_post(
                user_id=user_id,
                title=f"Post {i} History",
                description=f"Post {i}",
                media_type="image",
                media_files=[],
                tags=["test"],
                visibility="public"
            )
            view_history_store.create_view(user_id, post_id, view_duration=1000)

        # Get first page
        response, data = api_client.get_json(
            f'/api/users/{user_dict["id"]}/view-history',
            auth_token=token,
            query_params={'limit': 2, 'skip': 0}
        )

        assert response.status_code == 200
        assert len(data['data']['view_history']) == 2
        assert data['data']['total'] >= 2  # At least 2 results

    def test_get_view_history_min_duration_filter(self, api_client, registered_user, post_store, view_history_store, cleanup_view_history_data):
        """Test filtering by minimum view duration."""
        user_dict, token = registered_user
        user_id = ObjectId(user_dict['id'])

        # Create posts with different view durations
        post1_id = post_store.create_post(
            user_id=user_id,
            title="Post 1 Short",
            description="Post 1",
            media_type="image",
            media_files=[],
            tags=["test"],
            visibility="public"
        )

        post2_id = post_store.create_post(
            user_id=user_id,
            title="Post 2 Long",
            description="Post 2",
            media_type="image",
            media_files=[],
            tags=["test"],
            visibility="public"
        )

        # Record views with different durations
        view_history_store.create_view(user_id, post1_id, view_duration=500)
        view_history_store.create_view(user_id, post2_id, view_duration=2000)

        # Get history with min_duration=1000
        response, data = api_client.get_json(
            f'/api/users/{user_dict["id"]}/view-history',
            auth_token=token,
            query_params={'min_duration': 1000}
        )

        assert response.status_code == 200
        # Should only return the post with duration >= 1000
        for view in data['data']['view_history']:
            assert view['view_duration'] >= 1000


class TestTrendingPosts:
    """Test trending posts functionality."""

    def test_get_trending_posts_success(self, api_client, registered_user, post_store, view_history_store, cleanup_view_history_data):
        """Test successful trending posts retrieval."""
        user_dict, token = registered_user
        user_id = ObjectId(user_dict['id'])

        # Create posts
        post1_id = post_store.create_post(
            user_id=user_id,
            title="Popular Post Trending",
            description="Popular post",
            media_type="image",
            media_files=[],
            tags=["popular"],
            visibility="public"
        )

        post2_id = post_store.create_post(
            user_id=user_id,
            title="Less Popular Post Trending",
            description="Less popular post",
            media_type="image",
            media_files=[],
            tags=["test"],
            visibility="public"
        )

        # Record more views for post1
        for _ in range(5):
            view_history_store.create_view(user_id, post1_id, view_duration=1000)

        view_history_store.create_view(user_id, post2_id, view_duration=1000)

        # Get trending posts
        response, data = api_client.get_json(
            '/api/posts/trending-views',
            query_params={'time_range': '24h', 'limit': 10}
        )

        assert response.status_code == 200
        assert data['success'] is True
        assert 'posts' in data['data']
        assert len(data['data']['posts']) >= 2

        # Verify popular post has higher view count
        popular_post = next((p for p in data['data']['posts'] if p['title'] == "Popular Post Trending"), None)
        less_popular_post = next((p for p in data['data']['posts'] if p['title'] == "Less Popular Post Trending"), None)

        assert popular_post is not None
        assert less_popular_post is not None
        assert popular_post['view_count'] >= less_popular_post['view_count']

    def test_get_trending_posts_invalid_time_range(self, api_client, cleanup_view_history_data):
        """Test that invalid time range returns error."""
        response, data = api_client.get_json(
            '/api/posts/trending-views',
            query_params={'time_range': 'invalid'}
        )

        assert response.status_code == 400
        assert 'time_range' in data['error'].lower()

    def test_get_trending_posts_valid_time_ranges(self, api_client, cleanup_view_history_data):
        """Test all valid time ranges."""
        valid_ranges = ['1h', '6h', '24h', '7d']

        for time_range in valid_ranges:
            response, data = api_client.get_json(
                '/api/posts/trending-views',
                query_params={'time_range': time_range}
            )

            assert response.status_code == 200


class TestPostViewStats:
    """Test post view statistics functionality."""

    def test_get_post_view_stats_success(self, api_client, registered_user, post_store, view_history_store, cleanup_view_history_data):
        """Test successful post view statistics retrieval."""
        user_dict, token = registered_user
        user_id = ObjectId(user_dict['id'])

        # Create a post
        post_id = post_store.create_post(
            user_id=user_id,
            title="Test Post Stats",
            description="Test post",
            media_type="image",
            media_files=[],
            tags=["test"],
            visibility="public"
        )

        # Record views with different durations
        view_history_store.create_view(user_id, post_id, view_duration=2000)
        view_history_store.create_view(user_id, post_id, view_duration=3000)

        # Get view stats
        response, data = api_client.get_json(
            f'/api/posts/{post_id}/view-stats'
        )

        assert response.status_code == 200
        assert data['success'] is True
        assert data['data']['post_id'] == str(post_id)
        assert data['data']['total_views'] == 2
        assert data['data']['total_duration_ms'] == 5000
        assert data['data']['average_duration_ms'] == 2500

    def test_get_post_view_stats_invalid_post_id(self, api_client, cleanup_view_history_data):
        """Test that invalid post ID returns error."""
        fake_id = str(ObjectId())

        response, data = api_client.get_json(
            f'/api/posts/{fake_id}/view-stats'
        )

        assert response.status_code == 404
        assert 'not found' in data['error'].lower()

    def test_get_post_view_stats_no_views(self, api_client, registered_user, post_store, cleanup_view_history_data):
        """Test post stats with no views."""
        user_dict, token = registered_user
        user_id = ObjectId(user_dict['id'])

        # Create a post
        post_id = post_store.create_post(
            user_id=user_id,
            title="Test Post No Views",
            description="Test post",
            media_type="image",
            media_files=[],
            tags=["test"],
            visibility="public"
        )

        # Get view stats
        response, data = api_client.get_json(
            f'/api/posts/{post_id}/view-stats'
        )

        assert response.status_code == 200
        assert data['data']['total_views'] == 0
        assert data['data']['total_duration_ms'] == 0
        assert data['data']['average_duration_ms'] == 0
