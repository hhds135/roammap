"""Corner management endpoints."""
from datetime import datetime
from flask import Blueprint, request, jsonify
from bson import ObjectId

from storage.corner_store import CornerStore
from storage.post_store import PostStore
from storage.user_store import UserStore
from storage.connection import MongoDBConnection, get_db
from utils import jwt_required, jwt_optional, check_post_visibility, is_following_user
from config import Config

bp = Blueprint('corners', __name__)

# Initialize MongoDB connection if not already connected
try:
    if get_db() is None:
        conn = MongoDBConnection()
        conn.connect()
except Exception:
    pass

corner_store = CornerStore()
post_store = PostStore()
user_store = UserStore()


def validate_corner_data(data, is_update=False):
    """
    Validate corner creation/update data.

    Args:
        data: Request JSON data
        is_update: Whether this is an update operation

    Returns:
        tuple: (is_valid, error_message)
    """
    if not is_update:
        # Required fields for creation
        required_fields = ['name', 'latitude', 'longitude']
        for field in required_fields:
            if field not in data:
                return False, f'Missing required field: {field}'

    # Validate coordinates
    if 'latitude' in data:
        try:
            lat = float(data['latitude'])
            if not -90 <= lat <= 90:
                return False, 'Latitude must be between -90 and 90'
        except (ValueError, TypeError):
            return False, 'Invalid latitude'

    if 'longitude' in data:
        try:
            lng = float(data['longitude'])
            if not -180 <= lng <= 180:
                return False, 'Longitude must be between -180 and 180'
        except (ValueError, TypeError):
            return False, 'Invalid longitude'

    # Validate tags
    if 'tags' in data:
        if not isinstance(data['tags'], list):
            return False, 'tags must be an array'

    return True, None


@bp.route('/api/corners', methods=['GET'])
@jwt_optional
def get_corners():
    """
    Get list of corners with filtering and search support.

    Query parameters:
        - limit: Return quantity limit (default 100)
        - search: Search keyword (matches name or description)
        - user_id: User ID, only return corners created by this user

    Returns:
        JSON with corners list
    """
    try:
        limit = int(request.args.get('limit', 100))
        limit = min(limit, 100)
    except ValueError:
        limit = 100

    search = request.args.get('search')
    user_id = request.args.get('user_id')

    # Query corners
    query = {}
    if search:
        query = {'name': {'$regex': search, '$options': 'i'}}
        corners = corner_store.find(query, limit=limit)
    elif user_id:
        # Get corners created by specific user
        try:
            user_id_obj = ObjectId(user_id)
            query = {'creator_id': user_id_obj}
            corners = corner_store.find(query, limit=limit)
        except Exception:
            return jsonify({'error': 'Invalid user_id parameter'}), 400
    else:
        query = {}
        corners = corner_store.get_all_corners(limit=limit)

    # Convert ObjectIds to strings for JSON response
    result = []
    for corner in corners:
        corner_data = {
            '_id': str(corner['_id']),
            'name': corner.get('name', ''),
            'description': corner.get('description', ''),
            'location': corner.get('location'),
            'address': corner.get('address', ''),
            'created_at': corner.get('created_at')
        }
        result.append(corner_data)

    return jsonify({
        'success': True,
        'data': {
            'corners': result,
            'total': corner_store.count(query)
        }
    })


@bp.route('/api/corners', methods=['POST'])
@jwt_required
def create_corner():
    """
    Create a new corner.

    Request body (JSON):
        - name: Corner name (required)
        - description: Corner description
        - latitude: Latitude (required, -90 to 90)
        - longitude: Longitude (required, -180 to 180)
        - address: Address
        - tags: List of tags

    Returns:
        JSON with created corner data
    """
    data = request.get_json()

    # Validate data
    is_valid, error_msg = validate_corner_data(data)
    if not is_valid:
        return jsonify({'error': error_msg}), 400

    # Extract fields
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    latitude = float(data['latitude'])
    longitude = float(data['longitude'])
    address = data.get('address', '').strip()
    tags = data.get('tags', [])
    images = data.get('images', [])

    # Check if corner name already exists
    existing_corner = corner_store.get_corner_by_name(name)
    if existing_corner:
        return jsonify({'error': 'Corner with this name already exists'}), 400

    # Get current user ID from JWT token
    current_user_id = getattr(request, 'user_id', None)
    creator_id = ObjectId(current_user_id) if current_user_id else None

    # Create corner
    try:
        corner_id = corner_store.create_corner(
            name=name,
            description=description,
            latitude=latitude,
            longitude=longitude,
            address=address,
            images=images,
            creator_id=creator_id
        )

        # Add tags if provided
        if tags:
            corner_store.update(corner_id, {'tags': tags})

        # Get created corner
        corner = corner_store.get_corner_by_id(corner_id)

        return jsonify({
            'success': True,
            'message': 'Corner created successfully',
            'data': {
                '_id': str(corner['_id']),
                'name': corner['name'],
                'description': corner['description'],
                'location': corner['location'],
                'address': corner['address'],
                'tags': corner.get('tags', []),
                'images': corner.get('images', []),
                'created_at': corner['created_at']
            }
        }), 201

    except Exception as e:
        return jsonify({'error': f'Failed to create corner: {str(e)}'}), 500


@bp.route('/api/corners/<corner_id>', methods=['GET'])
def get_corner_detail(corner_id):
    """
    Get corner details.

    Args:
        corner_id: Corner ID

    Returns:
        JSON with corner detail
    """
    try:
        corner_obj = ObjectId(corner_id)
    except Exception:
        return jsonify({'error': 'Invalid corner ID'}), 400

    corner = corner_store.get_corner_by_id(corner_obj)
    if not corner:
        return jsonify({'error': 'Corner not found'}), 404

    return jsonify({
        'success': True,
        'data': {
            '_id': str(corner['_id']),
            'name': corner['name'],
            'description': corner['description'],
            'location': corner['location'],
            'address': corner['address'],
            'tags': corner.get('tags', []),
            'images': [str(img_id) for img_id in corner.get('images', [])],  # Convert ObjectIds to strings
            'created_at': corner['created_at']
        }
    })


@bp.route('/api/corners/<corner_id>', methods=['PUT'])
@jwt_required
def update_corner(corner_id):
    """
    Update corner information.

    Args:
        corner_id: Corner ID

    Request body (JSON):
        - name: Corner name
        - description: Corner description
        - latitude: Latitude
        - longitude: Longitude
        - address: Address
        - tags: List of tags

    Returns:
        JSON with updated corner data
    """
    try:
        corner_obj = ObjectId(corner_id)
    except Exception:
        return jsonify({'error': 'Invalid corner ID'}), 400

    # Check if corner exists
    corner = corner_store.get_corner_by_id(corner_obj)
    if not corner:
        return jsonify({'error': 'Corner not found'}), 404

    data = request.get_json()

    # Validate data
    is_valid, error_msg = validate_corner_data(data, is_update=True)
    if not is_valid:
        return jsonify({'error': error_msg}), 400

    # Build update object
    updates = {}

    if 'name' in data:
        name = data['name'].strip()
        # Check if new name conflicts with another corner
        existing_corner = corner_store.get_corner_by_name(name)
        if existing_corner and str(existing_corner['_id']) != corner_id:
            return jsonify({'error': 'Corner with this name already exists'}), 400
        updates['name'] = name

    if 'description' in data:
        updates['description'] = data['description'].strip()

    if 'latitude' in data and 'longitude' in data:
        latitude = float(data['latitude'])
        longitude = float(data['longitude'])
        updates['location'] = {
            'type': 'Point',
            'coordinates': [longitude, latitude]
        }

    if 'address' in data:
        updates['address'] = data['address'].strip()

    if 'tags' in data:
        updates['tags'] = data['tags']

    if 'images' in data:
        updates['images'] = data['images']

    # Update corner
    success = corner_store.update(corner_obj, updates)
    if not success:
        return jsonify({'error': 'Failed to update corner'}), 500

    # Get updated corner
    updated_corner = corner_store.get_corner_by_id(corner_obj)

    return jsonify({
        'success': True,
        'message': 'Corner updated successfully',
        'data': {
            '_id': str(updated_corner['_id']),
            'name': updated_corner['name'],
            'description': updated_corner['description'],
            'location': updated_corner['location'],
            'address': updated_corner['address'],
            'tags': updated_corner.get('tags', []),
            'images': updated_corner.get('images', []),
            'created_at': updated_corner['created_at']
        }
    })


@bp.route('/api/corners/<corner_id>', methods=['DELETE'])
@jwt_required
def delete_corner(corner_id):
    """
    Delete a corner.

    Args:
        corner_id: Corner ID

    Returns:
        JSON with success message
    """
    try:
        corner_obj = ObjectId(corner_id)
    except Exception:
        return jsonify({'error': 'Invalid corner ID'}), 400

    # Check if corner exists
    corner = corner_store.get_corner_by_id(corner_obj)
    if not corner:
        return jsonify({'error': 'Corner not found'}), 404

    # Delete corner
    success = corner_store.delete(corner_obj)
    if not success:
        return jsonify({'error': 'Failed to delete corner'}), 500

    return jsonify({
        'success': True,
        'message': 'Corner deleted successfully'
    })


@bp.route('/api/corners/nearby', methods=['GET'])
@jwt_optional
def get_nearby_corners():
    """
    Query nearby corners.

    Query parameters:
        - lat: Latitude (required, -90 to 90)
        - lng: Longitude (required, -180 to 180)
        - radius: Search radius in meters (default 10000, i.e., 10km)
        - limit: Return quantity limit (default 20)

    Returns:
        JSON with nearby corners sorted by distance
    """
    # Get and validate parameters
    try:
        lat = float(request.args.get('lat'))
        if not -90 <= lat <= 90:
            return jsonify({'error': 'Invalid latitude (must be -90 to 90)'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'Missing or invalid parameter: lat'}), 400

    try:
        lng = float(request.args.get('lng'))
        if not -180 <= lng <= 180:
            return jsonify({'error': 'Invalid longitude (must be -180 to 180)'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'Missing or invalid parameter: lng'}), 400

    try:
        radius = int(request.args.get('radius', 10000))
        if radius < 10 or radius > 100000:
            return jsonify({'error': 'Invalid radius (must be 10 to 100000 meters)'}), 400
    except (ValueError, TypeError):
        radius = 10000

    try:
        limit = int(request.args.get('limit', 20))
        limit = min(limit, 100)
    except (ValueError, TypeError):
        limit = 20

    # Query nearby corners
    corners = corner_store.get_nearby_corners(
        latitude=lat,
        longitude=lng,
        max_distance=radius,
        limit=limit
    )

    # Prepare response with distance information
    result = []
    for corner in corners:
        # Calculate distance
        distance = corner_store.calculate_distance(
            lat, lng,
            corner['location']['coordinates'][1],
            corner['location']['coordinates'][0]
        )

        corner_data = {
            '_id': str(corner['_id']),
            'name': corner.get('name', ''),
            'description': corner.get('description', ''),
            'location': corner['location'],
            'address': corner.get('address', ''),
            'distance': round(distance, 2),  # Distance in meters
            'images': [str(img_id) for img_id in corner.get('images', [])],  # Convert ObjectIds to strings
            'tags': corner.get('tags', []),
            'created_at': corner.get('created_at')
        }
        result.append(corner_data)

    return jsonify({
        'success': True,
        'data': {
            'corners': result,
            'query_point': {
                'lat': lat,
                'lng': lng
            },
            'radius': radius,
            'total': len(result)
        }
    })


@bp.route('/api/corners/<corner_id>/posts', methods=['GET'])
@jwt_optional
def get_corner_posts(corner_id):
    """
    Get all posts associated with a specific corner.

    Args:
        corner_id: Corner ID

    Query parameters:
        - limit: Items per page (default 20)
        - skip: Number of items to skip (for pagination)

    Returns:
        JSON with corner info and posts list
    """
    try:
        corner_obj = ObjectId(corner_id)
    except Exception:
        return jsonify({'error': 'Invalid corner ID'}), 400

    # Get corner
    corner = corner_store.get_corner_by_id(corner_obj)
    if not corner:
        return jsonify({'error': 'Corner not found'}), 404

    # Get pagination parameters
    try:
        limit = int(request.args.get('limit', 20))
        limit = min(limit, 100)
    except ValueError:
        limit = 20

    try:
        skip = int(request.args.get('skip', 0))
        if skip < 0:
            skip = 0
    except ValueError:
        skip = 0

    # Get current user ID
    current_user_id = getattr(request, 'user_id', None)

    # Get posts that reference this corner
    posts = post_store.get_posts_by_corner(corner_obj, limit=limit, skip=skip)

    # Filter by visibility
    visible_posts = []
    for post in posts:
        if check_post_visibility(current_user_id, post, is_following_user):
            # Expand post data
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

            # Add corner information
            post_corners = []
            for corner_id in post.get('corner_ids', []):
                try:
                    corner_obj = ObjectId(corner_id) if isinstance(corner_id, str) else corner_id
                    corner = corner_store.get_corner_by_id(corner_obj)
                    if corner:
                        post_corners.append({
                            '_id': str(corner['_id']),
                            'name': corner.get('name', ''),
                            'location': corner.get('location', {})
                        })
                except Exception:
                    pass
            post_data['corners'] = post_corners

            # Add route if exists
            if 'route' in post and post['route']:
                route_data = post['route'].copy()
                route_data['corner_ids'] = [str(cid) for cid in route_data.get('corner_ids', [])]
                post_data['route'] = route_data

            visible_posts.append(post_data)

    # Get total count
    total = post_store.count_posts_by_corner(corner_obj)

    return jsonify({
        'success': True,
        'data': {
            'corner': {
                '_id': str(corner['_id']),
                'name': corner['name'],
                'location': corner['location']
            },
            'posts': visible_posts,
            'total': total,
            'limit': limit,
            'skip': skip
        }
    })


@bp.route('/api/corners/aggregate', methods=['GET'])
@jwt_optional
def get_corners_aggregate():
    """
    Get aggregate information for multiple corners, including post count, popularity, etc.

    Query parameters:
        - corner_ids: Comma-separated list of corner IDs (required)

    Returns:
        JSON with corners aggregate information
    """
    # Get corner_ids parameter
    corner_ids_str = request.args.get('corner_ids', '')
    if not corner_ids_str:
        return jsonify({'error': 'Missing corner_ids parameter'}), 400

    # Parse corner_ids
    corner_ids = [cid.strip() for cid in corner_ids_str.split(',') if cid.strip()]
    if not corner_ids:
        return jsonify({'error': 'No valid corner IDs provided'}), 400

    try:
        corner_id_objs = [ObjectId(cid) for cid in corner_ids]
    except Exception:
        return jsonify({'error': 'Invalid corner ID format'}), 400

    # Batch query corners
    corners = list(corner_store.collection.find({"_id": {"$in": corner_id_objs}}))

    if not corners:
        return jsonify({
            'success': True,
            'data': {
                'corners': []
            }
        })

    # Aggregate query for post statistics
    pipeline = [
        {
            "$match": {
                "corner_ids": {"$in": corner_id_objs},
                "visibility": {"$in": ["public", "followers"]}
            }
        },
        {
            "$unwind": "$corner_ids"
        },
        {
            "$group": {
                "_id": "$corner_ids",
                "post_count": {"$sum": 1},
                "total_likes": {"$sum": "$stats.likes_count"},
                "total_comments": {"$sum": "$stats.comments_count"}
            }
        }
    ]

    try:
        stats = list(post_store.collection.aggregate(pipeline))
    except Exception as e:
        return jsonify({'error': f'Failed to aggregate posts: {str(e)}'}), 500

    # Build stats map
    stats_map = {str(s['_id']): s for s in stats}

    # Query recent posts
    try:
        recent_posts = list(post_store.collection.find({
            "corner_ids": {"$in": corner_id_objs},
            "visibility": {"$in": ["public", "followers"]}
        }).sort("created_at", -1).limit(20))
    except Exception as e:
        recent_posts = []

    # Build corner_posts_map
    corner_posts_map = {}
    for post in recent_posts:
        for cid in post.get('corner_ids', []):
            cid_str = str(cid)
            if cid_str not in corner_posts_map:
                corner_posts_map[cid_str] = []
            if len(corner_posts_map[cid_str]) < 3:  # Keep only 3 recent posts per corner
                corner_posts_map[cid_str].append({
                    'post_id': str(post['_id']),
                    'title': post.get('title', ''),
                    'created_at': post.get('created_at')
                })

    # Build result
    result = []
    for corner in corners:
        cid_str = str(corner['_id'])
        stat = stats_map.get(cid_str, {'post_count': 0, 'total_likes': 0, 'total_comments': 0})

        result.append({
            'corner_id': cid_str,
            'name': corner.get('name', ''),
            'description': corner.get('description', ''),
            'location': corner.get('location', {}),
            'address': corner.get('address', ''),
            'post_count': stat['post_count'],
            'total_likes': stat['total_likes'],
            'total_comments': stat['total_comments'],
            'recent_posts': corner_posts_map.get(cid_str, [])
        })

    return jsonify({
        'success': True,
        'data': {
            'corners': result
        }
    })


@bp.route('/api/corners/search', methods=['GET'])
@jwt_optional
def search_corners():
    """
    Search corners by name, description, or tags.

    Query parameters:
        - q: Search keyword (required)
        - limit: Number of results to return (default 20)

    Returns:
        JSON with matching corners
    """
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'error': 'Missing search query'}), 400

    try:
        limit = int(request.args.get('limit', 20))
        limit = min(limit, 100)
    except ValueError:
        limit = 20

    # Use regex for fuzzy search on name, description, and tags
    import re
    regex = re.compile(query, re.IGNORECASE)

    try:
        corners = list(corner_store.collection.find({
            "$or": [
                {"name": regex},
                {"description": regex},
                {"tags": regex}
            ]
        }).limit(limit))
    except Exception as e:
        return jsonify({'error': f'Failed to search corners: {str(e)}'}), 500

    # Convert to response format
    result = []
    for corner in corners:
        result.append({
            '_id': str(corner['_id']),
            'name': corner.get('name', ''),
            'description': corner.get('description', ''),
            'location': corner.get('location', {}),
            'address': corner.get('address', ''),
            'images': [str(img_id) for img_id in corner.get('images', [])],  # Convert ObjectIds to strings
            'tags': corner.get('tags', []),
            'created_at': corner.get('created_at')
        })

    return jsonify({
        'success': True,
        'data': {
            'corners': result,
            'total': len(result)
        }
    })


@bp.route('/api/corners/hot', methods=['GET'])
@jwt_optional
def get_hot_corners():
    """
    Get hot/popular corners sorted by activity.

    Corners are ranked by:
    1. Post count (primary)
    2. Total likes and comments (secondary)
    3. Recent activity (within 7 days)

    Query parameters:
        - lat: User's current latitude (optional, for distance calculation)
        - lng: User's current longitude (optional, for distance calculation)
        - limit: Number of results to return (default 20)
        - radius: Filter by radius in meters (optional)

    Returns:
        JSON with hot corners list
    """
    # Get parameters
    try:
        limit = int(request.args.get('limit', 20))
        limit = min(limit, 50)
    except ValueError:
        limit = 20

    user_location = None
    lat = request.args.get('lat')
    lng = request.args.get('lng')
    radius = request.args.get('radius')

    if lat and lng:
        try:
            user_location = (float(lat), float(lng))
        except ValueError:
            pass

    if radius:
        try:
            radius = int(radius)
        except ValueError:
            radius = None

    # Aggregate pipeline to calculate popularity
    from datetime import datetime, timedelta

    # Calculate date 7 days ago
    seven_days_ago = datetime.utcnow() - timedelta(days=7)

    pipeline = [
        # Match public and followers-visible posts
        {
            "$match": {
                "visibility": {"$in": ["public", "followers"]},
                "corner_ids": {"$exists": True, "$ne": []}
            }
        },
        # Unwind corner_ids to get one document per corner
        {
            "$unwind": "$corner_ids"
        },
        # Group by corner and calculate metrics
        {
            "$group": {
                "_id": "$corner_ids",
                "post_count": {"$sum": 1},
                "total_likes": {"$sum": "$stats.likes_count"},
                "total_comments": {"$sum": "$stats.comments_count"},
                "recent_posts": {
                    "$sum": {
                        "$cond": [
                            {"$gte": ["$created_at", seven_days_ago.isoformat()]},
                            1,
                            0
                        ]
                    }
                }
            }
        },
        # Calculate popularity score
        # Score = post_count * 10 + total_likes + total_comments * 2 + recent_posts * 5
        {
            "$addFields": {
                "popularity_score": {
                    "$add": [
                        {"$multiply": ["$post_count", 10]},
                        "$total_likes",
                        {"$multiply": ["$total_comments", 2]},
                        {"$multiply": ["$recent_posts", 5]}
                    ]
                }
            }
        },
        # Sort by popularity score
        {
            "$sort": {"popularity_score": -1}
        },
        # Limit results
        {
            "$limit": limit * 2  # Get more for filtering
        }
    ]

    try:
        popularity_stats = list(post_store.collection.aggregate(pipeline))
    except Exception as e:
        return jsonify({'error': f'Failed to calculate popularity: {str(e)}'}), 500

    # Get corner details and build result
    result = []
    for stat in popularity_stats:
        corner_id = stat['_id']
        corner = corner_store.get_corner_by_id(corner_id)

        if not corner:
            continue

        # Calculate distance if user location provided
        distance = None
        if user_location and 'location' in corner:
            distance = corner_store.calculate_distance(
                user_location[0], user_location[1],
                corner['location']['coordinates'][1],
                corner['location']['coordinates'][0]
            )
            # Filter by radius if specified
            if radius and distance > radius:
                continue

        corner_data = {
            '_id': str(corner['_id']),
            'name': corner.get('name', ''),
            'description': corner.get('description', ''),
            'location': corner.get('location', {}),
            'address': corner.get('address', ''),
            'images': [str(img_id) for img_id in corner.get('images', [])],
            'tags': corner.get('tags', []),
            'post_count': stat['post_count'],
            'total_likes': stat['total_likes'],
            'total_comments': stat['total_comments'],
            'recent_posts': stat['recent_posts'],
            'popularity_score': stat['popularity_score'],
            'distance': round(distance, 2) if distance else None
        }
        result.append(corner_data)

        if len(result) >= limit:
            break

    return jsonify({
        'success': True,
        'data': {
            'corners': result,
            'total': len(result)
        }
    })
