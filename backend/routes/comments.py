"""Comment functionality endpoints."""
from datetime import datetime
import uuid
from flask import Blueprint, request, jsonify

from models import load_corners, save_corners, find_user_by_id
from utils import jwt_required

bp = Blueprint('comments', __name__)


@bp.route('/api/corners/<corner_id>/comment', methods=['POST'])
@jwt_required
def add_comment(corner_id):
    """Add a comment to a corner."""
    data = request.get_json()

    user_id = request.user_id

    if not data or not data.get('content'):
        return jsonify({'error': 'Comment content required'}), 400

    content = data['content'].strip()

    if len(content) == 0:
        return jsonify({'error': 'Comment content required'}), 400

    user = find_user_by_id(user_id)

    corners = load_corners()
    corner = next((c for c in corners if c['id'] == corner_id), None)

    if not corner:
        return jsonify({'error': 'Corner not found'}), 404

    if 'comments' not in corner:
        corner['comments'] = []

    new_comment = {
        'id': str(uuid.uuid4()),
        'user_id': user_id,
        'username': user['username'],
        'content': content,
        'created_at': datetime.now().isoformat()
    }

    corner['comments'].append(new_comment)
    save_corners(corners)

    return jsonify({'message': 'Comment added', 'comment': new_comment}), 201


@bp.route('/api/corners/<corner_id>/comments/<comment_id>', methods=['DELETE'])
@jwt_required
def delete_comment(corner_id, comment_id):
    """Delete a comment."""
    user_id = request.user_id

    corners = load_corners()
    corner = next((c for c in corners if c['id'] == corner_id), None)

    if not corner:
        return jsonify({'error': 'Corner not found'}), 404

    comments = corner.get('comments', [])
    comment_index = next((i for i, c in enumerate(comments) if c['id'] == comment_id), -1)

    if comment_index == -1:
        return jsonify({'error': 'Comment not found'}), 404

    if comments[comment_index]['user_id'] != user_id:
        return jsonify({'error': 'Access denied'}), 403

    comments.pop(comment_index)
    save_corners(corners)

    return jsonify({'message': 'Comment deleted'}), 200
