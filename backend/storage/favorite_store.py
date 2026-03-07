"""
Favorite storage module.

Handles all favorite related database operations including:
- Favorite/unfavorite posts
- Check favorite status
- Get favorites by post or user
"""

from typing import Any, Dict, List, Optional
from bson import ObjectId
from pymongo.errors import PyMongoError, DuplicateKeyError

from .base_store import BaseStore


class FavoriteStore(BaseStore):
    """
    Storage operations for the favorites collection.
    """
    
    collection_name = "favorites"
    
    def create_favorite(self, user_id: ObjectId, post_id: ObjectId) -> Optional[ObjectId]:
        """
        Create a favorite (user favorites a post).
        
        Args:
            user_id: User's ObjectId
            post_id: Post's ObjectId
            
        Returns:
            ObjectId of the created favorite, or None if already favorited
        """
        try:
            document = {
                'user_id': user_id,
                'post_id': post_id
            }
            return self.create(document)
        except DuplicateKeyError:
            # Already favorited
            return None
    
    def delete_favorite(self, user_id: ObjectId, post_id: ObjectId) -> bool:
        """
        Unfavorite a post.
        
        Args:
            user_id: User's ObjectId
            post_id: Post's ObjectId
            
        Returns:
            True if favorite was deleted
        """
        result = self.collection.delete_one({
            'user_id': user_id,
            'post_id': post_id
        })
        return result.deleted_count > 0
    
    def toggle_favorite(self, user_id: ObjectId, post_id: ObjectId) -> bool:
        """
        Toggle favorite status.
        
        Args:
            user_id: User's ObjectId
            post_id: Post's ObjectId
            
        Returns:
            True if favorited, False if unfavorited
        """
        if self.is_favorite(user_id, post_id):
            self.delete_favorite(user_id, post_id)
            return False
        else:
            self.create_favorite(user_id, post_id)
            return True
    
    def is_favorite(self, user_id: ObjectId, post_id: ObjectId) -> bool:
        """
        Check if a user has favorited a post.
        
        Args:
            user_id: User's ObjectId
            post_id: Post's ObjectId
            
        Returns:
            True if favorited
        """
        return self.exists({
            'user_id': user_id,
            'post_id': post_id
        })
    
    def get_favorites_by_post(self, post_id: ObjectId,
                              limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all favorites for a post.
        
        Args:
            post_id: Post's ObjectId
            limit: Maximum number of results
            
        Returns:
            List of favorite records
        """
        return self.find(
            {'post_id': post_id},
            limit=limit,
            sort=[('created_at', -1)]
        )
    
    def get_favorites_by_user(self, user_id: ObjectId,
                              limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all favorites by a user.
        
        Args:
            user_id: User's ObjectId
            limit: Maximum number of results
            
        Returns:
            List of favorite records
        """
        return self.find(
            {'user_id': user_id},
            limit=limit,
            sort=[('created_at', -1)]
        )
    
    def count_favorites_by_post(self, post_id: ObjectId) -> int:
        """
        Count favorites for a post.
        
        Args:
            post_id: Post's ObjectId
            
        Returns:
            Number of favorites
        """
        return self.count({'post_id': post_id})
    
    def count_favorites_by_user(self, user_id: ObjectId) -> int:
        """
        Count favorites by a user.
        
        Args:
            user_id: User's ObjectId
            
        Returns:
            Number of favorites
        """
        return self.count({'user_id': user_id})
    
    def delete_favorites_by_post(self, post_id: ObjectId) -> int:
        """
        Delete all favorites for a post.
        
        Args:
            post_id: Post's ObjectId
            
        Returns:
            Number of deleted favorites
        """
        result = self.collection.delete_many({'post_id': post_id})
        return result.deleted_count
    
    def delete_favorites_by_user(self, user_id: ObjectId) -> int:
        """
        Delete all favorites by a user.
        
        Args:
            user_id: User's ObjectId
            
        Returns:
            Number of deleted favorites
        """
        result = self.collection.delete_many({'user_id': user_id})
        return result.deleted_count
    
    def create_indexes(self):
        """Create indexes for the favorites collection."""
        self.collection.create_index([('user_id', 1), ('post_id', 1)], unique=True)
        self.collection.create_index('post_id')
        self.collection.create_index('created_at', descending=True)
