"""Friend system endpoints."""
from flask import Blueprint, request, jsonify

from models import (
    load_users, find_user_by_id, find_user_by_username,
    add_friend_request, accept_friend_request, reject_friend_request,
    remove_friend, get_friend_requests, is_friend, can_access_corner,
    get_user_friends
)
from utils import jwt_required

bp = Blueprint('friends', __name__)


@bp.route('/api/users/search', methods=['GET'])
@jwt_required
def search_users():
    """Search users by username."""
    query = request.args.get('q', '').strip()
    current_user_id = request.user_id

    if not query:
        return jsonify({'error': 'Search query required'}), 400

    users = load_users()
    results = []

    for user in users:
        if user['id'] == current_user_id:
            continue

        if query.lower() in user['username'].lower():
            is_friend_status = current_user_id in user.get('friends', [])

            has_pending_request = False
            friend_requests = user.get('friend_requests', [])
            if current_user_id in friend_requests:
                has_pending_request = True

            results.append({
                'id': user['id'],
                'username': user['username'],
                'is_friend': is_friend_status,
                'has_pending_request': has_pending_request
            })

    return jsonify({'users': results})


@bp.route('/api/friends/request', methods=['POST'])
@jwt_required
def send_friend_request():
    """Send a friend request."""
    data = request.get_json()
    sender_id = request.user_id
    receiver_id = data.get('receiver_id')

    if not receiver_id:
        return jsonify({'error': 'Receiver ID required'}), 400

    if sender_id == receiver_id:
        return jsonify({'error': 'Cannot send friend request to self'}), 400

    success, message = add_friend_request(sender_id, receiver_id)
    if not success:
        return jsonify({'error': message}), 400

    return jsonify({'message': message})


@bp.route('/api/friends/request/<sender_id>', methods=['PUT'])
@jwt_required
def handle_friend_request(sender_id):
    """Handle friend request (accept/reject)."""
    data = request.get_json()
    receiver_id = request.user_id
    action = data.get('action')

    if action not in ['accept', 'reject']:
        return jsonify({'error': 'Invalid action'}), 400

    if action == 'accept':
        success, message = accept_friend_request(receiver_id, sender_id)
    else:
        success, message = reject_friend_request(receiver_id, sender_id)

    if not success:
        return jsonify({'error': message}), 400

    return jsonify({'message': message})


@bp.route('/api/friends', methods=['GET'])
@jwt_required
def get_friends():
    """Get user's friend list."""
    user_id = request.user_id

    users = load_users()
    friends = []

    current_user = find_user_by_id(user_id)
    if not current_user:
        return jsonify({'error': 'User not found'}), 404

    friend_ids = current_user.get('friends', [])

    for user in users:
        if user['id'] in friend_ids:
            friends.append({
                'id': user['id'],
                'username': user['username']
            })

    return jsonify({'friends': friends})


@bp.route('/api/friends/requests', methods=['GET'])
@jwt_required
def get_friend_requests_list():
    """Get friend request list."""
    user_id = request.user_id

    users = load_users()
    requests = []

    current_user = find_user_by_id(user_id)
    if not current_user:
        return jsonify({'error': 'User not found'}), 404

    request_ids = current_user.get('friend_requests', [])

    for user in users:
        if user['id'] in request_ids:
            requests.append({
                'id': user['id'],
                'username': user['username']
            })

    return jsonify({'requests': requests})


@bp.route('/api/friends/<friend_id>', methods=['DELETE'])
@jwt_required
def delete_friend(friend_id):
    """Delete a friend."""
    user_id = request.user_id

    success, message = remove_friend(user_id, friend_id)
    if not success:
        return jsonify({'error': message}), 400

    return jsonify({'message': message})


@bp.route('/api/friends/<friend_id>/corners', methods=['GET'])
@jwt_required
def get_friend_corners(friend_id):
    """Get friend's corners that are visible to current user."""
    current_user_id = request.user_id

    friend = find_user_by_id(friend_id)
    if not friend:
        return jsonify({'error': 'User not found'}), 404

    if not is_friend(current_user_id, friend_id):
        return jsonify({'error': 'Friends only'}), 403

    corners = load_corners()

    friend_corners = []
    for corner in corners:
        if corner.get('user_id') == friend_id:
            if can_access_corner(current_user_id, corner):
                friend_corners.append(corner)

    friend_corners.sort(key=lambda x: x.get('created_at', ''), reverse=True)

    for corner in friend_corners:
        corner['likes'] = len(corner.get('liked_users', []))

    return jsonify({'corners': friend_corners, 'count': len(friend_corners)})
