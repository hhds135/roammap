"""
Like storage module.

Handles all like related database operations including:
- Like/unlike posts
- Check like status
- Get likes by post or user
"""

from typing import Any, Dict, List, Optional
from bson import ObjectId
from pymongo.errors import PyMongoError, DuplicateKeyError

from .base_store import BaseStore


class LikeStore(BaseStore):
    """
    Storage operations for the likes collection.
    """
    
    collection_name = "likes"
    
    def create_like(self, user_id: ObjectId, post_id: ObjectId) -> Optional[ObjectId]:
        """
        Create a like (user likes a post).
        
        Args:
            user_id: User's ObjectId
            post_id: Post's ObjectId
            
        Returns:
            ObjectId of the created like, or None if already liked
        """
        try:
            document = {
                'user_id': user_id,
                'post_id': post_id
            }
            return self.create(document)
        except DuplicateKeyError:
            # Already liked
            return None
    
    def delete_like(self, user_id: ObjectId, post_id: ObjectId) -> bool:
        """
        Unlike a post.
        
        Args:
            user_id: User's ObjectId
            post_id: Post's ObjectId
            
        Returns:
            True if like was deleted
        """
        result = self.collection.delete_one({
            'user_id': user_id,
            'post_id': post_id
        })
        return result.deleted_count > 0
    
    def toggle_like(self, user_id: ObjectId, post_id: ObjectId) -> bool:
        """
        Toggle like status (like if not liked, unlike if liked).
        
        Args:
            user_id: User's ObjectId
            post_id: Post's ObjectId
            
        Returns:
            True if liked, False if unliked
        """
        if self.is_liked(user_id, post_id):
            self.delete_like(user_id, post_id)
            return False
        else:
            self.create_like(user_id, post_id)
            return True
    
    def is_liked(self, user_id: ObjectId, post_id: ObjectId) -> bool:
        """
        Check if a user has liked a post.
        
        Args:
            user_id: User's ObjectId
            post_id: Post's ObjectId
            
        Returns:
            True if liked
        """
        return self.exists({
            'user_id': user_id,
            'post_id': post_id
        })
    
    def get_likes_by_post(self, post_id: ObjectId,
                          limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all likes for a post.
        
        Args:
            post_id: Post's ObjectId
            limit: Maximum number of results
            
        Returns:
            List of like records
        """
        return self.find(
            {'post_id': post_id},
            limit=limit,
            sort=[('created_at', -1)]
        )
    
    def get_likes_by_user(self, user_id: ObjectId,
                          limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all likes by a user.
        
        Args:
            user_id: User's ObjectId
            limit: Maximum number of results
            
        Returns:
            List of like records
        """
        return self.find(
            {'user_id': user_id},
            limit=limit,
            sort=[('created_at', -1)]
        )
    
    def count_likes_by_post(self, post_id: ObjectId) -> int:
        """
        Count likes for a post.
        
        Args:
            post_id: Post's ObjectId
            
        Returns:
            Number of likes
        """
        return self.count({'post_id': post_id})
    
    def count_likes_by_user(self, user_id: ObjectId) -> int:
        """
        Count likes by a user.
        
        Args:
            user_id: User's ObjectId
            
        Returns:
            Number of likes
        """
        return self.count({'user_id': user_id})
    
    def delete_likes_by_post(self, post_id: ObjectId) -> int:
        """
        Delete all likes for a post.
        
        Args:
            post_id: Post's ObjectId
            
        Returns:
            Number of deleted likes
        """
        result = self.collection.delete_many({'post_id': post_id})
        return result.deleted_count
    
    def delete_likes_by_user(self, user_id: ObjectId) -> int:
        """
        Delete all likes by a user.
        
        Args:
            user_id: User's ObjectId
            
        Returns:
            Number of deleted likes
        """
        result = self.collection.delete_many({'user_id': user_id})
        return result.deleted_count
    
    def create_indexes(self):
        """Create indexes for the likes collection."""
        self.collection.create_index([('user_id', 1), ('post_id', 1)], unique=True)
        self.collection.create_index('post_id')
        self.collection.create_index('created_at', descending=True)
