"""
User storage module.

Handles all user-related database operations including:
- User CRUD operations
- Follow/unfollow functionality
- User queries
"""

from typing import Any, Dict, List, Optional
from bson import ObjectId
from pymongo.errors import PyMongoError

from .base_store import BaseStore


class UserStore(BaseStore):
    """
    Storage operations for the users collection.
    """
    
    collection_name = "users"
    
    def create_user(self, username: str, password_hash: str,
                    interest_tags: Optional[List[str]] = None,
                    location: Optional[Dict[str, Any]] = None) -> ObjectId:
        """
        Create a new user.
        
        Args:
            username: Unique username
            password_hash: Hashed password
            interest_tags: List of interest tags
            location: Optional GeoJSON location
            
        Returns:
            ObjectId of the created user
            
        Raises:
            PyMongoError: If username already exists
        """
        document = {
            'username': username,
            'password_hash': password_hash,
            'interest_tags': interest_tags or [],
            'following': [],
            'followers': [],
        }
        
        if location:
            document['location'] = location
            
        return self.create(document)
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get a user by username.
        
        Args:
            username: Username to search for
            
        Returns:
            User document or None
        """
        return self.find_one({'username': username})
    
    def get_user_by_id(self, user_id: ObjectId) -> Optional[Dict[str, Any]]:
        """
        Get a user by ObjectId.
        
        Args:
            user_id: User's ObjectId
            
        Returns:
            User document or None
        """
        return self.get_by_id(user_id)
    
    def update_user(self, user_id: ObjectId, updates: Dict[str, Any]) -> bool:
        """
        Update user fields.
        
        Args:
            user_id: User's ObjectId
            updates: Fields to update
            
        Returns:
            True if updated successfully
        """
        return self.update(user_id, updates)
    
    def delete_user(self, user_id: ObjectId) -> bool:
        """
        Delete a user.
        
        Args:
            user_id: User's ObjectId
            
        Returns:
            True if deleted successfully
        """
        return self.delete(user_id)
    
    def follow(self, follower_id: ObjectId, following_id: ObjectId) -> bool:
        """
        Make one user follow another.
        
        Args:
            follower_id: User who is following
            following_id: User being followed
            
        Returns:
            True if follow was successful
        """
        # Add to follower's following list
        self.collection.update_one(
            {'_id': follower_id, 'following': {'$ne': following_id}},
            {'$push': {'following': following_id}}
        )
        
        # Add to following's followers list
        result = self.collection.update_one(
            {'_id': following_id, 'followers': {'$ne': follower_id}},
            {'$push': {'followers': follower_id}}
        )
        
        return result.modified_count > 0
    
    def unfollow(self, follower_id: ObjectId, following_id: ObjectId) -> bool:
        """
        Make one user unfollow another.
        
        Args:
            follower_id: User who is unfollowing
            following_id: User being unfollowed
            
        Returns:
            True if unfollow was successful
        """
        # Remove from follower's following list
        self.collection.update_one(
            {'_id': follower_id},
            {'$pull': {'following': following_id}}
        )
        
        # Remove from following's followers list
        result = self.collection.update_one(
            {'_id': following_id},
            {'$pull': {'followers': follower_id}}
        )
        
        return result.modified_count > 0
    
    def is_following(self, follower_id: ObjectId, following_id: ObjectId) -> bool:
        """
        Check if a user is following another user.
        
        Args:
            follower_id: User who might be following
            following_id: User who might be followed
            
        Returns:
            True if following
        """
        return self.exists({
            '_id': follower_id,
            'following': following_id
        })
    
    def get_followers(self, user_id: ObjectId) -> List[Dict[str, Any]]:
        """
        Get all followers of a user.
        
        Args:
            user_id: User's ObjectId
            
        Returns:
            List of follower user documents
        """
        user = self.get_by_id(user_id)
        if not user:
            return []
        
        follower_ids = user.get('followers', [])
        return self.find({'_id': {'$in': follower_ids}})
    
    def get_following(self, user_id: ObjectId) -> List[Dict[str, Any]]:
        """
        Get all users that a user is following.
        
        Args:
            user_id: User's ObjectId
            
        Returns:
            List of following user documents
        """
        user = self.get_by_id(user_id)
        if not user:
            return []
        
        following_ids = user.get('following', [])
        return self.find({'_id': {'$in': following_ids}})
    
    def create_indexes(self):
        """Create indexes for the users collection."""
        self.collection.create_index('username', unique=True)
        self.collection.create_index([('location', '2dsphere')])
        self.collection.create_index('followers')
        self.collection.create_index('following')
