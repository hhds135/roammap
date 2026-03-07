"""
MongoDB connection management module.

Provides a singleton connection manager for MongoDB database access.
"""

from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure

from config import Config


class MongoDBConnection:
    """
    MongoDB connection singleton.

    Manages the database connection and provides access to collections.
    """

    _instance: Optional['MongoDBConnection'] = None
    _client: Optional[MongoClient] = None
    _db: Optional[Database] = None

    def __new__(cls, uri: str = None, db_name: str = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, uri: str = None, db_name: str = None):
        """
        Initialize MongoDB connection.

        Args:
            uri: MongoDB connection URI (e.g., 'mongodb://localhost:27017/')
            db_name: Database name (e.g., 'urban_canvas')
        """
        if self._client is not None:
            return

        self.uri = uri or Config.MONGODB_URI
        self.db_name = db_name or Config.MONGODB_DB_NAME
        
    def connect(self) -> Database:
        """
        Establish connection to MongoDB.
        
        Returns:
            Database instance
            
        Raises:
            ConnectionFailure: If connection cannot be established
        """
        if self._client is not None:
            return self._db
        
        try:
            self._client = MongoClient(self.uri)
            self._db = self._client[self.db_name]
            
            # Test connection
            self._client.admin.command('ping')
            return self._db
        except ConnectionFailure as e:
            raise ConnectionFailure(f"Failed to connect to MongoDB: {e}")
    
    def get_database(self) -> Optional[Database]:
        """
        Get the database instance.
        
        Returns:
            Database instance or None if not connected
        """
        return self._db
    
    def get_collection(self, name: str):
        """
        Get a collection by name.
        
        Args:
            name: Collection name
            
        Returns:
            Collection instance
        """
        if self._db is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._db[name]
    
    def close(self):
        """Close the MongoDB connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
    
    def is_connected(self) -> bool:
        """
        Check if connected to MongoDB.
        
        Returns:
            True if connected, False otherwise
        """
        return self._client is not None


# Convenience functions
def get_db() -> Database:
    """
    Get the database instance.
    
    Returns:
        Database instance
    """
    conn = MongoDBConnection()
    return conn.get_database()


def get_collection(name: str):
    """
    Get a collection by name.
    
    Args:
        name: Collection name
        
    Returns:
        Collection instance
    """
    conn = MongoDBConnection()
    return conn.get_collection(name)


def init_db(uri: str, db_name: str) -> Database:
    """
    Initialize database connection.
    
    Args:
        uri: MongoDB connection URI
        db_name: Database name
        
    Returns:
        Database instance
    """
    conn = MongoDBConnection(uri, db_name)
    return conn.connect()
