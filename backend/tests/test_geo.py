"""Tests for geospatial query functionality."""
import pytest
from bson import ObjectId


@pytest.fixture(scope='function')
def cleanup_geo_test_data(corner_store, post_store, user_store):
    """Clean up test data before and after each geo test."""
    # Clean up before test
    try:
        corner_store.collection.delete_many({})
        post_store.collection.delete_many({})
        user_store.collection.delete_many({'username': {'$regex': 'test', '$options': 'i'}})
    except Exception:
        pass
    
    yield
    
    # Clean up after test
    try:
        corner_store.collection.delete_many({})
        post_store.collection.delete_many({})
        user_store.collection.delete_many({'username': {'$regex': 'test', '$options': 'i'}})
    except Exception:
        pass


class TestNearbyCorners:
    """Test nearby corners query functionality."""

    def test_get_nearby_corners_success(self, api_client, corner_store, cleanup_geo_test_data):
        """Test successful nearby corners query."""
        # Create test corners at known locations
        corner1 = corner_store.create_corner(
            name="Test Corner 1 Unique",
            description="Test corner 1",
            latitude=31.2304,
            longitude=121.4737,
            address="Test Address 1"
        )

        corner2 = corner_store.create_corner(
            name="Test Corner 2 Unique",
            description="Test corner 2",
            latitude=31.2310,  # Very close to corner1
            longitude=121.4740,
            address="Test Address 2"
        )

        corner3 = corner_store.create_corner(
            name="Test Corner 3 Unique",
            description="Test corner 3",
            latitude=31.2500,  # Far from corner1
            longitude=121.5000,
            address="Test Address 3"
        )

        # Query nearby corners
        response, data = api_client.get_json(
            '/api/corners/nearby',
            query_params={'lat': 31.2304, 'lng': 121.4737, 'radius': 1000, 'limit': 10}
        )

        assert response.status_code == 200
        assert data['success'] is True
        assert 'corners' in data['data']
        assert len(data['data']['corners']) >= 2  # At least corner1 and corner2

        # Verify corners are sorted by distance
        corners = data['data']['corners']
        assert corners[0]['name'] == "Test Corner 1 Unique"  # Should be closest (distance = 0)

    def test_get_nearby_corners_missing_params(self, api_client, cleanup_geo_test_data):
        """Test that missing required parameters returns error."""
        # Missing lat
        response, data = api_client.get_json(
            '/api/corners/nearby',
            query_params={'lng': 121.4737}
        )
        assert response.status_code == 400
        assert 'lat' in data['error'].lower()

        # Missing lng
        response, data = api_client.get_json(
            '/api/corners/nearby',
            query_params={'lat': 31.2304}
        )
        assert response.status_code == 400
        assert 'lng' in data['error'].lower()

    def test_get_nearby_corners_invalid_coordinates(self, api_client, cleanup_geo_test_data):
        """Test that invalid coordinates return error."""
        # Invalid latitude (> 90)
        response = api_client.client.get(
            '/api/corners/nearby',
            query_string={'lat': 100, 'lng': 121.4737}
        )
        assert response.status_code == 400
        data = response.get_json()
        assert 'latitude' in data['error'].lower()

        # Invalid longitude (> 180)
        response = api_client.client.get(
            '/api/corners/nearby',
            query_string={'lat': 31.2304, 'lng': 200}
        )
        assert response.status_code == 400
        data = response.get_json()
        assert 'longitude' in data['error'].lower()

    def test_get_nearby_corners_invalid_radius(self, api_client, cleanup_geo_test_data):
        """Test that invalid radius returns error."""
        # Radius too small
        response = api_client.client.get(
            '/api/corners/nearby',
            query_string={'lat': 31.2304, 'lng': 121.4737, 'radius': 5}
        )
        assert response.status_code == 400
        data = response.get_json()
        assert 'radius' in data['error'].lower()

        # Radius too large
        response = api_client.client.get(
            '/api/corners/nearby',
            query_string={'lat': 31.2304, 'lng': 121.4737, 'radius': 200000}
        )
        assert response.status_code == 400
        data = response.get_json()
        assert 'radius' in data['error'].lower()

    def test_get_nearby_corners_distance_calculation(self, api_client, corner_store, cleanup_geo_test_data):
        """Test that distance is calculated correctly."""
        # Create a corner at known location
        corner = corner_store.create_corner(
            name="Test Corner Distance",
            description="Test corner",
            latitude=31.2304,
            longitude=121.4737,
            address="Test Address"
        )

        # Query from same location (should have distance 0)
        response, data = api_client.get_json(
            '/api/corners/nearby',
            query_params={'lat': 31.2304, 'lng': 121.4737, 'radius': 1000}
        )

        assert response.status_code == 200
        corners = data['data']['corners']
        assert len(corners) >= 1

        # Find the corner we created
        test_corner = next((c for c in corners if c['name'] == "Test Corner Distance"), None)
        assert test_corner is not None
        assert test_corner['distance'] == 0.0


class TestCornerPosts:
    """Test corner posts query functionality."""

    def test_get_corner_posts_success(self, api_client, corner_store, registered_user, post_store, cleanup_geo_test_data):
        """Test successful corner posts query."""
        # Create a corner
        corner = corner_store.create_corner(
            name="Test Corner Posts",
            description="Test corner",
            latitude=31.2304,
            longitude=121.4737,
            address="Test Address"
        )

        # Create posts referencing this corner
        user_dict, token = registered_user
        user_id = ObjectId(user_dict['id'])

        post1 = post_store.create_post(
            user_id=user_id,
            title="Test Post 1",
            description="Test post 1",
            corner_ids=[corner],
            media_type="image",
            media_files=[],
            tags=["test"],
            visibility="public"
        )

        post2 = post_store.create_post(
            user_id=user_id,
            title="Test Post 2",
            description="Test post 2",
            corner_ids=[corner],
            media_type="image",
            media_files=[],
            tags=["test"],
            visibility="public"
        )

        # Query posts for this corner
        response, data = api_client.get_json(
            f'/api/corners/{corner}/posts'
        )

        assert response.status_code == 200
        assert data['success'] is True
        assert 'posts' in data['data']
        assert len(data['data']['posts']) >= 2

    def test_get_corner_posts_invalid_corner_id(self, api_client, cleanup_geo_test_data):
        """Test that invalid corner ID returns error."""
        fake_id = str(ObjectId())
        response, data = api_client.get_json(
            f'/api/corners/{fake_id}/posts'
        )

        assert response.status_code == 404
        assert 'not found' in data['error'].lower()

    def test_get_corner_posts_pagination(self, api_client, corner_store, registered_user, post_store, cleanup_geo_test_data):
        """Test corner posts pagination."""
        # Create a corner
        corner = corner_store.create_corner(
            name="Test Corner Pagination",
            description="Test corner",
            latitude=31.2304,
            longitude=121.4737,
            address="Test Address"
        )

        # Create multiple posts
        user_dict, token = registered_user
        user_id = ObjectId(user_dict['id'])

        for i in range(5):
            post_store.create_post(
                user_id=user_id,
                title=f"Test Post {i}",
                description=f"Test post {i}",
                corner_ids=[corner],
                media_type="image",
                media_files=[],
                tags=["test"],
                visibility="public"
            )

        # Query with pagination
        response, data = api_client.get_json(
            f'/api/corners/{corner}/posts',
            query_params={'limit': 2, 'skip': 0}
        )

        assert response.status_code == 200
        assert len(data['data']['posts']) == 2
        assert data['data']['total'] >= 5

        # Get next page
        response, data = api_client.get_json(
            f'/api/corners/{corner}/posts',
            query_params={'limit': 2, 'skip': 2}
        )

        assert response.status_code == 200
        assert len(data['data']['posts']) == 2


class TestCornerCRUD:
    """Test corner CRUD operations with MongoDB storage."""

    def test_create_corner_success(self, api_client, registered_user, cleanup_geo_test_data):
        """Test successful corner creation."""
        user_dict, token = registered_user
        
        corner_data = {
            'name': 'New Test Corner Unique',
            'description': 'A test corner',
            'latitude': 31.2304,
            'longitude': 121.4737,
            'address': 'Test Address',
            'tags': ['test', 'location']
        }

        response, data = api_client.post_json(
            '/api/corners',
            data=corner_data,
            auth_token=token
        )

        assert response.status_code == 201
        assert data['success'] is True
        assert data['data']['name'] == 'New Test Corner Unique'

    def test_get_corner_detail_success(self, api_client, corner_store, cleanup_geo_test_data):
        """Test successful corner detail retrieval."""
        corner_id = corner_store.create_corner(
            name="Test Corner Detail",
            description="Test corner",
            latitude=31.2304,
            longitude=121.4737,
            address="Test Address"
        )

        response, data = api_client.get_json(f'/api/corners/{corner_id}')

        assert response.status_code == 200
        assert data['success'] is True
        assert data['data']['name'] == "Test Corner Detail"

    def test_update_corner_success(self, api_client, corner_store, registered_user, cleanup_geo_test_data):
        """Test successful corner update."""
        corner_id = corner_store.create_corner(
            name="Test Corner Update",
            description="Test corner",
            latitude=31.2304,
            longitude=121.4737,
            address="Test Address"
        )

        user_dict, token = registered_user
        
        update_data = {
            'name': 'Updated Corner Name',
            'description': 'Updated description'
        }

        response, data = api_client.put_json(
            f'/api/corners/{corner_id}',
            data=update_data,
            auth_token=token
        )

        assert response.status_code == 200
        assert data['success'] is True
        assert data['data']['name'] == 'Updated Corner Name'

    def test_delete_corner_success(self, api_client, corner_store, registered_user, cleanup_geo_test_data):
        """Test successful corner deletion."""
        corner_id = corner_store.create_corner(
            name="Test Corner Delete",
            description="Test corner",
            latitude=31.2304,
            longitude=121.4737,
            address="Test Address"
        )

        user_dict, token = registered_user
        
        response, data = api_client.delete(
            f'/api/corners/{corner_id}',
            auth_token=token
        )

        assert response.status_code == 200
        assert data['success'] is True

    def test_get_corners_list_success(self, api_client, corner_store, cleanup_geo_test_data):
        """Test successful corners list retrieval."""
        # Create test corners
        corner_store.create_corner(
            name="Corner List 1",
            description="Test corner 1",
            latitude=31.2304,
            longitude=121.4737,
            address="Address 1"
        )

        corner_store.create_corner(
            name="Corner List 2",
            description="Test corner 2",
            latitude=31.2310,
            longitude=121.4740,
            address="Address 2"
        )

        response, data = api_client.get_json('/api/corners')

        assert response.status_code == 200
        assert data['success'] is True
        assert 'corners' in data['data']
        assert len(data['data']['corners']) >= 2

    def test_get_corners_list_total_ignores_limit(self, api_client, registered_user, cleanup_geo_test_data):
        """Test corners list total still reflects all matching corners when limit is applied."""
        user_dict, token = registered_user
        user_id = user_dict['id']

        for idx in range(2):
            response, data = api_client.post_json(
                '/api/corners',
                data={
                    'name': f'Profile Corner {idx} Unique',
                    'description': f'Profile corner {idx}',
                    'latitude': 31.2304 + (idx * 0.001),
                    'longitude': 121.4737 + (idx * 0.001),
                    'address': f'Address {idx}'
                },
                auth_token=token
            )
            assert response.status_code == 201

        response, data = api_client.get_json(
            '/api/corners',
            query_params={'user_id': user_id, 'limit': 1}
        )

        assert response.status_code == 200
        assert data['success'] is True
        assert len(data['data']['corners']) == 1
        assert data['data']['total'] >= 2


class TestCornersAggregateAPI:
    """Test corners aggregate API functionality."""

    def test_corners_aggregate_success(self, api_client, corner_store, post_store, registered_user, cleanup_geo_test_data):
        """Test successful corners aggregate query."""
        # Create test corners
        corner1_id = corner_store.create_corner(
            name="Aggregate Corner 1",
            description="Test corner for aggregate",
            latitude=31.2304,
            longitude=121.4737,
            address="Address 1"
        )

        corner2_id = corner_store.create_corner(
            name="Aggregate Corner 2",
            description="Test corner for aggregate",
            latitude=31.2310,
            longitude=121.4740,
            address="Address 2"
        )

        # Create test user and post
        user_dict, token = registered_user
        user_id = user_dict['id']

        # Create a post that references both corners
        from storage.media_store import MediaStore
        media_store = MediaStore(bucket_name="media")
        
        # Upload a test image
        import io
        image_data = b"test image content"
        file_id = media_store.save_file(
            file_data=image_data,
            filename="test.jpg",
            content_type="image/jpeg",
            metadata={
                'media_type': 'image',
                'user_id': user_id
            }
        )

        # Create post referencing corners
        post_id = post_store.create_post(
            user_id=ObjectId(user_id),
            title="Test Post for Aggregate",
            description="Test post",
            corner_ids=[corner1_id, corner2_id],
            media_type="image",
            media_files=[file_id],
            tags=["test"],
            visibility="public"
        )

        # Test aggregate API
        response, data = api_client.get_json(
            f'/api/corners/aggregate?corner_ids={corner1_id},{corner2_id}'
        )

        assert response.status_code == 200
        assert data['success'] is True
        assert 'corners' in data['data']
        assert len(data['data']['corners']) == 2

        # Check that both corners have post_count >= 1
        for corner_data in data['data']['corners']:
            assert 'post_count' in corner_data
            assert corner_data['post_count'] >= 1
            assert 'total_likes' in corner_data
            assert 'total_comments' in corner_data
            assert 'recent_posts' in corner_data

    def test_corners_aggregate_missing_parameter(self, api_client):
        """Test corners aggregate API with missing corner_ids parameter."""
        response, data = api_client.get_json('/api/corners/aggregate')

        assert response.status_code == 400
        assert 'error' in data

    def test_corners_aggregate_empty_corner_ids(self, api_client):
        """Test corners aggregate API with empty corner_ids."""
        response, data = api_client.get_json('/api/corners/aggregate?corner_ids=')

        assert response.status_code == 400
        assert 'error' in data

    def test_corners_aggregate_single_corner(self, api_client, corner_store, cleanup_geo_test_data):
        """Test corners aggregate API with single corner."""
        corner_id = corner_store.create_corner(
            name="Single Aggregate Corner",
            description="Test corner",
            latitude=31.2304,
            longitude=121.4737,
            address="Address"
        )

        response, data = api_client.get_json(f'/api/corners/aggregate?corner_ids={corner_id}')

        assert response.status_code == 200
        assert data['success'] is True
        assert len(data['data']['corners']) == 1
        assert data['data']['corners'][0]['corner_id'] == str(corner_id)

    def test_corners_aggregate_invalid_corner_id(self, api_client):
        """Test corners aggregate API with invalid corner ID."""
        invalid_id = "invalid_corner_id_12345"
        response, data = api_client.get_json(f'/api/corners/aggregate?corner_ids={invalid_id}')

        assert response.status_code == 400
        assert 'error' in data


class TestCornersSearchAPI:
    """Test corners search API functionality."""

    def test_corners_search_by_name(self, api_client, corner_store, cleanup_geo_test_data):
        """Test successful corners search by name."""
        # Create test corners with specific names
        corner_store.create_corner(
            name="Coffee Shop Search Test",
            description="A cozy coffee shop",
            latitude=31.2304,
            longitude=121.4737,
            address="Address 1"
        )

        corner_store.create_corner(
            name="Tea House",
            description="A nice tea house",
            latitude=31.2310,
            longitude=121.4740,
            address="Address 2"
        )

        corner_store.create_corner(
            name="Coffee Corner",
            description="Another coffee place",
            latitude=31.2320,
            longitude=121.4750,
            address="Address 3"
        )

        # Search for "coffee"
        response, data = api_client.get_json('/api/corners/search?q=coffee')

        assert response.status_code == 200
        assert data['success'] is True
        assert 'corners' in data['data']
        assert 'total' in data['data']

        # Should find corners with "coffee" in name
        corner_names = [c['name'] for c in data['data']['corners']]
        coffee_corners = [name for name in corner_names if 'coffee' in name.lower()]
        assert len(coffee_corners) >= 2

    def test_corners_search_by_description(self, api_client, corner_store, cleanup_geo_test_data):
        """Test successful corners search by description."""
        # Create test corners
        corner_store.create_corner(
            name="Test Place 1",
            description="Cozy atmosphere with good music",
            latitude=31.2304,
            longitude=121.4737,
            address="Address 1"
        )

        corner_store.create_corner(
            name="Test Place 2",
            description="Quiet place for reading",
            latitude=31.2310,
            longitude=121.4740,
            address="Address 2"
        )

        # Search for "music"
        response, data = api_client.get_json('/api/corners/search?q=music')

        assert response.status_code == 200
        assert data['success'] is True
        assert len(data['data']['corners']) >= 1

    def test_corners_search_missing_parameter(self, api_client):
        """Test corners search API with missing query parameter."""
        response, data = api_client.get_json('/api/corners/search')

        assert response.status_code == 400
        assert 'error' in data

    def test_corners_search_empty_query(self, api_client):
        """Test corners search API with empty query."""
        response, data = api_client.get_json('/api/corners/search?q=')

        assert response.status_code == 400
        assert 'error' in data

    def test_corners_search_no_results(self, api_client, corner_store, cleanup_geo_test_data):
        """Test corners search API with no matching results."""
        # Create a corner that won't match
        corner_store.create_corner(
            name="XYZ Place",
            description="A unique place",
            latitude=31.2304,
            longitude=121.4737,
            address="Address"
        )

        # Search for something that doesn't exist
        response, data = api_client.get_json('/api/corners/search?q=nonexistentplace123')

        assert response.status_code == 200
        assert data['success'] is True
        assert len(data['data']['corners']) == 0
        assert data['data']['total'] == 0

    def test_corners_search_case_insensitive(self, api_client, corner_store, cleanup_geo_test_data):
        """Test corners search API is case insensitive."""
        corner_store.create_corner(
            name="COFFEE Shop",
            description="A coffee shop",
            latitude=31.2304,
            longitude=121.4737,
            address="Address"
        )

        # Search with different cases
        response_lower, data_lower = api_client.get_json('/api/corners/search?q=coffee')
        response_upper, data_upper = api_client.get_json('/api/corners/search?q=COFFEE')
        response_mixed, data_mixed = api_client.get_json('/api/corners/search?q=Coffee')

        assert response_lower.status_code == 200
        assert response_upper.status_code == 200
        assert response_mixed.status_code == 200

        # All should return the same result
        assert len(data_lower['data']['corners']) == 1
        assert len(data_upper['data']['corners']) == 1
        assert len(data_mixed['data']['corners']) == 1

    def test_corners_search_with_limit(self, api_client, corner_store, cleanup_geo_test_data):
        """Test corners search API with limit parameter."""
        # Create multiple corners
        for i in range(5):
            corner_store.create_corner(
                name=f"Search Test {i}",
                description=f"Test corner {i}",
                latitude=31.2304 + (i * 0.001),
                longitude=121.4737 + (i * 0.001),
                address=f"Address {i}"
            )

        # Search with limit
        response, data = api_client.get_json('/api/corners/search?q=search&limit=3')

        assert response.status_code == 200
        assert data['success'] is True
        assert len(data['data']['corners']) <= 3
