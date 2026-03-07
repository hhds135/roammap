"""
Comment storage module.

Handles all comment related database operations including:
- Comment CRUD operations
- Comments by post
- Comments by user
"""

from typing import Any, Dict, List, Optional
from bson import ObjectId
from pymongo.errors import PyMongoError

from .base_store import BaseStore


class CommentStore(BaseStore):
    """
    Storage operations for the comments collection.
    """
    
    collection_name = "comments"
    
    def create_comment(self, post_id: ObjectId, user_id: ObjectId,
                       username: str, content: str) -> ObjectId:
        """
        Create a new comment.
        
        Args:
            post_id: Post's ObjectId
            user_id: Commenter's user ID
            username: Username (cached for display)
            content: Comment text
            
        Returns:
            ObjectId of the created comment
        """
        document = {
            'post_id': post_id,
            'user_id': user_id,
            'username': username,
            'content': content
        }
        
        return self.create(document)
    
    def get_comment_by_id(self, comment_id: ObjectId) -> Optional[Dict[str, Any]]:
        """
        Get a comment by ObjectId.
        
        Args:
            comment_id: Comment's ObjectId
            
        Returns:
            Comment document or None
        """
        return self.get_by_id(comment_id)
    
    def update_comment(self, comment_id: ObjectId, content: str) -> bool:
        """
        Update comment content.
        
        Args:
            comment_id: Comment's ObjectId
            content: New content
            
        Returns:
            True if updated successfully
        """
        return self.update(comment_id, {'content': content})
    
    def delete_comment(self, comment_id: ObjectId) -> bool:
        """
        Delete a comment.
        
        Args:
            comment_id: Comment's ObjectId
            
        Returns:
            True if deleted successfully
        """
        return self.delete(comment_id)
    
    def get_comments_by_post(self, post_id: ObjectId,
                             limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get all comments for a post.
        
        Args:
            post_id: Post's ObjectId
            limit: Maximum number of results
            
        Returns:
            List of comments
        """
        return self.find(
            {'post_id': post_id},
            limit=limit,
            sort=[('created_at', 1)]  # Oldest first
        )
    
    def get_comments_by_user(self, user_id: ObjectId,
                             limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get all comments by a user.
        
        Args:
            user_id: User's ObjectId
            limit: Maximum number of results
            
        Returns:
            List of comments
        """
        return self.find(
            {'user_id': user_id},
            limit=limit,
            sort=[('created_at', -1)]
        )
    
    def count_comments_by_post(self, post_id: ObjectId) -> int:
        """
        Count comments for a post.
        
        Args:
            post_id: Post's ObjectId
            
        Returns:
            Number of comments
        """
        return self.count({'post_id': post_id})
    
    def delete_comments_by_post(self, post_id: ObjectId) -> int:
        """
        Delete all comments for a post.
        
        Args:
            post_id: Post's ObjectId
            
        Returns:
            Number of deleted comments
        """
        result = self.collection.delete_many({'post_id': post_id})
        return result.deleted_count
    
    def delete_comments_by_user(self, user_id: ObjectId) -> int:
        """
        Delete all comments by a user.
        
        Args:
            user_id: User's ObjectId
            
        Returns:
            Number of deleted comments
        """
        result = self.collection.delete_many({'user_id': user_id})
        return result.deleted_count
    
    def create_indexes(self):
        """Create indexes for the comments collection."""
        self.collection.create_index('post_id')
        self.collection.create_index('user_id')
        self.collection.create_index('created_at', descending=True)
