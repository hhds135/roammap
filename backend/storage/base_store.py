"""
Base store module providing common database operations.

All store classes should inherit from BaseStore to get common CRUD operations.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TypeVar, Generic
from bson import ObjectId
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from .connection import get_collection


T = TypeVar('T')


class BaseStore(Generic[T]):
    """
    Base class for all storage operations.
    
    Provides common CRUD operations and utility methods.
    """
    
    collection_name: str = ""
    
    def __init__(self):
        """Initialize the store with a collection."""
        self._collection: Optional[Collection] = None
    
    @property
    def collection(self) -> Collection:
        """
        Get the collection for this store.
        
        Returns:
            Pymongo Collection instance
        """
        if self._collection is None:
            self._collection = get_collection(self.collection_name)
        return self._collection
    
    @staticmethod
    def now() -> datetime:
        """
        Get current UTC datetime.
        
        Returns:
            Current datetime in UTC
        """
        return datetime.now(timezone.utc)
    
    @staticmethod
    def is_valid_object_id(object_id: str) -> bool:
        """
        Check if a string is a valid ObjectId.
        
        Args:
            object_id: String to check
            
        Returns:
            True if valid ObjectId, False otherwise
        """
        return ObjectId.is_valid(object_id)
    
    @staticmethod
    def to_object_id(object_id: str) -> ObjectId:
        """
        Convert a string to ObjectId.
        
        Args:
            object_id: String representation of ObjectId
            
        Returns:
            ObjectId instance
            
        Raises:
            InvalidId: If the string is not a valid ObjectId
        """
        return ObjectId(object_id)
    
    def create(self, document: Dict[str, Any]) -> ObjectId:
        """
        Create a new document.
        
        Args:
            document: Document to insert
            
        Returns:
            ObjectId of the inserted document
        """
        if 'created_at' not in document:
            document['created_at'] = self.now()
        if 'updated_at' not in document:
            document['updated_at'] = self.now()
        
        result = self.collection.insert_one(document)
        return result.inserted_id
    
    def get_by_id(self, object_id: ObjectId) -> Optional[Dict[str, Any]]:
        """
        Get a document by its ObjectId.
        
        Args:
            object_id: ObjectId of the document
            
        Returns:
            Document or None if not found
        """
        return self.collection.find_one({'_id': object_id})
    
    def update(self, object_id: ObjectId, updates: Dict[str, Any]) -> bool:
        """
        Update a document by its ObjectId.
        
        Args:
            object_id: ObjectId of the document to update
            updates: Fields to update
            
        Returns:
            True if document was updated, False if not found
        """
        updates['updated_at'] = self.now()
        result = self.collection.update_one(
            {'_id': object_id},
            {'$set': updates}
        )
        return result.modified_count > 0
    
    def delete(self, object_id: ObjectId) -> bool:
        """
        Delete a document by its ObjectId.
        
        Args:
            object_id: ObjectId of the document to delete
            
        Returns:
            True if document was deleted, False if not found
        """
        result = self.collection.delete_one({'_id': object_id})
        return result.deleted_count > 0
    
    def find(self, query: Dict[str, Any], limit: Optional[int] = None, 
             skip: Optional[int] = None, sort: Optional[List[tuple]] = None) -> List[Dict[str, Any]]:
        """
        Find documents matching a query.
        
        Args:
            query: MongoDB query filter
            limit: Maximum number of results to return
            skip: Number of results to skip
            sort: Sort specification (e.g., [('created_at', -1)])
            
        Returns:
            List of matching documents
        """
        cursor = self.collection.find(query)
        
        if sort:
            cursor = cursor.sort(sort)
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        
        return list(cursor)
    
    def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Find a single document matching a query.
        
        Args:
            query: MongoDB query filter
            
        Returns:
            Document or None if not found
        """
        return self.collection.find_one(query)
    
    def count(self, query: Optional[Dict[str, Any]] = None) -> int:
        """
        Count documents matching a query.
        
        Args:
            query: MongoDB query filter (None for all documents)
            
        Returns:
            Number of matching documents
        """
        return self.collection.count_documents(query or {})
    
    def exists(self, query: Dict[str, Any]) -> bool:
        """
        Check if any document matches a query.
        
        Args:
            query: MongoDB query filter
            
        Returns:
            True if a document exists, False otherwise
        """
        return self.count(query) > 0
    
    def create_indexes(self):
        """
        Create indexes on the collection.

        Override this method in subclasses to define collection-specific indexes.
        """
        pass
