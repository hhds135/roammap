"""
Post storage module.

Handles all post related database operations including:
- Post CRUD operations
- Route management
- Stats management
- Visibility filtering
"""

from typing import Any, Dict, List, Optional
from bson import ObjectId
from pymongo.errors import PyMongoError

from .base_store import BaseStore


class PostStore(BaseStore):
    """
    Storage operations for the posts collection.
    """

    collection_name = "posts"

    def create_post(self, user_id: ObjectId, title: str, description: str,
                    corner_ids: Optional[List[ObjectId]] = None,
                    media_type: str = "image",
                    media_files: Optional[List[ObjectId]] = None,
                    tags: Optional[List[str]] = None,
                    visibility: str = "public",
                    route: Optional[Dict[str, Any]] = None) -> ObjectId:
        """
        Create a new post.
        
        Args:
            user_id: Creator's user ID
            title: Post title
            description: Post description
            corner_ids: List of corner IDs mentioned in post
            media_type: "image" or "video"
            media_files: List of GridFS file IDs
            tags: Free-form tags
            visibility: "public", "private", or "followers"
            route: Optional embedded route with route_name and corner_ids
            
        Returns:
            ObjectId of the created post
        """
        document = {
            'user_id': user_id,
            'title': title,
            'description': description,
            'corner_ids': corner_ids or [],
            'media_type': media_type,
            'media_files': media_files or [],
            'tags': tags or [],
            'visibility': visibility,
            'stats': {
                'likes_count': 0,
                'comments_count': 0,
                'favorites_count': 0
            }
        }
        
        if route:
            document['route'] = route
            
        return self.create(document)
    
    def get_post_by_id(self, post_id: ObjectId) -> Optional[Dict[str, Any]]:
        """
        Get a post by ObjectId.
        
        Args:
            post_id: Post's ObjectId
            
        Returns:
            Post document or None
        """
        return self.get_by_id(post_id)
    
    def update_post(self, post_id: ObjectId, updates: Dict[str, Any]) -> bool:
        """
        Update post fields.
        
        Args:
            post_id: Post's ObjectId
            updates: Fields to update
            
        Returns:
            True if updated successfully
        """
        return self.update(post_id, updates)
    
    def delete_post(self, post_id: ObjectId) -> bool:
        """
        Delete a post.
        
        Args:
            post_id: Post's ObjectId
            
        Returns:
            True if deleted successfully
        """
        return self.delete(post_id)
    
    def get_posts_by_user(self, user_id: ObjectId, visibility: str = "public",
                          limit: int = 20, skip: int = 0) -> List[Dict[str, Any]]:
        """
        Get posts by a specific user.
        
        Args:
            user_id: User's ObjectId
            visibility: Filter by visibility
            limit: Maximum number of results
            skip: Number of results to skip
            
        Returns:
            List of posts
        """
        query = {'user_id': user_id}
        if visibility:
            query['visibility'] = visibility
            
        return self.find(
            query,
            limit=limit,
            skip=skip,
            sort=[('created_at', -1)]
        )
    
    def get_posts_by_corner(self, corner_id: ObjectId,
                            limit: int = 20, skip: int = 0) -> List[Dict[str, Any]]:
        """
        Get posts that mention a specific corner.

        Args:
            corner_id: Corner's ObjectId
            limit: Maximum number of results
            skip: Number of results to skip

        Returns:
            List of posts
        """
        return self.find(
            {'corner_ids': corner_id},
            limit=limit,
            skip=skip,
            sort=[('created_at', -1)]
        )

    def count_posts_by_corner(self, corner_id: ObjectId) -> int:
        """
        Count posts that mention a specific corner.

        Args:
            corner_id: Corner's ObjectId

        Returns:
            Number of posts
        """
        return self.count({'corner_ids': corner_id})
    
    def get_feed_posts(self, user_id: ObjectId = None,
                       limit: int = 20, skip: int = 0) -> List[Dict[str, Any]]:
        """
        Get posts for the main feed.
        
        Args:
            user_id: Optional user ID for personalized feed
            limit: Maximum number of results
            skip: Number of results to skip
            
        Returns:
            List of posts
        """
        query = {'visibility': 'public'}
        
        return self.find(
            query,
            limit=limit,
            skip=skip,
            sort=[('created_at', -1)]
        )
    
    def get_posts_by_visibility(self, visibility: str,
                                limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get posts by visibility.
        
        Args:
            visibility: Visibility filter
            limit: Maximum number of results
            
        Returns:
            List of posts
        """
        return self.find(
            {'visibility': visibility},
            limit=limit,
            sort=[('created_at', -1)]
        )
    
    def increment_stat(self, post_id: ObjectId, stat_name: str,
                       value: int = 1) -> bool:
        """
        Increment a post stat counter.
        
        Args:
            post_id: Post's ObjectId
            stat_name: Name of stat (likes_count, comments_count, favorites_count)
            value: Amount to increment
            
        Returns:
            True if updated successfully
        """
        result = self.collection.update_one(
            {'_id': post_id},
            {'$inc': {f'stats.{stat_name}': value}}
        )
        return result.modified_count > 0
    
    def decrement_stat(self, post_id: ObjectId, stat_name: str,
                       value: int = 1) -> bool:
        """
        Decrement a post stat counter.
        
        Args:
            post_id: Post's ObjectId
            stat_name: Name of stat
            value: Amount to decrement
            
        Returns:
            True if updated successfully
        """
        result = self.collection.update_one(
            {'_id': post_id},
            {'$inc': {f'stats.{stat_name}': -value}}
        )
        return result.modified_count > 0
    
    def get_stats(self, post_id: ObjectId) -> Optional[Dict[str, int]]:
        """
        Get post statistics.
        
        Args:
            post_id: Post's ObjectId
            
        Returns:
            Stats dict or None
        """
        post = self.get_by_id(post_id)
        return post.get('stats') if post else None
    
    def search_posts(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search posts by title or description.
        
        Args:
            query: Search query string
            limit: Maximum number of results
            
        Returns:
            List of matching posts
        """
        return self.find(
            {
                '$or': [
                    {'title': {'$regex': query, '$options': 'i'}},
                    {'description': {'$regex': query, '$options': 'i'}}
                ]
            },
            limit=limit,
            sort=[('created_at', -1)]
        )
    
    def get_posts_by_tags(self, tags: List[str],
                          limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get posts by tags.
        
        Args:
            tags: List of tags to search for
            limit: Maximum number of results
            
        Returns:
            List of matching posts
        """
        return self.find(
            {'tags': {'$in': tags}},
            limit=limit,
            sort=[('created_at', -1)]
        )
    
    def create_indexes(self):
        """Create indexes for the posts collection."""
        self.collection.create_index('user_id')
        self.collection.create_index('corner_ids')
        self.collection.create_index('created_at', descending=True)
        self.collection.create_index('visibility')
        self.collection.create_index('tags')
