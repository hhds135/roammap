"""Sharing functionality endpoints."""
import uuid
from flask import Blueprint, request, jsonify

from models import load_corners, save_corners
from utils import jwt_required

bp = Blueprint('sharing', __name__)


@bp.route('/api/share/<share_id>', methods=['GET'])
def get_shared_corner(share_id):
    """Get corner by share ID without authentication."""
    corners = load_corners()
    corner = next((c for c in corners if c.get('share_id') == share_id), None)

    if not corner:
        return jsonify({'error': 'Invalid or expired share link'}), 404

    corner_data = corner.copy()
    corner_data['likes'] = len(corner.get('liked_users', []))
    if 'share_id' in corner_data:
        del corner_data['share_id']

    return jsonify({'corner': corner_data})


@bp.route('/api/corners/<corner_id>/share-link', methods=['POST'])
@jwt_required
def generate_share_link(corner_id):
    """Generate or reset share link for a corner."""
    user_id = request.user_id

    corners = load_corners()
    corner = next((c for c in corners if c['id'] == corner_id), None)

    if not corner:
        return jsonify({'error': 'Corner not found'}), 404

    if corner['user_id'] != user_id:
        return jsonify({'error': 'Access denied'}), 403

    corner['share_id'] = str(uuid.uuid4())
    save_corners(corners)

    share_link = f"/share/{corner['share_id']}"
    return jsonify({
        'message': 'Share link generated',
        'share_link': share_link,
        'share_id': corner['share_id']
    })
