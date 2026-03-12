"""Recommendation endpoints."""
from flask import Blueprint, request, jsonify

from services.recommendation_service import get_recommendation_service
from storage.user_store import UserStore
from utils import jwt_required, jwt_optional
from config import Config

bp = Blueprint('recommendations', __name__)

# Get recommendation service instance
recommendation_service = get_recommendation_service()
user_store = UserStore()


@bp.route('/api/recommendations/feed', methods=['GET'])
@jwt_optional
def get_recommendation_feed():
    """
    Get personalized recommendation feed.

    Get personalized recommended post feed based on user location, interests, social relationships, and behavior history.

    Query parameters:
        - lat: User's current latitude (optional)
        - lng: User's current longitude (optional)
        - limit: Number of posts to return (default 20)

    Returns:
        JSON with recommended posts list
    """
    current_user_id = getattr(request, 'user_id', None)

    # Get query parameters
    try:
        limit = int(request.args.get('limit', 20))
        limit = min(limit, 100)
    except ValueError:
        limit = 20

    # Get user location
    user_location = None
    lat = request.args.get('lat')
    lng = request.args.get('lng')

    if lat and lng:
        try:
            user_location = (float(lat), float(lng))
            # Validate coordinates
            if not (-90 <= user_location[0] <= 90 and -180 <= user_location[1] <= 180):
                return jsonify({'error': 'Invalid coordinates'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid coordinates format'}), 400

    # Get recommendations
    try:
        posts = recommendation_service.recommend_feed(
            user_id=current_user_id,
            user_location=user_location,
            limit=limit
        )

        # Expand post data
        result = []
        for post in posts:
            post_data = {
                '_id': str(post['_id']),
                'user_id': str(post['user_id']),
                'title': post.get('title', ''),
                'description': post.get('description', ''),
                'media_type': post.get('media_type'),
                'media_files': [str(fid) for fid in post.get('media_files', [])],
                'tags': post.get('tags', []),
                'visibility': post.get('visibility'),
                'created_at': post.get('created_at'),
                'stats': post.get('stats', {})
            }

            # Get creator username
            creator = user_store.get_user_by_id(post['user_id'])
            if creator:
                post_data['username'] = creator.get('username', '')

            result.append(post_data)

        response_data = {
            'success': True,
            'data': {
                'posts': result,
                'total': len(result)
            }
        }

        # Add user location if provided
        if user_location:
            response_data['data']['user_location'] = {
                'lat': user_location[0],
                'lng': user_location[1]
            }

        return jsonify(response_data)

    except Exception as e:
        return jsonify({'error': f'Failed to get recommendations: {str(e)}'}), 500


@bp.route('/api/recommendations/corners', methods=['GET'])
@jwt_optional
def get_recommendation_corners():
    """
    Get recommended corners.

    Recommend corners that may be of interest based on user location and interests.

    Query parameters:
        - lat: User's current latitude (optional)
        - lng: User's current longitude (optional)
        - radius: Search radius in meters (default 10000)
        - limit: Number of corners to return (default 10)

    Returns:
        JSON with recommended corners list
    """
    current_user_id = getattr(request, 'user_id', None)

    # Get query parameters
    try:
        radius = int(request.args.get('radius', 10000))
        if radius < 10 or radius > 100000:
            return jsonify({'error': 'Invalid radius (must be 10 to 100000 meters)'}), 400
    except ValueError:
        radius = 10000

    try:
        limit = int(request.args.get('limit', 10))
        limit = min(limit, 50)
    except ValueError:
        limit = 10

    # Get user location
    user_location = None
    lat = request.args.get('lat')
    lng = request.args.get('lng')

    if lat and lng:
        try:
            user_location = (float(lat), float(lng))
            # Validate coordinates
            if not (-90 <= user_location[0] <= 90 and -180 <= user_location[1] <= 180):
                return jsonify({'error': 'Invalid coordinates'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid coordinates format'}), 400

    # Get recommendations
    try:
        corners = recommendation_service.recommend_corners(
            user_id=current_user_id,
            user_location=user_location,
            radius=radius,
            limit=limit
        )

        response_data = {
            'success': True,
            'data': {
                'corners': corners,
                'total': len(corners)
            }
        }

        # Add query info if location provided
        if user_location:
            response_data['data']['query_point'] = {
                'lat': user_location[0],
                'lng': user_location[1]
            }
            response_data['data']['radius'] = radius

        return jsonify(response_data)

    except Exception as e:
        return jsonify({'error': f'Failed to get corner recommendations: {str(e)}'}), 500


@bp.route('/api/recommendations/config', methods=['GET'])
def get_recommendation_config():
    """
    Get recommendation algorithm weight configuration (for debugging).

    Returns:
        JSON with recommendation weights
    """
    try:
        weights = recommendation_service.weights

        return jsonify({
            'success': True,
            'data': {
                'weights': {
                    'geo': weights['geo'],
                    'interest': weights['interest'],
                    'social': weights['social'],
                    'behavior': weights['behavior']
                },
                'weight_sum': sum(weights.values())
            }
        })

    except Exception as e:
        return jsonify({'error': f'Failed to get config: {str(e)}'}), 500


@bp.route('/api/recommendations/stats', methods=['GET'])
@jwt_required
def get_recommendation_stats():
    """
    Get recommendation algorithm statistics.

    Returns:
        JSON with recommendation statistics
    """
    try:
        # Get recommendation service cache info
        cache_info = getattr(recommendation_service, 'recommend_feed', None)
        cache_stats = {}

        if cache_info and hasattr(cache_info, 'cache_info'):
            cache_info_data = cache_info.cache_info()
            cache_stats = {
                'cache_hits': cache_info_data.hits,
                'cache_misses': cache_info_data.misses,
                'cache_size': cache_info_data.currsize,
                'cache_maxsize': cache_info_data.maxsize
            }

        return jsonify({
            'success': True,
            'data': {
                'cache_stats': cache_stats,
                'service_initialized': recommendation_service is not None
            }
        })

    except Exception as e:
        return jsonify({'error': f'Failed to get stats: {str(e)}'}), 500