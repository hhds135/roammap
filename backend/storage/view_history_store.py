"""
View history storage module.

Handles all view history related database operations including:
- Track post views
- Get view history by user
- Get view duration statistics
"""

from typing import Any, Dict, List, Optional
from bson import ObjectId
from datetime import datetime, timedelta
from pymongo.errors import PyMongoError

from .base_store import BaseStore


class ViewHistoryStore(BaseStore):
    """
    Storage operations for the view_history collection.
    """
    
    collection_name = "view_history"
    
    def create_view(self, user_id: ObjectId, post_id: ObjectId,
                    view_duration: int = 0) -> ObjectId:
        """
        Record a post view.
        
        Args:
            user_id: User's ObjectId
            post_id: Post's ObjectId
            view_duration: View duration in milliseconds
            
        Returns:
            ObjectId of the created view record
        """
        document = {
            'user_id': user_id,
            'post_id': post_id,
            'view_duration': view_duration
        }
        
        return self.create(document)
    
    def update_view_duration(self, user_id: ObjectId, post_id: ObjectId,
                             view_duration: int) -> bool:
        """
        Update the view duration for a view record.
        
        Args:
            user_id: User's ObjectId
            post_id: Post's ObjectId
            view_duration: New view duration in milliseconds
            
        Returns:
            True if updated successfully
        """
        result = self.collection.update_one(
            {
                'user_id': user_id,
                'post_id': post_id
            },
            {'$set': {'view_duration': view_duration}}
        )
        return result.modified_count > 0
    
    def get_views_by_user(self, user_id: ObjectId,
                          limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get view history for a user.
        
        Args:
            user_id: User's ObjectId
            limit: Maximum number of results
            
        Returns:
            List of view records
        """
        return self.find(
            {'user_id': user_id},
            limit=limit,
            sort=[('created_at', -1)]
        )
    
    def get_views_by_post(self, post_id: ObjectId,
                          limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all views for a post.
        
        Args:
            post_id: Post's ObjectId
            limit: Maximum number of results
            
        Returns:
            List of view records
        """
        return self.find(
            {'post_id': post_id},
            limit=limit,
            sort=[('created_at', -1)]
        )
    
    def get_recent_views(self, user_id: ObjectId,
                         hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get recent views for a user within a time period.
        
        Args:
            user_id: User's ObjectId
            hours: Number of hours to look back
            
        Returns:
            List of recent view records
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        return self.find(
            {
                'user_id': user_id,
                'created_at': {'$gte': cutoff_time}
            },
            sort=[('created_at', -1)]
        )
    
    def get_total_view_duration(self, user_id: ObjectId,
                                post_id: ObjectId) -> int:
        """
        Get total view duration for a user on a post.
        
        Args:
            user_id: User's ObjectId
            post_id: Post's ObjectId
            
        Returns:
            Total view duration in milliseconds
        """
        views = self.find({
            'user_id': user_id,
            'post_id': post_id
        })
        
        return sum(view.get('view_duration', 0) for view in views)
    
    def get_view_count_by_post(self, post_id: ObjectId) -> int:
        """
        Count views for a post.
        
        Args:
            post_id: Post's ObjectId
            
        Returns:
            Number of views
        """
        return self.count({'post_id': post_id})
    
    def get_view_count_by_user(self, user_id: ObjectId) -> int:
        """
        Count views by a user.
        
        Args:
            user_id: User's ObjectId
            
        Returns:
            Number of views
        """
        return self.count({'user_id': user_id})
    
    def delete_views_by_user(self, user_id: ObjectId) -> int:
        """
        Delete all views by a user.
        
        Args:
            user_id: User's ObjectId
            
        Returns:
            Number of deleted views
        """
        result = self.collection.delete_many({'user_id': user_id})
        return result.deleted_count
    
    def delete_views_by_post(self, post_id: ObjectId) -> int:
        """
        Delete all views for a post.
        
        Args:
            post_id: Post's ObjectId
            
        Returns:
            Number of deleted views
        """
        result = self.collection.delete_many({'post_id': post_id})
        return result.deleted_count
    
    def cleanup_old_views(self, days: int = 30) -> int:
        """
        Delete view records older than specified days.

        Args:
            days: Number of days to keep

        Returns:
            Number of deleted records
        """
        cutoff_time = datetime.utcnow() - timedelta(days=days)

        result = self.collection.delete_many({
            'created_at': {'$lt': cutoff_time}
        })
        return result.deleted_count

    def get_trending_posts(self, hours: int = 24, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get trending posts based on view count within a time period.

        Args:
            hours: Number of hours to look back
            limit: Maximum number of results

        Returns:
            List of posts with view counts
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": cutoff_time}
                }
            },
            {
                "$group": {
                    "_id": "$post_id",
                    "view_count": {"$sum": 1},
                    "total_duration": {"$sum": "$view_duration"}
                }
            },
            {"$sort": {"view_count": -1}},
            {"$limit": limit}
        ]

        return list(self.collection.aggregate(pipeline))

    def create_indexes(self):
        """Create indexes for the view_history collection."""
        self.collection.create_index('user_id')
        self.collection.create_index('post_id')
        self.collection.create_index('created_at', descending=True)
