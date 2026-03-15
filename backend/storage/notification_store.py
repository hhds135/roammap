"""
Notification storage module.

Handles all notification-related database operations including:
- Notification CRUD operations
- Query by user
- Mark as read
"""

from typing import Any, Dict, List, Optional
from bson import ObjectId
from pymongo.errors import PyMongoError

from .base_store import BaseStore


class NotificationStore(BaseStore):
    """
    Storage operations for the notifications collection.
    """
    
    collection_name = "notifications"
    
    def create_notification(self, user_id: ObjectId, notification_type: str,
                           actor_id: ObjectId, content: str,
                           post_id: Optional[ObjectId] = None) -> ObjectId:
        """
        Create a new notification.
        
        Args:
            user_id: User receiving the notification
            notification_type: Type of notification ('like', 'comment', 'follow')
            actor_id: User who triggered the notification
            content: Notification message
            post_id: Related post ID (optional)
            
        Returns:
            ObjectId of the created notification
        """
        document = {
            'user_id': user_id,
            'type': notification_type,
            'actor_id': actor_id,
            'content': content,
            'post_id': post_id,
            'read': False,
            'created_at': self._get_current_timestamp()
        }
        
        return self.create(document)
    
    def get_user_notifications(self, user_id: ObjectId, 
                                unread_only: bool = False,
                                limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get notifications for a user.
        
        Args:
            user_id: User's ObjectId
            unread_only: Only return unread notifications
            limit: Maximum number of results
            
        Returns:
            List of notification documents
        """
        query = {'user_id': user_id}
        
        if unread_only:
            query['read'] = False
        
        return self.find(
            query,
            limit=limit,
            sort=[('created_at', -1)]
        )
    
    def mark_as_read(self, notification_id: ObjectId) -> bool:
        """
        Mark a notification as read.
        
        Args:
            notification_id: Notification's ObjectId
            
        Returns:
            True if updated successfully
        """
        return self.update(notification_id, {'read': True})
    
    def mark_all_as_read(self, user_id: ObjectId) -> bool:
        """
        Mark all notifications for a user as read.
        
        Args:
            user_id: User's ObjectId
            
        Returns:
            True if updated successfully
        """
        result = self.collection.update_many(
            {'user_id': user_id, 'read': False},
            {'$set': {'read': True}}
        )
        return result.modified_count > 0
    
    def get_unread_count(self, user_id: ObjectId) -> int:
        """
        Get count of unread notifications for a user.
        
        Args:
            user_id: User's ObjectId
            
        Returns:
            Number of unread notifications
        """
        return self.collection.count_documents({
            'user_id': user_id,
            'read': False
        })
    
    def delete_notification(self, notification_id: ObjectId) -> bool:
        """
        Delete a notification.
        
        Args:
            notification_id: Notification's ObjectId
            
        Returns:
            True if deleted successfully
        """
        return self.delete(notification_id)
    
    def create_indexes(self):
        """Create indexes for the notifications collection."""
        self.collection.create_index([('user_id', 1), ('created_at', -1)])
        self.collection.create_index([('user_id', 1), ('read', 1)])