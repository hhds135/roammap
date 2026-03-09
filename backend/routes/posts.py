"""Post management endpoints."""
from datetime import datetime
from flask import Blueprint, request, jsonify
from bson import ObjectId

from storage.post_store import PostStore
from storage.media_store import MediaStore
from storage.corner_store import CornerStore
from storage.user_store import UserStore
from storage.connection import MongoDBConnection, get_db
from utils import jwt_required, jwt_optional, check_post_visibility, is_following_user
from config import Config

bp = Blueprint('posts', __name__)

# Initialize MongoDB connection if not already connected
try:
    if get_db() is None:
        conn = MongoDBConnection()
        conn.connect()
except Exception:
    pass

post_store = PostStore()
media_store = MediaStore(bucket_name="media")
corner_store = CornerStore()
user_store = UserStore()


def validate_post_data(data, is_update=False):
    """
    Validate post creation/update data.
    
    Args:
        data: Request JSON data
        is_update: Whether this is an update operation
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not is_update:
        # Required fields for creation
        required_fields = ['title', 'media_type', 'media_files']
        for field in required_fields:
            if field not in data:
                return False, f'Missing required field: {field}'
    
    # Validate media_type
    if 'media_type' in data:
        if data['media_type'] not in ['image', 'video']:
            return False, 'media_type must be "image" or "video"'
    
    # Validate media_files
    if 'media_files' in data:
        if not isinstance(data['media_files'], list):
            return False, 'media_files must be an array'
    
    # Validate visibility
    if 'visibility' in data:
        if data['visibility'] not in ['public', 'private', 'followers']:
            return False, 'visibility must be "public", "private", or "followers"'
    
    # Validate corner_ids
    if 'corner_ids' in data:
        if not isinstance(data['corner_ids'], list):
            return False, 'corner_ids must be an array'
    
    # Validate tags
    if 'tags' in data:
        if not isinstance(data['tags'], list):
            return False, 'tags must be an array'
    
    return True, None


def validate_media_files_exist(media_file_ids):
    """
    Validate that all media files exist in GridFS.
    
    Args:
        media_file_ids: List of file ObjectIds
        
    Returns:
        tuple: (all_exist, missing_id)
    """
    for file_id in media_file_ids:
        try:
            file_obj = ObjectId(file_id) if isinstance(file_id, str) else file_id
        except Exception:
            return False, str(file_id)
        
        file_doc = media_store.get_file(file_obj)
        if not file_doc:
            return False, str(file_id)
    
    return True, None


def validate_corners_exist(corner_ids):
    """
    Validate that all corners exist.
    
    Args:
        corner_ids: List of corner ObjectIds
        
    Returns:
        tuple: (all_exist, missing_id)
    """
    for corner_id in corner_ids:
        try:
            corner_obj = ObjectId(corner_id) if isinstance(corner_id, str) else corner_id
        except Exception:
            return False, str(corner_id)
        
        corner = corner_store.get_corner_by_id(corner_obj)
        if not corner:
            return False, str(corner_id)
    
    return True, None


def expand_post_data(post):
    """
    Expand post data with related information.
    
    Args:
        post: Post document
        
    Returns:
        dict: Expanded post data
    """
    if not post:
        return None
    
    expanded = dict(post)
    expanded['_id'] = str(post['_id'])
    expanded['user_id'] = str(post['user_id'])
    
    # Get creator info
    creator = user_store.get_user_by_id(post['user_id'])
    if creator:
        expanded['username'] = creator.get('username', '')
    
    # Expand corner_ids to include corner details
    corners = []
    for corner_id in post.get('corner_ids', []):
        try:
            corner_obj = ObjectId(corner_id) if isinstance(corner_id, str) else corner_id
            corner = corner_store.get_corner_by_id(corner_obj)
            if corner:
                corners.append({
                    '_id': str(corner['_id']),
                    'name': corner.get('name', ''),
                    'location': corner.get('location', {})
                })
        except Exception:
            pass
    expanded['corners'] = corners
    
    # Generate media URLs
    media_urls = []
    for file_id in post.get('media_files', []):
        media_urls.append(f'/api/media/{str(file_id)}')
    expanded['media_urls'] = media_urls
    
    # Convert ObjectIds to strings
    expanded['corner_ids'] = [str(cid) for cid in post.get('corner_ids', [])]
    expanded['media_files'] = [str(fid) for fid in post.get('media_files', [])]
    
    return expanded


@bp.route('/api/posts', methods=['POST'])
@jwt_required
def create_post():
    """
    Create a new post.
    
    Request body:
        - title: Post title (required)
        - description: Post description (optional)
        - corner_ids: List of corner IDs (optional)
        - media_type: "image" or "video" (required)
        - media_files: List of GridFS file IDs (required)
        - tags: List of tags (optional)
        - visibility: "public", "private", or "followers" (optional, default "public")
        - route: Route object with route_name and corner_ids (optional)
        
    Returns:
        JSON with created post data
    """
    user_id = request.user_id
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Request body is required'}), 400
    
    # Validate post data
    is_valid, error = validate_post_data(data)
    if not is_valid:
        return jsonify({'error': error}), 400
    
    # Validate media files exist
    media_file_ids = data.get('media_files', [])
    if media_file_ids:
        all_exist, missing_id = validate_media_files_exist(media_file_ids)
        if not all_exist:
            return jsonify({'error': f'Media file not found: {missing_id}'}), 404
    
    # Validate corners exist
    corner_ids = data.get('corner_ids', [])
    if corner_ids:
        all_exist, missing_id = validate_corners_exist(corner_ids)
        if not all_exist:
            return jsonify({'error': f'Corner not found: {missing_id}'}), 404
    
    # Validate route if provided
    route = data.get('route')
    if route:
        route_corner_ids = route.get('corner_ids', [])
        if not isinstance(route_corner_ids, list):
            return jsonify({'error': 'route.corner_ids must be an array'}), 400

        # Validate route corners are in main corner_ids
        for route_corner_id in route_corner_ids:
            if route_corner_id not in corner_ids:
                return jsonify({
                    'error': f'Route corner {route_corner_id} must be in corner_ids'
                }), 400

        # Add created_at to route
        route['created_at'] = datetime.utcnow().isoformat()

    # Convert IDs to appropriate types
    # Note: user_id from JWT is already a string (ObjectId hex string)
    media_file_objs = []
    corner_id_objs = []
    
    try:
        # User ID, media files, and corners all use ObjectId
        user_id_obj = ObjectId(user_id)
        media_file_objs = [ObjectId(fid) for fid in media_file_ids]
        corner_id_objs = [ObjectId(cid) for cid in corner_ids] if corner_ids else []

        if route and route.get('corner_ids'):
            route['corner_ids'] = [ObjectId(cid) for cid in route['corner_ids']]
    except Exception as e:
        return jsonify({'error': f'Invalid ID format: {str(e)}'}), 400

    # Create post
    try:
        post_id = post_store.create_post(
            user_id=user_id_obj,
            title=data['title'],
            description=data.get('description', ''),
            corner_ids=corner_id_objs,
            media_type=data['media_type'],
            media_files=media_file_objs,
            tags=data.get('tags', []),
            visibility=data.get('visibility', 'public'),
            route=route
        )
    except Exception as e:
        return jsonify({'error': f'Failed to create post: {str(e)}'}), 500
    
    # Get created post
    post = post_store.get_post_by_id(post_id)
    if not post:
        return jsonify({'error': 'Post created but not found'}), 500
    
    expanded_post = expand_post_data(post)
    
    return jsonify({
        'success': True,
        'data': expanded_post
    }), 201


@bp.route('/api/posts/<post_id>', methods=['GET'])
@jwt_optional
def get_post(post_id):
    """
    Get a post by ID.
    
    Args:
        post_id: Post ObjectId
        
    Returns:
        JSON with post data (if user has permission)
    """
    try:
        post_obj = ObjectId(post_id)
    except Exception:
        return jsonify({'error': 'Invalid post ID'}), 400
    
    # Get post
    post = post_store.get_post_by_id(post_obj)
    if not post:
        return jsonify({'error': 'Post not found'}), 404
    
    # Get current user ID (may be None if not logged in)
    current_user_id = getattr(request, 'user_id', None)
    
    # Check visibility
    if not check_post_visibility(current_user_id, post, is_following_user):
        return jsonify({'error': 'Access denied'}), 403
    
    expanded_post = expand_post_data(post)
    
    return jsonify({
        'success': True,
        'data': expanded_post
    })


@bp.route('/api/posts/<post_id>', methods=['PUT'])
@jwt_required
def update_post(post_id):
    """
    Update a post.
    
    Only the post creator can update the post.
    Only certain fields can be updated: title, description, tags, visibility
    
    Args:
        post_id: Post ObjectId
        
    Request body:
        - title: New title (optional)
        - description: New description (optional)
        - tags: New tags (optional)
        - visibility: New visibility (optional)
        
    Returns:
        JSON with updated post data
    """
    user_id = request.user_id
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Request body is required'}), 400
    
    try:
        post_obj = ObjectId(post_id)
        user_id_obj = ObjectId(user_id)
    except Exception:
        return jsonify({'error': 'Invalid ID format'}), 400
    
    # Get post
    post = post_store.get_post_by_id(post_obj)
    if not post:
        return jsonify({'error': 'Post not found'}), 404
    
    # Check if user is the creator
    if str(post['user_id']) != user_id:
        return jsonify({'error': 'Access denied. Only the creator can update the post'}), 403
    
    # Validate update data
    is_valid, error = validate_post_data(data, is_update=True)
    if not is_valid:
        return jsonify({'error': error}), 400
    
    # Build update object (only allowed fields)
    allowed_fields = ['title', 'description', 'tags', 'visibility']
    updates = {}
    for field in allowed_fields:
        if field in data:
            updates[field] = data[field]
    
    # Add updated_at timestamp
    updates['updated_at'] = datetime.utcnow().isoformat()
    
    # Update post
    try:
        if not post_store.update_post(post_obj, updates):
            return jsonify({'error': 'Failed to update post'}), 500
    except Exception as e:
        return jsonify({'error': f'Failed to update post: {str(e)}'}), 500
    
    # Get updated post
    updated_post = post_store.get_post_by_id(post_obj)
    expanded_post = expand_post_data(updated_post)
    
    return jsonify({
        'success': True,
        'data': expanded_post
    })


@bp.route('/api/posts/<post_id>', methods=['DELETE'])
@jwt_required
def delete_post(post_id):
    """
    Delete a post and its associated media files.
    
    Args:
        post_id: Post ObjectId
        
    Returns:
        Success message
    """
    user_id = request.user_id
    
    try:
        post_obj = ObjectId(post_id)
    except Exception:
        return jsonify({'error': 'Invalid post ID'}), 400
    
    # Get post
    post = post_store.get_post_by_id(post_obj)
    if not post:
        return jsonify({'error': 'Post not found'}), 404
    
    # Check if user is the creator
    if str(post['user_id']) != user_id:
        return jsonify({'error': 'Access denied. Only the creator can delete the post'}), 403
    
    # Get media file IDs to delete
    media_file_ids = post.get('media_files', [])
    
    # Delete post
    try:
        if not post_store.delete_post(post_obj):
            return jsonify({'error': 'Failed to delete post'}), 500
    except Exception as e:
        return jsonify({'error': f'Failed to delete post: {str(e)}'}), 500
    
    # Delete associated media files
    for file_id in media_file_ids:
        try:
            file_obj = ObjectId(file_id)
            media_store.delete_file(file_obj)
        except Exception:
            pass  # Continue even if some files fail to delete
    
    return jsonify({
        'success': True,
        'message': 'Post deleted successfully'
    })


@bp.route('/api/posts', methods=['GET'])
@jwt_optional
def get_posts():
    """
    Get list of posts with pagination and filtering.
    
    Query parameters:
        - user_id: Filter by user ID (optional)
        - visibility: Filter by visibility (optional)
        - tag: Filter by tag (optional)
        - limit: Number of results per page (default 20, max 100)
        - skip: Number of results to skip (default 0)
        - sort_by: Sort field (default "created_at")
        - order: Sort order "asc" or "desc" (default "desc")
        
    Returns:
        JSON with posts list and pagination info
    """
    # Get query parameters
    filter_user_id = request.args.get('user_id')
    filter_visibility = request.args.get('visibility')
    filter_tag = request.args.get('tag')
    
    try:
        limit = int(request.args.get('limit', 20))
        limit = min(limit, 100)  # Max 100
    except ValueError:
        limit = 20
    
    try:
        skip = int(request.args.get('skip', 0))
        if skip < 0:
            skip = 0
    except ValueError:
        skip = 0
    
    sort_by = request.args.get('sort_by', 'created_at')
    order = request.args.get('order', 'desc')
    sort_order = -1 if order.lower() == 'desc' else 1
    
    # Build query
    query = {}
    
    # Filter by user_id
    if filter_user_id:
        try:
            query['user_id'] = ObjectId(filter_user_id)
        except Exception:
            return jsonify({'error': 'Invalid user_id format'}), 400
    
    # Filter by visibility
    if filter_visibility:
        if filter_visibility not in ['public', 'private', 'followers']:
            return jsonify({'error': 'Invalid visibility value'}), 400
        query['visibility'] = filter_visibility
    
    # Filter by tag
    if filter_tag:
        query['tags'] = filter_tag
    
    # Get current user for visibility filtering
    current_user_id = getattr(request, 'user_id', None)
    
    # Get posts
    try:
        sort_field = sort_by if sort_by in ['created_at', 'updated_at', 'title'] else 'created_at'
        posts = post_store.find(
            query,
            limit=limit,
            skip=skip,
            sort=[(sort_field, sort_order)]
        )
        
        # Get total count
        total = post_store.collection.count_documents(query)
    except Exception as e:
        return jsonify({'error': f'Failed to get posts: {str(e)}'}), 500
    
    # Filter posts by visibility for current user
    filtered_posts = []
    for post in posts:
        if check_post_visibility(current_user_id, post, is_following_user):
            filtered_posts.append(expand_post_data(post))
    
    return jsonify({
        'success': True,
        'data': {
            'posts': filtered_posts,
            'total': total,
            'limit': limit,
            'skip': skip
        }
    })


@bp.route('/api/posts/user/<user_id>', methods=['GET'])
@jwt_optional
def get_posts_by_user(user_id):
    """
    Get all posts by a specific user.
    
    Args:
        user_id: User ObjectId
        
    Query parameters:
        - limit: Number of results per page (default 20)
        - skip: Number of results to skip (default 0)
        
    Returns:
        JSON with posts list
    """
    try:
        user_id_obj = ObjectId(user_id)
    except Exception:
        return jsonify({'error': 'Invalid user ID'}), 400
    
    # Get query parameters
    try:
        limit = int(request.args.get('limit', 20))
        limit = min(limit, 100)
    except ValueError:
        limit = 20
    
    try:
        skip = int(request.args.get('skip', 0))
    except ValueError:
        skip = 0
    
    # Get current user for visibility filtering
    current_user_id = getattr(request, 'user_id', None)
    
    # Get posts
    posts = post_store.get_posts_by_user(
        user_id_obj,
        limit=limit,
        skip=skip
    )
    
    # Filter by visibility
    filtered_posts = []
    for post in posts:
        if check_post_visibility(current_user_id, post, is_following_user):
            filtered_posts.append(expand_post_data(post))
    
    return jsonify({
        'success': True,
        'data': {
            'posts': filtered_posts,
            'total': len(filtered_posts)
        }
    })
