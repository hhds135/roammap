"""Notification endpoints."""
from flask import Blueprint, request, jsonify
from bson import ObjectId

from storage.notification_store import NotificationStore
from storage.user_store import UserStore
from utils import jwt_required

bp = Blueprint('notifications', __name__)

notification_store = NotificationStore()
user_store = UserStore()


@bp.route('/api/notifications', methods=['GET'])
@jwt_required
def get_notifications():
    """
    Get notifications for the current user.
    
    Query parameters:
        - unread_only: Only return unread notifications (default: false)
        - limit: Maximum number of results (default: 50)
    
    Returns:
        JSON with notifications list
    """
    user_id = request.user_id
    
    try:
        user_id_obj = ObjectId(user_id)
    except Exception:
        return jsonify({'error': 'Invalid user ID'}), 400
    
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    
    try:
        limit = int(request.args.get('limit', 50))
        limit = min(limit, 100)
    except ValueError:
        limit = 50
    
    # Get notifications
    notifications = notification_store.get_user_notifications(
        user_id_obj,
        unread_only=unread_only,
        limit=limit
    )
    
    # Get actor info for each notification
    result = []
    for notification in notifications:
        actor = user_store.get_user_by_id(notification['actor_id'])
        
        notification_data = {
            '_id': str(notification['_id']),
            'type': notification['type'],
            'content': notification['content'],
            'read': notification['read'],
            'created_at': notification['created_at']
        }
        
        if actor:
            notification_data['actor'] = {
                'user_id': str(actor['_id']),
                'username': actor.get('username', '')
            }
        
        if notification.get('post_id'):
            notification_data['post_id'] = str(notification['post_id'])
        
        result.append(notification_data)
    
    return jsonify({
        'success': True,
        'data': {
            'notifications': result
        }
    })


@bp.route('/api/notifications/unread-count', methods=['GET'])
@jwt_required
def get_unread_count():
    """
    Get count of unread notifications for the current user.
    
    Returns:
        JSON with unread count
    """
    user_id = request.user_id
    
    try:
        user_id_obj = ObjectId(user_id)
    except Exception:
        return jsonify({'error': 'Invalid user ID'}), 400
    
    count = notification_store.get_unread_count(user_id_obj)
    
    return jsonify({
        'success': True,
        'data': {
            'unread_count': count
        }
    })


@bp.route('/api/notifications/<notification_id>/read', methods=['PUT'])
@jwt_required
def mark_as_read(notification_id):
    """
    Mark a notification as read.
    
    Args:
        notification_id: Notification ID
    
    Returns:
        JSON with success message
    """
    user_id = request.user_id
    
    try:
        notification_id_obj = ObjectId(notification_id)
    except Exception:
        return jsonify({'error': 'Invalid notification ID'}), 400
    
    # Verify notification belongs to user
    notification = notification_store.get_by_id(notification_id_obj)
    if not notification:
        return jsonify({'error': 'Notification not found'}), 404
    
    if str(notification['user_id']) != user_id:
        return jsonify({'error': 'Access denied'}), 403
    
    # Mark as read
    success = notification_store.mark_as_read(notification_id_obj)
    if not success:
        return jsonify({'error': 'Failed to mark notification as read'}), 500
    
    return jsonify({
        'success': True,
        'message': 'Notification marked as read'
    })


@bp.route('/api/notifications/read-all', methods=['PUT'])
@jwt_required
def mark_all_as_read():
    """
    Mark all notifications for the current user as read.
    
    Returns:
        JSON with success message
    """
    user_id = request.user_id
    
    try:
        user_id_obj = ObjectId(user_id)
    except Exception:
        return jsonify({'error': 'Invalid user ID'}), 400
    
    success = notification_store.mark_all_as_read(user_id_obj)
    if not success:
        return jsonify({'error': 'Failed to mark notifications as read'}), 500
    
    return jsonify({
        'success': True,
        'message': 'All notifications marked as read'
    })


@bp.route('/api/notifications/<notification_id>', methods=['DELETE'])
@jwt_required
def delete_notification(notification_id):
    """
    Delete a notification.
    
    Args:
        notification_id: Notification ID
    
    Returns:
        JSON with success message
    """
    user_id = request.user_id
    
    try:
        notification_id_obj = ObjectId(notification_id)
    except Exception:
        return jsonify({'error': 'Invalid notification ID'}), 400
    
    # Verify notification belongs to user
    notification = notification_store.get_by_id(notification_id_obj)
    if not notification:
        return jsonify({'error': 'Notification not found'}), 404
    
    if str(notification['user_id']) != user_id:
        return jsonify({'error': 'Access denied'}), 403
    
    # Delete notification
    success = notification_store.delete(notification_id_obj)
    if not success:
        return jsonify({'error': 'Failed to delete notification'}), 500
    
    return jsonify({
        'success': True,
        'message': 'Notification deleted'
    })