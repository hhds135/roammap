"""Favorite functionality endpoints."""
from flask import Blueprint, request, jsonify

from models import load_corners, save_corners, find_user_by_id, can_access_corner
from utils import jwt_required

bp = Blueprint('favorites', __name__)


@bp.route('/api/corners/<corner_id>/favorite', methods=['POST'])
@jwt_required
def favorite_corner(corner_id):
    """Favorite or unfavorite a corner."""
    user_id = request.user_id

    corners = load_corners()
    corner = next((c for c in corners if c['id'] == corner_id), None)

    if not corner:
        return jsonify({'error': 'Corner not found'}), 404

    if 'favorited_users' not in corner:
        corner['favorited_users'] = []

    if user_id in corner['favorited_users']:
        corner['favorited_users'].remove(user_id)
        message = 'Unfavorited'
        is_favorited = False
    else:
        corner['favorited_users'].append(user_id)
        message = 'Favorited'
        is_favorited = True

    save_corners(corners)

    return jsonify({
        'message': message,
        'favorites_count': len(corner['favorited_users']),
        'is_favorited': is_favorited
    })


@bp.route('/api/users/<user_id>/favorites', methods=['GET'])
def get_user_favorites(user_id):
    """Get user's favorite corners."""
    if not find_user_by_id(user_id):
        return jsonify({'error': 'User not found'}), 404

    corners = load_corners()
    favorited_corners = []
    for corner in corners:
        is_favorited = 'favorited_users' in corner and user_id in corner['favorited_users']
        can_see = can_access_corner(user_id, corner)

        if is_favorited and can_see:
            favorited_corners.append(corner)

    return jsonify({
        'corners': favorited_corners,
        'count': len(favorited_corners)
    })
