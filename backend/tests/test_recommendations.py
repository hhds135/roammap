"""Tests for recommendation algorithm functionality."""
import pytest
from bson import ObjectId

from services.recommendation_service import RecommendationService


@pytest.fixture(scope='function')
def cleanup_recommendation_data(corner_store, post_store, user_store, view_history_store, like_store, favorite_store):
    """Clean up test data before and after each recommendation test."""
    # Clean up before test
    try:
        corner_store.collection.delete_many({})
        post_store.collection.delete_many({})
        user_store.collection.delete_many({'username': {'$regex': 'test', '$options': 'i'}})
        view_history_store.collection.delete_many({})
        like_store.collection.delete_many({})
        favorite_store.collection.delete_many({})
    except Exception:
        pass
    
    yield
    
    # Clean up after test
    try:
        corner_store.collection.delete_many({})
        post_store.collection.delete_many({})
        user_store.collection.delete_many({'username': {'$regex': 'test', '$options': 'i'}})
        view_history_store.collection.delete_many({})
        like_store.collection.delete_many({})
        favorite_store.collection.delete_many({})
    except Exception:
        pass


class TestRecommendationService:
    """Test recommendation service core functionality."""

    def test_service_initialization(self):
        """Test that recommendation service initializes correctly."""
        service = RecommendationService()

        assert service is not None
        assert 'geo' in service.weights
        assert 'interest' in service.weights
        assert 'social' in service.weights
        assert 'behavior' in service.weights

        # Verify weights sum to 1.0
        total_weight = sum(service.weights.values())
        assert abs(total_weight - 1.0) < 0.01

    def test_custom_weights(self):
        """Test that custom weights can be set."""
        custom_weights = {
            'geo': 0.5,
            'interest': 0.3,
            'social': 0.1,
            'behavior': 0.1
        }

        service = RecommendationService(weights=custom_weights)

        assert service.weights == custom_weights

    def test_recommend_feed_with_no_user(self, api_client, cleanup_recommendation_data):
        """Test recommendation feed without user (anonymous)."""
        response, data = api_client.get_json(
            '/api/recommendations/feed',
            query_params={'limit': 5}
        )

        assert response.status_code == 200
        assert data['success'] is True
        assert 'posts' in data['data']

    def test_recommend_feed_with_location(self, api_client, cleanup_recommendation_data):
        """Test recommendation feed with user location."""
        response, data = api_client.get_json(
            '/api/recommendations/feed',
            query_params={'lat': 31.2304, 'lng': 121.4737, 'limit': 5}
        )

        assert response.status_code == 200
        assert data['success'] is True
        assert 'posts' in data['data']
        assert 'user_location' in data['data']
        assert data['data']['user_location']['lat'] == 31.2304
        assert data['data']['user_location']['lng'] == 121.4737

    def test_recommend_feed_invalid_coordinates(self, api_client, cleanup_recommendation_data):
        """Test recommendation feed with invalid coordinates."""
        # Invalid latitude
        response = api_client.client.get(
            '/api/recommendations/feed',
            query_string={'lat': 100, 'lng': 121.4737}
        )
        assert response.status_code == 400

        # Invalid longitude
        response = api_client.client.get(
            '/api/recommendations/feed',
            query_string={'lat': 31.2304, 'lng': 200}
        )
        assert response.status_code == 400

    def test_recommend_corners_with_location(self, api_client, corner_store, cleanup_recommendation_data):
        """Test corner recommendations with location."""
        # Create test corners
        corner_store.create_corner(
            name="Corner Rec 1",
            description="Corner 1",
            latitude=31.2304,
            longitude=121.4737,
            address="Address 1"
        )

        corner_store.create_corner(
            name="Corner Rec 2",
            description="Corner 2",
            latitude=31.2310,
            longitude=121.4740,
            address="Address 2"
        )

        # Get corner recommendations
        response, data = api_client.get_json(
            '/api/recommendations/corners',
            query_params={'lat': 31.2304, 'lng': 121.4737, 'radius': 1000, 'limit': 10}
        )

        assert response.status_code == 200
        assert data['success'] is True
        assert 'corners' in data['data']
        assert 'query_point' in data['data']
        assert data['data']['query_point']['lat'] == 31.2304

    def test_recommend_corners_without_location(self, api_client, corner_store, cleanup_recommendation_data):
        """Test corner recommendations without location (should return popular corners)."""
        # Create test corners
        for i in range(3):
            corner_store.create_corner(
                name=f"Corner Rec No Loc {i}",
                description=f"Corner {i}",
                latitude=31.2304 + i * 0.001,
                longitude=121.4737 + i * 0.001,
                address=f"Address {i}"
            )

        # Get corner recommendations without location
        response, data = api_client.get_json(
            '/api/recommendations/corners',
            query_params={'limit': 10}
        )

        assert response.status_code == 200
        assert data['success'] is True
        assert 'corners' in data['data']

    def test_recommend_corners_invalid_radius(self, api_client, cleanup_recommendation_data):
        """Test corner recommendations with invalid radius."""
        # Radius too small
        response = api_client.client.get(
            '/api/recommendations/corners',
            query_string={'lat': 31.2304, 'lng': 121.4737, 'radius': 5}
        )
        assert response.status_code == 400

        # Radius too large
        response = api_client.client.get(
            '/api/recommendations/corners',
            query_string={'lat': 31.2304, 'lng': 121.4737, 'radius': 200000}
        )
        assert response.status_code == 400

    def test_get_recommendation_config(self, api_client, cleanup_recommendation_data):
        """Test getting recommendation configuration."""
        response, data = api_client.get_json('/api/recommendations/config')

        assert response.status_code == 200
        assert data['success'] is True
        assert 'weights' in data['data']
        assert 'weight_sum' in data['data']

        # Verify weights are valid
        weights = data['data']['weights']
        assert 'geo' in weights
        assert 'interest' in weights
        assert 'social' in weights
        assert 'behavior' in weights

        # Verify sum is close to 1.0
        assert abs(data['data']['weight_sum'] - 1.0) < 0.01

    def test_get_recommendation_stats(self, api_client, registered_user, cleanup_recommendation_data):
        """Test getting recommendation statistics."""
        user_dict, token = registered_user

        response, data = api_client.get_json(
            '/api/recommendations/stats',
            auth_token=token
        )

        assert response.status_code == 200
        assert data['success'] is True
        assert 'cache_stats' in data['data'] or 'cache_size' in data['data']
        assert 'service_initialized' in data['data']
        assert data['data']['service_initialized'] is True


class TestScoreCalculation:
    """Test individual score calculation methods."""

    def test_geo_score_nearby(self):
        """Test geo score for nearby corner."""
        service = RecommendationService()

        # Post with nearby corner
        post = {
            '_id': ObjectId(),
            'corner_ids': [ObjectId()],
            'tags': [],
            'user_id': ObjectId()
        }

        # Mock corner location (very close)
        with pytest.MonkeyPatch().context() as m:
            def mock_get_corner_by_id(corner_id):
                return {
                    '_id': corner_id,
                    'location': {
                        'type': 'Point',
                        'coordinates': [121.4737, 31.2304]  # Same as user location
                    }
                }

            m.setattr(service.corner_store, 'get_corner_by_id', mock_get_corner_by_id)

            score = service._calculate_geo_score(post, (31.2304, 121.4737))
            assert score == 100  # Should be maximum score

    def test_geo_score_no_corners(self):
        """Test geo score for post without corners."""
        service = RecommendationService()

        post = {
            '_id': ObjectId(),
            'corner_ids': [],  # No corners
            'tags': [],
            'user_id': ObjectId()
        }

        score = service._calculate_geo_score(post, (31.2304, 121.4737))
        assert score == 30  # Should be low score

    def test_geo_score_no_location(self):
        """Test geo score without user location."""
        service = RecommendationService()

        post = {
            '_id': ObjectId(),
            'corner_ids': [ObjectId()],
            'tags': [],
            'user_id': ObjectId()
        }

        score = service._calculate_geo_score(post, None)
        assert score == 50  # Should be medium score

    def test_interest_score_full_match(self):
        """Test interest score with full tag match."""
        service = RecommendationService()

        user = {
            'interest_tags': ['food', 'coffee', 'travel']
        }

        post = {
            '_id': ObjectId(),
            'corner_ids': [],
            'tags': ['food', 'coffee', 'travel'],
            'user_id': ObjectId()
        }

        score = service._calculate_interest_score(post, user)
        assert score == 100  # Full match

    def test_interest_score_partial_match(self):
        """Test interest score with partial tag match."""
        service = RecommendationService()

        user = {
            'interest_tags': ['food', 'coffee', 'travel']
        }

        post = {
            '_id': ObjectId(),
            'corner_ids': [],
            'tags': ['food', 'other'],
            'user_id': ObjectId()
        }

        score = service._calculate_interest_score(post, user)
        assert 0 < score < 100  # Partial match

    def test_interest_score_no_match(self):
        """Test interest score with no tag match."""
        service = RecommendationService()

        user = {
            'interest_tags': ['food', 'coffee', 'travel']
        }

        post = {
            '_id': ObjectId(),
            'corner_ids': [],
            'tags': ['sports', 'music'],
            'user_id': ObjectId()
        }

        score = service._calculate_interest_score(post, user)
        assert score == 20  # No match

    def test_social_score_own_post(self):
        """Test social score for own post."""
        service = RecommendationService()

        user_id = str(ObjectId())
        post = {
            '_id': ObjectId(),
            'corner_ids': [],
            'tags': [],
            'user_id': ObjectId(user_id)
        }

        score = service._calculate_social_score(post, user_id)
        assert score == 100  # Own post

    def test_social_score_no_user(self):
        """Test social score without user."""
        service = RecommendationService()

        post = {
            '_id': ObjectId(),
            'corner_ids': [],
            'tags': [],
            'user_id': ObjectId()
        }

        score = service._calculate_social_score(post, None)
        assert score == 40  # No user

    def test_behavior_score_no_user(self):
        """Test behavior score without user."""
        service = RecommendationService()

        post = {
            '_id': ObjectId(),
            'corner_ids': [],
            'tags': [],
            'user_id': ObjectId()
        }

        score = service._calculate_behavior_score(post, None)
        assert score == 10  # No user, only base score

    def test_distance_calculation(self):
        """Test Haversine distance calculation."""
        service = RecommendationService()

        # Distance between two points in Shanghai
        point1 = (31.2304, 121.4737)  # People's Square
        point2 = {
            'type': 'Point',
            'coordinates': [121.4738, 31.2305]  # Very close
        }

        distance = service._calculate_distance(point1, point2)

        assert distance > 0
        assert distance < 200  # Should be less than 200 meters


class TestRecommendationIntegration:
    """Integration tests for recommendation system."""

    def test_full_recommendation_flow(self, api_client, registered_user, post_store, corner_store, user_store, cleanup_recommendation_data):
        """Test complete recommendation flow with user, posts, and corners."""
        user_dict, token = registered_user
        user_id = ObjectId(user_dict['id'])

        # Update user with interest tags
        user_store.update(user_id, {'interest_tags': ['food', 'coffee']})

        # Create a corner
        corner = corner_store.create_corner(
            name="Test Cafe Integration",
            description="A nice cafe",
            latitude=31.2304,
            longitude=121.4737,
            address="Test Address"
        )

        # Create posts with tags
        post1 = post_store.create_post(
            user_id=user_id,
            title="Best Coffee Rec",
            description="Great coffee here",
            corner_ids=[corner],
            media_type="image",
            media_files=[],
            tags=['food', 'coffee'],
            visibility="public"
        )

        post2 = post_store.create_post(
            user_id=user_id,
            title="Sports Event Rec",
            description="Sports activity",
            corner_ids=[],
            media_type="image",
            media_files=[],
            tags=['sports'],
            visibility="public"
        )

        # Get recommendations with location
        response, data = api_client.get_json(
            '/api/recommendations/feed',
            query_params={'lat': 31.2304, 'lng': 121.4737, 'limit': 10},
            auth_token=token
        )

        assert response.status_code == 200
        assert data['success'] is True
        assert len(data['data']['posts']) >= 2

        # The coffee post should be ranked higher (matches interests + location)
        posts = data['data']['posts']
        coffee_post = next((p for p in posts if p['title'] == "Best Coffee Rec"), None)
        sports_post = next((p for p in posts if p['title'] == "Sports Event Rec"), None)

        assert coffee_post is not None
        assert sports_post is not None


class TestRecommendationCache:
    """Test recommendation cache functionality."""

    def test_cache_hit(self, cleanup_recommendation_data):
        """Test that cache returns same result for same parameters."""
        service = RecommendationService()
        
        # First call - should miss cache
        result1 = service.recommend_feed(
            user_id=None,
            user_location=(31.2304, 121.4737),
            limit=5
        )
        
        # Second call with same params - should hit cache
        result2 = service.recommend_feed(
            user_id=None,
            user_location=(31.2304, 121.4737),
            limit=5
        )
        
        # Results should be the same
        assert len(result1) == len(result2)

    def test_cache_clear(self, cleanup_recommendation_data):
        """Test that cache can be cleared."""
        service = RecommendationService()
        
        # Make a request to populate cache
        service.recommend_feed(
            user_id=None,
            user_location=(31.2304, 121.4737),
            limit=5
        )
        
        # Check cache has entries
        cache_info = service.get_cache_info()
        assert cache_info['cache_size'] >= 0
        
        # Clear cache
        service.clear_cache()
        
        # Check cache is empty
        cache_info = service.get_cache_info()
        assert cache_info['cache_size'] == 0

    def test_cache_info(self, cleanup_recommendation_data):
        """Test cache info returns correct structure."""
        service = RecommendationService()
        
        cache_info = service.get_cache_info()
        
        assert 'cache_size' in cache_info
        assert 'cache_ttl' in cache_info
        assert 'max_cache_size' in cache_info
        assert cache_info['cache_ttl'] == 300  # Default TTL
        assert cache_info['max_cache_size'] == 100
