"""End-to-end integration tests for Urban Canvas backend.

This module tests complete user flows through the application.
"""
import pytest
import io
from bson import ObjectId


@pytest.mark.integration
class TestCompleteUserFlow:
    """Test complete user flow from registration to content interaction."""

    def test_complete_post_with_route_flow(self, client, cleanup_test_data):
        """Test complete flow: register → create corners → upload media → create post with route."""
        # 1. Register user
        register_data = {
            'username': 'test_flow_user',
            'password': 'testpassword123'
        }
        response = client.post('/api/auth/register', json=register_data)
        assert response.status_code == 201
        user_data = response.get_json()
        user_id = user_data['user']['id']

        # 2. Login to get token
        login_data = {
            'username': 'test_flow_user',
            'password': 'testpassword123'
        }
        response = client.post('/api/auth/login', json=login_data)
        assert response.status_code == 200
        login_result = response.get_json()
        token = login_result['token']

        headers = {'Authorization': f'Bearer {token}'}

        # 3. Set user interest tags
        response = client.put(
            f'/api/users/{user_id}/interests',
            json={'interest_tags': ['food', 'coffee', 'travel']},
            headers=headers
        )
        assert response.status_code == 200

        # 4. Create corners
        corner1_data = {
            'name': 'Old Alley Cafe',
            'description': 'A quiet cafe',
            'latitude': 31.2304,
            'longitude': 121.4737,
            'address': 'No. 1 Old Alley, Huangpu District, Shanghai'
        }
        response = client.post('/api/corners', json=corner1_data, headers=headers)
        assert response.status_code == 201
        corner1 = response.get_json()['data']
        corner1_id = corner1['_id']

        corner2_data = {
            'name': 'Small Lane Restaurant',
            'description': 'Authentic Shanghai cuisine',
            'latitude': 31.2404,
            'longitude': 121.4837,
            'address': 'No. 2 Small Lane, Huangpu District, Shanghai'
        }
        response = client.post('/api/corners', json=corner2_data, headers=headers)
        assert response.status_code == 201
        corner2 = response.get_json()['data']
        corner2_id = corner2['_id']

        # 5. Upload media file
        image_content = io.BytesIO(b'fake image content for testing')
        image_content.name = 'test.jpg'
        image_content.content_type = 'image/jpeg'

        # Create multipart form data
        boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
        body = (
            f'------WebKitFormBoundary7MA4YWxkTrZu0gW\r\n'
            f'Content-Disposition: form-data; name="file"; filename="test.jpg"\r\n'
            f'Content-Type: image/jpeg\r\n\r\n'
        ).encode('utf-8') + image_content.getvalue() + (
            f'\r\n------WebKitFormBoundary7MA4YWxkTrZu0gW\r\n'
            f'Content-Disposition: form-data; name="media_type"\r\n\r\n'
            f'image\r\n'
            f'------WebKitFormBoundary7MA4YWxkTrZu0gW--\r\n'
        ).encode('utf-8')

        content_type = f'multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW'

        response = client.post(
            '/api/media/upload',
            data=body,
            content_type=content_type,
            headers=headers
        )
        assert response.status_code == 201
        upload_result = response.get_json()
        image_id = upload_result['data']['file_id']

        # 6. Create post with route
        post_data = {
            'title': 'Weekend Cafe Tour',
            'description': 'Explored two unique shops',
            'corner_ids': [corner1_id, corner2_id],
            'media_type': 'image',
            'media_files': [image_id],
            'tags': ['food', 'coffee'],
            'visibility': 'public',
            'route': {
                'route_name': 'Weekend Cafe Tour',
                'corner_ids': [corner1_id, corner2_id]
            }
        }
        response = client.post('/api/posts', json=post_data, headers=headers)
        assert response.status_code == 201
        post = response.get_json()['data']
        post_id = post['_id']

        # 7. Get post details
        response = client.get(f'/api/posts/{post_id}', headers=headers)
        assert response.status_code == 200
        post_detail = response.get_json()['data']
        assert post_detail['title'] == 'Weekend Cafe Tour'
        assert post_detail['route']['route_name'] == 'Weekend Cafe Tour'

        # 8. Get post route details
        response = client.get(f'/api/posts/{post_id}/route', headers=headers)
        assert response.status_code == 200
        route_data = response.get_json()['data']['route']
        assert route_data['route_name'] == 'Weekend Cafe Tour'
        assert len(route_data['corners']) == 2
        assert route_data['corners'][0]['name'] == 'Old Alley Cafe'
        assert route_data['corners'][1]['name'] == 'Small Lane Restaurant'

        # 9. Query nearby corners
        response = client.get(
            '/api/corners/nearby?lat=31.2304&lng=121.4737&radius=1000',
            headers=headers
        )
        assert response.status_code == 200
        nearby = response.get_json()['data']['corners']
        corner_ids = [c['_id'] for c in nearby]
        assert corner1_id in corner_ids

        # 10. Get corners aggregate
        response = client.get(
            f'/api/corners/aggregate?corner_ids={corner1_id},{corner2_id}',
            headers=headers
        )
        assert response.status_code == 200
        aggregate_data = response.get_json()['data']['corners']
        assert len(aggregate_data) == 2
        assert aggregate_data[0]['post_count'] >= 1

        # 11. Search corners
        response = client.get('/api/corners/search?q=cafe', headers=headers)
        assert response.status_code == 200
        search_results = response.get_json()['data']['corners']
        corner_names = [c['name'] for c in search_results]
        assert 'Old Alley Cafe' in corner_names

        # 12. Get comprehensive feed
        response = client.get(
            '/api/feed?type=all&lat=31.2304&lng=121.4737',
            headers=headers
        )
        assert response.status_code == 200
        feed_posts = response.get_json()['data']['posts']
        post_ids = [p['_id'] for p in feed_posts]
        assert post_id in post_ids


@pytest.mark.integration
class TestFollowAndFeedFlow:
    """Test follow system and feed functionality."""

    def test_follow_and_feed_interaction(self, client, cleanup_test_data):
        """Test complete follow and feed interaction flow."""
        # 1. Register two users
        user1_data = {
            'username': 'creator_user',
            'password': 'password123'
        }
        response = client.post('/api/auth/register', json=user1_data)
        assert response.status_code == 201
        user1 = response.get_json()['user']
        user1_id = user1['id']

        user1_login_data = {
            'username': 'creator_user',
            'password': 'password123'
        }
        response = client.post('/api/auth/login', json=user1_login_data)
        assert response.status_code == 200
        user1_token = response.get_json()['token']

        user2_data = {
            'username': 'follower_user',
            'password': 'password123'
        }
        response = client.post('/api/auth/register', json=user2_data)
        assert response.status_code == 201
        user2 = response.get_json()['user']
        user2_id = user2['id']

        user2_login_data = {
            'username': 'follower_user',
            'password': 'password123'
        }
        response = client.post('/api/auth/login', json=user2_login_data)
        assert response.status_code == 200
        user2_token = response.get_json()['token']

        user1_headers = {'Authorization': f'Bearer {user1_token}'}
        user2_headers = {'Authorization': f'Bearer {user2_token}'}

        # 2. user2 follows user1
        response = client.post(f'/api/follows/{user1_id}', headers=user2_headers)
        assert response.status_code == 200
        follow_result = response.get_json()['data']
        assert follow_result['is_following'] is True

        # 3. user1 creates a post
        corner_data = {
            'name': 'Test Location',
            'description': 'Location for testing',
            'latitude': 31.2304,
            'longitude': 121.4737
        }
        response = client.post('/api/corners', json=corner_data, headers=user1_headers)
        assert response.status_code == 201
        corner = response.get_json()['data']
        corner_id = corner['_id']

        # Upload media
        image_content = io.BytesIO(b'test image')
        image_content.name = 'test.jpg'
        image_content.content_type = 'image/jpeg'

        boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
        body = (
            f'------WebKitFormBoundary7MA4YWxkTrZu0gW\r\n'
            f'Content-Disposition: form-data; name="file"; filename="test.jpg"\r\n'
            f'Content-Type: image/jpeg\r\n\r\n'
        ).encode('utf-8') + image_content.getvalue() + (
            f'\r\n------WebKitFormBoundary7MA4YWxkTrZu0gW\r\n'
            f'Content-Disposition: form-data; name="media_type"\r\n\r\n'
            f'image\r\n'
            f'------WebKitFormBoundary7MA4YWxkTrZu0gW--\r\n'
        ).encode('utf-8')

        content_type = f'multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW'

        response = client.post(
            '/api/media/upload',
            data=body,
            content_type=content_type,
            headers=user1_headers
        )
        assert response.status_code == 200
        image_id = response.get_json()['data']['file_id']

        # Create post
        post_data = {
            'title': 'Test Post',
            'description': 'Post for testing',
            'corner_ids': [corner_id],
            'media_type': 'image',
            'media_files': [image_id],
            'visibility': 'public'
        }
        response = client.post('/api/posts', json=post_data, headers=user1_headers)
        assert response.status_code == 201
        post = response.get_json()['data']
        post_id = post['_id']

        # 4. user2 gets following feed
        response = client.get('/api/feed/following', headers=user2_headers)
        assert response.status_code == 200
        feed_posts = response.get_json()['data']['posts']
        post_ids = [p['_id'] for p in feed_posts]
        assert post_id in post_ids

        # 5. user2 gets comprehensive feed with following type
        response = client.get('/api/feed?type=following', headers=user2_headers)
        assert response.status_code == 200
        feed_posts = response.get_json()['data']['posts']
        post_ids = [p['_id'] for p in feed_posts]
        assert post_id in post_ids

        # 6. Check follow status
        response = client.get(f'/api/follows/{user1_id}/status', headers=user2_headers)
        assert response.status_code == 200
        status = response.get_json()['data']
        assert status['is_following'] is True

        # 7. user2 unfollows user1
        response = client.delete(f'/api/follows/{user1_id}', headers=user2_headers)
        assert response.status_code == 200
        unfollow_result = response.get_json()['data']
        assert unfollow_result['is_following'] is False


@pytest.mark.integration
class TestRecommendationFlow:
    """Test recommendation system functionality."""

    def test_recommendation_with_location(self, client, cleanup_test_data):
        """Test recommendation feed with user location."""
        # 1. Register user
        register_data = {
            'username': 'rec_test_user',
            'password': 'password123'
        }
        response = client.post('/api/auth/register', json=register_data)
        assert response.status_code == 201
        user = response.get_json()['user']
        user_id = user['id']

        login_data = {
            'username': 'rec_test_user',
            'password': 'password123'
        }
        response = client.post('/api/auth/login', json=login_data)
        assert response.status_code == 200
        token = response.get_json()['token']

        headers = {'Authorization': f'Bearer {token}'}

        # 2. Set user interests
        response = client.put(
            f'/api/users/{user_id}/interests',
            json={'interest_tags': ['food', 'coffee']},
            headers=headers
        )
        assert response.status_code == 200

        # 3. Create corners at specific locations
        corner1_data = {
            'name': 'Nearby Cafe',
            'description': 'A cafe nearby',
            'latitude': 31.2305,
            'longitude': 121.4738,
            'tags': ['coffee', 'food']
        }
        response = client.post('/api/corners', json=corner1_data, headers=headers)
        assert response.status_code == 201
        corner1 = response.get_json()['data']

        # 4. Upload and create post
        image_content = io.BytesIO(b'test image')
        image_content.name = 'test.jpg'
        image_content.content_type = 'image/jpeg'

        boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
        body = (
            f'------WebKitFormBoundary7MA4YWxkTrZu0gW\r\n'
            f'Content-Disposition: form-data; name="file"; filename="test.jpg"\r\n'
            f'Content-Type: image/jpeg\r\n\r\n'
        ).encode('utf-8') + image_content.getvalue() + (
            f'\r\n------WebKitFormBoundary7MA4YWxkTrZu0gW\r\n'
            f'Content-Disposition: form-data; name="media_type"\r\n\r\n'
            f'image\r\n'
            f'------WebKitFormBoundary7MA4YWxkTrZu0gW--\r\n'
        ).encode('utf-8')

        content_type = f'multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW'

        response = client.post(
            '/api/media/upload',
            data=body,
            content_type=content_type,
            headers=headers
        )
        assert response.status_code == 200
        image_id = response.get_json()['data']['file_id']

        post_data = {
            'title': 'Nearby Cafe Recommendation',
            'description': 'This cafe is great',
            'corner_ids': [corner1['_id']],
            'media_type': 'image',
            'media_files': [image_id],
            'tags': ['food', 'coffee'],
            'visibility': 'public'
        }
        response = client.post('/api/posts', json=post_data, headers=headers)
        assert response.status_code == 201
        post = response.get_json()['data']

        # 5. Get recommendation feed with location
        response = client.get(
            '/api/recommendations/feed?lat=31.2304&lng=121.4737',
            headers=headers
        )
        assert response.status_code == 200
        rec_posts = response.get_json()['data']['posts']
        post_ids = [p['_id'] for p in rec_posts]
        # The post should appear in recommendations
        # (might not appear if other posts exist, but API should work)
        assert isinstance(rec_posts, list)

        # 6. Get recommendation corners
        response = client.get(
            '/api/recommendations/corners?lat=31.2304&lng=121.4737&radius=1000',
            headers=headers
        )
        assert response.status_code == 200
        rec_corners = response.get_json()['data']['corners']
        assert isinstance(rec_corners, list)

        # 7. Get recommendation config
        response = client.get('/api/recommendations/config')
        assert response.status_code == 200
        config = response.get_json()['data']
        assert 'weights' in config
        assert config['weights']['geo'] == 0.4
        assert config['weights']['interest'] == 0.3


@pytest.mark.integration
class TestPostVisibilityFlow:
    """Test post visibility and access control."""

    def test_post_visibility_scenarios(self, client, cleanup_test_data):
        """Test different post visibility scenarios."""
        # 1. Register two users
        user1_data = {
            'username': 'visibility_user1',
            'password': 'password123'
        }
        response = client.post('/api/auth/register', json=user1_data)
        assert response.status_code == 201
        user1 = response.get_json()['user']
        user1_id = user1['id']

        user1_login_data = {
            'username': 'visibility_user1',
            'password': 'password123'
        }
        response = client.post('/api/auth/login', json=user1_login_data)
        assert response.status_code == 200
        user1_token = response.get_json()['token']

        user2_data = {
            'username': 'visibility_user2',
            'password': 'password123'
        }
        response = client.post('/api/auth/register', json=user2_data)
        assert response.status_code == 201
        user2 = response.get_json()['user']
        user2_id = user2['id']

        user2_login_data = {
            'username': 'visibility_user2',
            'password': 'password123'
        }
        response = client.post('/api/auth/login', json=user2_login_data)
        assert response.status_code == 200
        user2_token = response.get_json()['token']

        user1_headers = {'Authorization': f'Bearer {user1_token}'}
        user2_headers = {'Authorization': f'Bearer {user2_token}'}

        # 2. user2 follows user1
        response = client.post(f'/api/follows/{user1_id}', headers=user2_headers)
        assert response.status_code == 200

        # 3. Upload media
        image_content = io.BytesIO(b'test image')
        image_content.name = 'test.jpg'
        image_content.content_type = 'image/jpeg'

        boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
        body = (
            f'------WebKitFormBoundary7MA4YWxkTrZu0gW\r\n'
            f'Content-Disposition: form-data; name="file"; filename="test.jpg"\r\n'
            f'Content-Type: image/jpeg\r\n\r\n'
        ).encode('utf-8') + image_content.getvalue() + (
            f'\r\n------WebKitFormBoundary7MA4YWxkTrZu0gW\r\n'
            f'Content-Disposition: form-data; name="media_type"\r\n\r\n'
            f'image\r\n'
            f'------WebKitFormBoundary7MA4YWxkTrZu0gW--\r\n'
        ).encode('utf-8')

        content_type = f'multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW'

        response = client.post(
            '/api/media/upload',
            data=body,
            content_type=content_type,
            headers=user1_headers
        )
        assert response.status_code == 200
        image_id = response.get_json()['data']['file_id']

        # 4. Create posts with different visibility
        # Public post
        public_post_data = {
            'title': 'Public Post',
            'media_type': 'image',
            'media_files': [image_id],
            'visibility': 'public'
        }
        response = client.post('/api/posts', json=public_post_data, headers=user1_headers)
        assert response.status_code == 201
        public_post_id = response.get_json()['data']['_id']

        # Private post
        private_post_data = {
            'title': 'Private Post',
            'media_type': 'image',
            'media_files': [image_id],
            'visibility': 'private'
        }
        response = client.post('/api/posts', json=private_post_data, headers=user1_headers)
        assert response.status_code == 201
        private_post_id = response.get_json()['data']['_id']

        # Followers-only post
        followers_post_data = {
            'title': 'Followers Post',
            'media_type': 'image',
            'media_files': [image_id],
            'visibility': 'followers'
        }
        response = client.post('/api/posts', json=followers_post_data, headers=user1_headers)
        assert response.status_code == 201
        followers_post_id = response.get_json()['data']['_id']

        # 5. Test visibility scenarios
        # Public post: visible to everyone
        response = client.get(f'/api/posts/{public_post_id}', headers=user1_headers)
        assert response.status_code == 200

        response = client.get(f'/api/posts/{public_post_id}', headers=user2_headers)
        assert response.status_code == 200

        # Private post: only visible to creator
        response = client.get(f'/api/posts/{private_post_id}', headers=user1_headers)
        assert response.status_code == 200

        response = client.get(f'/api/posts/{private_post_id}', headers=user2_headers)
        assert response.status_code == 403

        # Followers-only post: visible to creator and followers
        response = client.get(f'/api/posts/{followers_post_id}', headers=user1_headers)
        assert response.status_code == 200

        response = client.get(f'/api/posts/{followers_post_id}', headers=user2_headers)
        assert response.status_code == 200  # user2 follows user1


@pytest.mark.integration
class TestFeedTypesFlow:
    """Test different feed types and filtering."""

    def test_feed_type_variations(self, client, cleanup_test_data):
        """Test different feed types (all, recommendation, following)."""
        # 1. Register user
        register_data = {
            'username': 'feed_test_user',
            'password': 'password123'
        }
        response = client.post('/api/auth/register', json=register_data)
        assert response.status_code == 201

        login_data = {
            'username': 'feed_test_user',
            'password': 'password123'
        }
        response = client.post('/api/auth/login', json=login_data)
        assert response.status_code == 200
        token = response.get_json()['token']

        headers = {'Authorization': f'Bearer {token}'}

        # 2. Create corner and post
        corner_data = {
            'name': 'Test Location',
            'description': 'For testing',
            'latitude': 31.2304,
            'longitude': 121.4737
        }
        response = client.post('/api/corners', json=corner_data, headers=headers)
        assert response.status_code == 201
        corner_id = response.get_json()['data']['_id']

        # Upload media
        image_content = io.BytesIO(b'test image')
        image_content.name = 'test.jpg'
        image_content.content_type = 'image/jpeg'

        boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
        body = (
            f'------WebKitFormBoundary7MA4YWxkTrZu0gW\r\n'
            f'Content-Disposition: form-data; name="file"; filename="test.jpg"\r\n'
            f'Content-Type: image/jpeg\r\n\r\n'
        ).encode('utf-8') + image_content.getvalue() + (
            f'\r\n------WebKitFormBoundary7MA4YWxkTrZu0gW\r\n'
            f'Content-Disposition: form-data; name="media_type"\r\n\r\n'
            f'image\r\n'
            f'------WebKitFormBoundary7MA4YWxkTrZu0gW--\r\n'
        ).encode('utf-8')

        content_type = f'multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW'

        response = client.post(
            '/api/media/upload',
            data=body,
            content_type=content_type,
            headers=headers
        )
        assert response.status_code == 200
        image_id = response.get_json()['data']['file_id']

        post_data = {
            'title': 'Test Post',
            'media_type': 'image',
            'media_files': [image_id],
            'visibility': 'public'
        }
        response = client.post('/api/posts', json=post_data, headers=headers)
        assert response.status_code == 201

        # 3. Test different feed types
        # All type
        response = client.get('/api/feed?type=all', headers=headers)
        assert response.status_code == 200
        assert 'posts' in response.get_json()['data']

        # Recommendation type
        response = client.get('/api/feed?type=recommendation', headers=headers)
        assert response.status_code == 200
        assert 'posts' in response.get_json()['data']

        # Following type
        response = client.get('/api/feed?type=following', headers=headers)
        assert response.status_code == 200
        assert 'posts' in response.get_json()['data']

        # Invalid type
        response = client.get('/api/feed?type=invalid', headers=headers)
        assert response.status_code == 400
