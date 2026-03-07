"""
Storage layer package for Urban Canvas.

This package provides all MongoDB storage operations for the application.
It includes connection management, base store functionality, and specific
stores for each entity type.

Usage:
    from storage import (
        init_storage,
        UserStore,
        CornerStore,
        PostStore,
        CommentStore,
        LikeStore,
        FavoriteStore,
        ViewHistoryStore,
        MediaStore,
        GeoStore
    )
    
    # Initialize database connection
    init_storage(uri, db_name)
    
    # Use stores
    user_store = UserStore()
    user_store.create_user("username", "password_hash")
"""

from typing import Optional
from bson import ObjectId

from .connection import (
    MongoDBConnection,
    get_db,
    get_collection,
    init_db
)

from .base_store import BaseStore

from .user_store import UserStore

from .corner_store import CornerStore

from .post_store import PostStore

from .comment_store import CommentStore

from .like_store import LikeStore

from .favorite_store import FavoriteStore

from .view_history_store import ViewHistoryStore

from .media_store import MediaStore

from .geo_store import GeoStore


__all__ = [
    # Connection
    'MongoDBConnection',
    'get_db',
    'get_collection',
    'init_db',
    
    # Base
    'BaseStore',
    
    # Stores
    'UserStore',
    'CornerStore',
    'PostStore',
    'CommentStore',
    'LikeStore',
    'FavoriteStore',
    'ViewHistoryStore',
    'MediaStore',
    'GeoStore',
]


_storage_initialized = False


def init_storage(uri: str, db_name: str) -> None:
    """
    Initialize the storage layer.
    
    Call this function at application startup to establish
    MongoDB connection and create indexes.
    
    Args:
        uri: MongoDB connection URI (e.g., 'mongodb://localhost:27017/')
        db_name: Database name (e.g., 'urban_canvas')
    """
    global _storage_initialized
    
    # Initialize connection
    init_db(uri, db_name)
    
    # Create indexes for all collections
    _create_indexes()
    
    _storage_initialized = True


def _create_indexes() -> None:
    """Create indexes for all collections."""
    try:
        UserStore().create_indexes()
        CornerStore().create_indexes()
        PostStore().create_indexes()
        CommentStore().create_indexes()
        LikeStore().create_indexes()
        FavoriteStore().create_indexes()
        ViewHistoryStore().create_indexes()
        GeoStore().create_indexes()
    except Exception as e:
        # Log error but don't fail initialization
        print(f"Warning: Failed to create indexes: {e}")


def is_initialized() -> bool:
    """
    Check if storage layer is initialized.
    
    Returns:
        True if initialized
    """
    return _storage_initialized
