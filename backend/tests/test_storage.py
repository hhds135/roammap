"""
Unit tests for the storage layer.

These tests require a MongoDB instance running on localhost:27017.
Use a test database that can be cleaned up after tests.

Run with: pytest tests/test_storage.py -v
"""

import pytest
from bson import ObjectId
from datetime import datetime, timedelta

from storage import (
    init_storage,
    MongoDBConnection,
    UserStore,
    CornerStore,
    PostStore,
    CommentStore,
    LikeStore,
    FavoriteStore,
    ViewHistoryStore,
    MediaStore,
    GeoStore,
)


# Test configuration
TEST_MONGO_URI = "mongodb://192.168.0.222:27017/"
TEST_DB_NAME = "conner_db_test"


@pytest.fixture(scope="module")
def db_connection():
    """Initialize database connection for tests."""
    init_storage(TEST_MONGO_URI, TEST_DB_NAME)
    yield
    # Cleanup: Drop test database after all tests
    conn = MongoDBConnection()
    if conn.is_connected():
        client = conn._client
        client.drop_database(TEST_DB_NAME)
        conn.close()


@pytest.fixture
def user_store(db_connection):
    """Get user store instance."""
    return UserStore()


@pytest.fixture
def corner_store(db_connection):
    """Get corner store instance."""
    return CornerStore()


@pytest.fixture
def post_store(db_connection):
    """Get post store instance."""
    return PostStore()


@pytest.fixture
def comment_store(db_connection):
    """Get comment store instance."""
    return CommentStore()


@pytest.fixture
def like_store(db_connection):
    """Get like store instance."""
    return LikeStore()


@pytest.fixture
def favorite_store(db_connection):
    """Get favorite store instance."""
    return FavoriteStore()


@pytest.fixture
def view_history_store(db_connection):
    """Get view history store instance."""
    return ViewHistoryStore()


@pytest.fixture
def media_store(db_connection):
    """Get media store instance."""
    return MediaStore()


@pytest.fixture
def geo_store(db_connection):
    """Get geo store instance."""
    return GeoStore()


class TestUserStore:
    """Tests for UserStore."""
    
    def test_create_user(self, user_store):
        """Test creating a user."""
        user_id = user_store.create_user(
            username="testuser1",
            password_hash="hashed_password_123"
        )
        assert isinstance(user_id, ObjectId)
        
        # Verify user was created
        user = user_store.get_user_by_id(user_id)
        assert user is not None
        assert user['username'] == "testuser1"
        assert 'created_at' in user
    
    def test_get_user_by_username(self, user_store):
        """Test getting user by username."""
        user = user_store.get_user_by_username("testuser1")
        assert user is not None
        assert user['username'] == "testuser1"
    
    def test_follow_unfollow(self, user_store):
        """Test follow and unfollow functionality."""
        # Create two users
        user1_id = user_store.create_user(
            username="follower_user",
            password_hash="pass1"
        )
        user2_id = user_store.create_user(
            username="followed_user",
            password_hash="pass2"
        )
        
        # Follow
        result = user_store.follow(user1_id, user2_id)
        assert result is True
        
        # Check is_following
        assert user_store.is_following(user1_id, user2_id) is True
        
        # Unfollow
        result = user_store.unfollow(user1_id, user2_id)
        assert result is True
        
        # Check is_following again
        assert user_store.is_following(user1_id, user2_id) is False
    
    def test_get_followers_and_following(self, user_store):
        """Test getting followers and following lists."""
        user1_id = user_store.create_user(
            username="user_a",
            password_hash="pass_a"
        )
        user2_id = user_store.create_user(
            username="user_b",
            password_hash="pass_b"
        )
        
        user_store.follow(user1_id, user2_id)
        
        followers = user_store.get_followers(user2_id)
        assert len(followers) == 1
        assert followers[0]['_id'] == user1_id
        
        following = user_store.get_following(user1_id)
        assert len(following) == 1
        assert following[0]['_id'] == user2_id


class TestCornerStore:
    """Tests for CornerStore."""
    
    def test_create_corner(self, corner_store):
        """Test creating a corner."""
        corner_id = corner_store.create_corner(
            name="Test Cafe",
            description="A nice test cafe",
            latitude=31.2304,
            longitude=121.4737,
            address="Test Street 123"
        )
        assert isinstance(corner_id, ObjectId)
        
        # Verify corner was created
        corner = corner_store.get_corner_by_id(corner_id)
        assert corner is not None
        assert corner['name'] == "Test Cafe"
        assert corner['location']['type'] == "Point"
    
    def test_get_corner_by_name(self, corner_store):
        """Test getting corner by name."""
        corner = corner_store.get_corner_by_name("Test Cafe")
        assert corner is not None
        assert corner['name'] == "Test Cafe"
    
    def test_nearby_corners(self, corner_store):
        """Test finding nearby corners."""
        # Create corners at different locations
        corner_store.create_corner(
            name="Nearby Cafe 1",
            description="Close by",
            latitude=31.2304,
            longitude=121.4737,
            address="Street 1"
        )
        corner_store.create_corner(
            name="Nearby Cafe 2",
            description="Also close",
            latitude=31.2310,
            longitude=121.4740,
            address="Street 2"
        )
        
        # Search nearby
        nearby = corner_store.get_nearby_corners(
            latitude=31.2304,
            longitude=121.4737,
            max_distance=1000
        )
        assert len(nearby) >= 1
    
    def test_search_corners_by_name(self, corner_store):
        """Test searching corners by name."""
        results = corner_store.search_corners_by_name("Cafe")
        assert len(results) >= 1


class TestPostStore:
    """Tests for PostStore."""
    
    def test_create_post(self, post_store, user_store, corner_store):
        """Test creating a post."""
        user = user_store.get_user_by_username("testuser1")
        corner = corner_store.get_corner_by_name("Test Cafe")
        
        post_id = post_store.create_post(
            user_id=user['_id'],
            title="Test Post",
            description="This is a test post",
            corner_ids=[corner['_id']],
            media_type="image",
            tags=["test", "demo"]
        )
        assert isinstance(post_id, ObjectId)
        
        # Verify post was created
        post = post_store.get_post_by_id(post_id)
        assert post is not None
        assert post['title'] == "Test Post"
        assert post['stats']['likes_count'] == 0
    
    def test_get_posts_by_user(self, post_store, user_store):
        """Test getting posts by user."""
        user = user_store.get_user_by_username("testuser1")
        posts = post_store.get_posts_by_user(user['_id'])
        assert len(posts) >= 1
    
    def test_increment_stat(self, post_store, user_store, corner_store):
        """Test incrementing post stats."""
        user = user_store.get_user_by_username("testuser1")
        corner = corner_store.get_corner_by_name("Test Cafe")
        
        post_id = post_store.create_post(
            user_id=user['_id'],
            title="Stat Test Post",
            description="Testing stats",
            corner_ids=[corner['_id']]
        )
        
        # Increment likes
        result = post_store.increment_stat(post_id, 'likes_count')
        assert result is True
        
        # Verify stat was updated
        post = post_store.get_post_by_id(post_id)
        assert post['stats']['likes_count'] == 1


class TestCommentStore:
    """Tests for CommentStore."""
    
    def test_create_comment(self, comment_store, post_store, user_store):
        """Test creating a comment."""
        user = user_store.get_user_by_username("testuser1")
        posts = post_store.get_posts_by_user(user['_id'])
        post_id = posts[0]['_id']
        
        comment_id = comment_store.create_comment(
            post_id=post_id,
            user_id=user['_id'],
            username=user['username'],
            content="This is a test comment"
        )
        assert isinstance(comment_id, ObjectId)
        
        # Verify comment was created
        comment = comment_store.get_comment_by_id(comment_id)
        assert comment is not None
        assert comment['content'] == "This is a test comment"
    
    def test_get_comments_by_post(self, comment_store, post_store, user_store):
        """Test getting comments by post."""
        user = user_store.get_user_by_username("testuser1")
        posts = post_store.get_posts_by_user(user['_id'])
        post_id = posts[0]['_id']
        
        comments = comment_store.get_comments_by_post(post_id)
        assert len(comments) >= 1


class TestLikeStore:
    """Tests for LikeStore."""
    
    def test_create_like(self, like_store, post_store, user_store):
        """Test creating a like."""
        user = user_store.get_user_by_username("testuser1")
        posts = post_store.get_posts_by_user(user['_id'])
        post_id = posts[0]['_id']
        
        like_id = like_store.create_like(user['_id'], post_id)
        assert isinstance(like_id, ObjectId)
        
        # Verify like was created
        assert like_store.is_liked(user['_id'], post_id) is True
    
    def test_toggle_like(self, like_store, post_store, user_store, corner_store):
        """Test toggling like status."""
        # Create a new user and post to avoid dependency on other tests
        user_id = user_store.create_user(
            username="toggle_test_user",
            password_hash="test_pass"
        )
        corner_id = corner_store.create_corner(
            name="Toggle Test Corner",
            description="For toggle test",
            latitude=40.0,
            longitude=-74.0,
            address="Test Addr"
        )
        post_id = post_store.create_post(
            user_id=user_id,
            title="Toggle Test Post",
            description="Test",
            corner_ids=[corner_id]
        )

        # Like
        result = like_store.toggle_like(user_id, post_id)
        assert result is True

        # Unlike
        result = like_store.toggle_like(user_id, post_id)
        assert result is False

        # Like again
        result = like_store.toggle_like(user_id, post_id)
        assert result is True


class TestFavoriteStore:
    """Tests for FavoriteStore."""
    
    def test_create_favorite(self, favorite_store, post_store, user_store):
        """Test creating a favorite."""
        user = user_store.get_user_by_username("testuser1")
        posts = post_store.get_posts_by_user(user['_id'])
        post_id = posts[0]['_id']
        
        fav_id = favorite_store.create_favorite(user['_id'], post_id)
        assert isinstance(fav_id, ObjectId)
        
        # Verify favorite was created
        assert favorite_store.is_favorite(user['_id'], post_id) is True
    
    def test_toggle_favorite(self, favorite_store, post_store, user_store, corner_store):
        """Test toggling favorite status."""
        # Create a new user and post to avoid dependency on other tests
        user_id = user_store.create_user(
            username="toggle_fav_test_user",
            password_hash="test_pass"
        )
        corner_id = corner_store.create_corner(
            name="Toggle Fav Test Corner",
            description="For toggle favorite test",
            latitude=40.0,
            longitude=-74.0,
            address="Test Addr"
        )
        post_id = post_store.create_post(
            user_id=user_id,
            title="Toggle Fav Test Post",
            description="Test",
            corner_ids=[corner_id]
        )

        # Favorite
        result = favorite_store.toggle_favorite(user_id, post_id)
        assert result is True

        # Unfavorite
        result = favorite_store.toggle_favorite(user_id, post_id)
        assert result is False

        # Favorite again
        result = favorite_store.toggle_favorite(user_id, post_id)
        assert result is True


class TestViewHistoryStore:
    """Tests for ViewHistoryStore."""
    
    def test_create_view(self, view_history_store, post_store, user_store):
        """Test creating a view record."""
        user = user_store.get_user_by_username("testuser1")
        posts = post_store.get_posts_by_user(user['_id'])
        post_id = posts[0]['_id']
        
        view_id = view_history_store.create_view(
            user_id=user['_id'],
            post_id=post_id,
            view_duration=5000
        )
        assert isinstance(view_id, ObjectId)
    
    def test_get_views_by_user(self, view_history_store, post_store, user_store):
        """Test getting views by user."""
        user = user_store.get_user_by_username("testuser1")
        
        views = view_history_store.get_views_by_user(user['_id'])
        assert len(views) >= 1


class TestMediaStore:
    """Tests for MediaStore."""
    
    def test_save_and_get_file(self, media_store):
        """Test saving and retrieving a file."""
        file_data = b"Test file content for media store"
        
        file_id = media_store.save_file(
            file_data=file_data,
            filename="test.txt",
            content_type="text/plain",
            metadata={'test': True}
        )
        assert isinstance(file_id, ObjectId)
        
        # Retrieve file
        retrieved_data = media_store.get_file_data(file_id)
        assert retrieved_data == file_data
    
    def test_delete_file(self, media_store):
        """Test deleting a file."""
        file_data = b"File to be deleted"
        
        file_id = media_store.save_file(
            file_data=file_data,
            filename="delete_test.txt",
            content_type="text/plain"
        )
        
        # Delete file
        result = media_store.delete_file(file_id)
        assert result is True
        
        # Verify file is deleted
        retrieved = media_store.get_file_data(file_id)
        assert retrieved is None


class TestGeoStore:
    """Tests for GeoStore."""
    
    def test_calculate_distance(self, geo_store):
        """Test distance calculation."""
        # Shanghai coordinates
        lat1, lng1 = 31.2304, 121.4737
        # Beijing coordinates
        lat2, lng2 = 39.9042, 116.4074
        
        distance = geo_store.calculate_distance(lat1, lng1, lat2, lng2)
        
        # Distance should be approximately 1068 km
        assert 1000000 < distance < 1200000  # meters
    
    def test_find_nearby(self, geo_store, corner_store):
        """Test finding nearby locations."""
        nearby = geo_store.find_nearby(
            latitude=31.2304,
            longitude=121.4737,
            max_distance=10000,
            limit=10
        )
        assert len(nearby) >= 1


class TestBaseStore:
    """Tests for BaseStore utilities."""
    
    def test_now_returns_utc(self):
        """Test that now() returns UTC datetime."""
        from storage.base_store import BaseStore
        
        now = BaseStore.now()
        assert now.tzinfo is not None
    
    def test_is_valid_object_id(self):
        """Test ObjectId validation."""
        from storage.base_store import BaseStore
        
        valid_id = str(ObjectId())
        invalid_id = "not_a_valid_id"
        
        assert BaseStore.is_valid_object_id(valid_id) is True
        assert BaseStore.is_valid_object_id(invalid_id) is False
    
    def test_to_object_id(self):
        """Test ObjectId conversion."""
        from storage.base_store import BaseStore
        
        valid_id = str(ObjectId())
        object_id = BaseStore.to_object_id(valid_id)
        
        assert isinstance(object_id, ObjectId)
        assert str(object_id) == valid_id
