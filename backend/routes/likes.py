"""Like functionality endpoints."""
from flask import Blueprint, request, jsonify

from models import load_corners, save_corners
from utils import jwt_required

bp = Blueprint('likes', __name__)


@bp.route('/api/corners/<corner_id>/like', methods=['POST'])
@jwt_required
def like_corner(corner_id):
    """Like or unlike a corner."""
    user_id = request.user_id

    corners = load_corners()
    corner = next((c for c in corners if c['id'] == corner_id), None)

    if not corner:
        return jsonify({'error': 'Corner not found'}), 404

    if 'liked_users' not in corner:
        corner['liked_users'] = []

    if user_id in corner['liked_users']:
        corner['liked_users'].remove(user_id)
        message = 'Unliked'
        is_liked = False
    else:
        corner['liked_users'].append(user_id)
        message = 'Liked'
        is_liked = True

    save_corners(corners)

    return jsonify({
        'message': message,
        'likes': len(corner['liked_users']),
        'is_liked': is_liked
    })
