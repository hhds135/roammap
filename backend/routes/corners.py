"""Corner management endpoints."""
import os
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

from models import (
    load_corners, save_corners, find_user_by_id,
    can_access_corner, is_friend
)
from utils import jwt_required, jwt_optional, allowed_file
from config import Config

bp = Blueprint('corners', __name__)


@bp.route('/api/corners', methods=['GET'])
@jwt_optional
def get_corners():
    """Get list of corners with optional filtering."""
    corners = load_corners()

    # Get current user ID (from JWT or query param)
    current_user_id = None
    if hasattr(request, 'user_id'):
        current_user_id = request.user_id
    else:
        current_user_id = request.args.get('user_id')

    # Filter by privacy
    filtered_corners = []
    for corner in corners:
        if can_access_corner(current_user_id, corner):
            filtered_corners.append(corner)
    corners = filtered_corners

    # Get query params
    tags = request.args.get('tags')
    search = request.args.get('search')

    # Filter by tags
    if tags:
        tag_list = [t.strip() for t in tags.split(',') if t.strip()]
        if tag_list:
            corners = [c for c in corners if
                      any(tag in c.get('tags', []) for tag in tag_list)]

    # Text search
    if search:
        search_lower = search.lower()
        corners = [c for c in corners if
                  search_lower in c.get('title', '').lower() or
                  search_lower in c.get('description', '').lower() or
                  search_lower in c.get('address', '').lower()]

    # Sort by created_at descending
    corners.sort(key=lambda x: x.get('created_at', ''), reverse=True)

    # Process corners to ensure likes count matches liked_users length
    for corner in corners:
        corner['likes'] = len(corner.get('liked_users', []))

    return jsonify({'corners': corners})


@bp.route('/api/corners', methods=['POST'])
@jwt_required
def create_corner():
    """Create a new corner."""
    if 'image' not in request.files:
        return jsonify({'error': 'Image required'}), 400

    file = request.files['image']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid image file'}), 400

    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    address = request.form.get('address', '').strip()
    tags = request.form.get('tags', '').strip()

    user_id = request.user_id

    if not all([title, description, latitude, longitude]):
        return jsonify({'error': 'All required fields must be filled'}), 400

    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except ValueError:
        return jsonify({'error': 'Invalid coordinates'}), 400

    # Save image
    filename = secure_filename(file.filename)
    file_ext = filename.rsplit('.', 1)[1].lower()
    new_filename = f"{uuid.uuid4().hex}.{file_ext}"
    file_path = os.path.join(Config.UPLOAD_FOLDER, new_filename)
    file.save(file_path)

    visibility = request.form.get('visibility', 'public')
    specific_friends = request.form.get('specific_friends', '').split(',') if request.form.get('specific_friends') else []
    exclude_friends = request.form.get('exclude_friends', '').split(',') if request.form.get('exclude_friends') else []

    specific_friends = [friend.strip() for friend in specific_friends if friend.strip()]
    exclude_friends = [friend.strip() for friend in exclude_friends if friend.strip()]

    # Create new corner
    corners = load_corners()
    new_corner = {
        'id': str(uuid.uuid4()),
        'share_id': str(uuid.uuid4()),
        'title': title,
        'description': description,
        'latitude': latitude,
        'longitude': longitude,
        'address': address,
        'tags': [tag.strip() for tag in tags.split(',') if tag.strip()],
        'image_url': f'/uploads/{new_filename}',
        'user_id': user_id,
        'created_at': datetime.now().isoformat(),
        'visibility': visibility,
        'specific_friends': specific_friends,
        'exclude_friends': exclude_friends,
        'liked_users': [],
        'favorited_users': [],
        'comments': []
    }

    corners.append(new_corner)
    save_corners(corners)

    return jsonify({'message': 'Corner created', 'corner': new_corner}), 201


@bp.route('/api/corners/<corner_id>', methods=['GET'])
def get_corner_detail(corner_id):
    """Get corner detail by ID."""
    corners = load_corners()
    corner = next((c for c in corners if c['id'] == corner_id), None)

    if not corner:
        return jsonify({'error': 'Corner not found'}), 404

    user_id = request.args.get('user_id')

    if not can_access_corner(user_id, corner):
        return jsonify({'error': 'Access denied'}), 403

    is_liked = False
    is_favorited = False

    if user_id:
        if 'liked_users' in corner:
            is_liked = user_id in corner['liked_users']
        if 'favorited_users' in corner:
            is_favorited = user_id in corner['favorited_users']

    corner_data = corner.copy()
    corner_data['likes'] = len(corner.get('liked_users', []))

    return jsonify({
        'corner': corner_data,
        'is_liked': is_liked,
        'is_favorited': is_favorited
    })


@bp.route('/api/corners/<corner_id>', methods=['PUT'])
@jwt_required
def update_corner(corner_id):
    """Update a corner."""
    user_id = request.user_id

    corners = load_corners()
    corner_index = next((i for i, c in enumerate(corners) if c['id'] == corner_id), -1)

    if corner_index == -1:
        return jsonify({'error': 'Corner not found'}), 404

    if corners[corner_index]['user_id'] != user_id:
        return jsonify({'error': 'Access denied'}), 403

    # Get form data
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    address = request.form.get('address', '').strip()
    tags = request.form.get('tags', '').strip()
    visibility = request.form.get('visibility', 'public')
    specific_friends = request.form.get('specific_friends', '').split(',') if request.form.get('specific_friends') else []
    exclude_friends = request.form.get('exclude_friends', '').split(',') if request.form.get('exclude_friends') else []

    # Clean empty values
    specific_friends = [friend.strip() for friend in specific_friends if friend.strip()]
    exclude_friends = [friend.strip() for friend in exclude_friends if friend.strip()]

    if not all([title, description, latitude, longitude]):
        return jsonify({'error': 'All required fields must be filled'}), 400

    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except ValueError:
        return jsonify({'error': 'Invalid coordinates'}), 400

    corner = corners[corner_index]
    corner['title'] = title
    corner['description'] = description
    corner['latitude'] = latitude
    corner['longitude'] = longitude
    corner['address'] = address
    corner['tags'] = [tag.strip() for tag in tags.split(',') if tag.strip()]
    corner['visibility'] = visibility
    corner['specific_friends'] = specific_friends
    corner['exclude_friends'] = exclude_friends

    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_ext = filename.rsplit('.', 1)[1].lower()
            new_filename = f"{uuid.uuid4().hex}.{file_ext}"
            file_path = os.path.join(Config.UPLOAD_FOLDER, new_filename)
            file.save(file_path)
            corner['image_url'] = f'/uploads/{new_filename}'

    save_corners(corners)

    return jsonify({'message': 'Corner updated', 'corner': corner}), 200


@bp.route('/api/corners/<corner_id>', methods=['DELETE'])
@jwt_required
def delete_corner(corner_id):
    """Delete a corner."""
    user_id = request.user_id

    corners = load_corners()
    corner_index = next((i for i, c in enumerate(corners) if c['id'] == corner_id), -1)

    if corner_index == -1:
        return jsonify({'error': 'Corner not found'}), 404

    if corners[corner_index]['user_id'] != user_id:
        return jsonify({'error': 'Access denied'}), 403

    corners.pop(corner_index)
    save_corners(corners)

    return jsonify({'message': 'Corner deleted'}), 200


@bp.route('/api/tags', methods=['GET'])
def get_tags():
    """Get preset tags."""
    preset_tags = Config.PRESET_TAGS

    # Get search param
    search_query = request.args.get('q', '').strip()

    # Filter tags if search query provided
    if search_query:
        filtered_tags = [tag for tag in preset_tags if search_query.lower() in tag.lower()]
        return jsonify({'tags': sorted(filtered_tags)})

    return jsonify({'tags': sorted(preset_tags)})


@bp.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files."""
    return send_from_directory(Config.UPLOAD_FOLDER, filename)
