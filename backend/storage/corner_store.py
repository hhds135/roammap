"""
Corner storage module.

Handles all corner (location) related database operations including:
- Corner CRUD operations
- Geospatial queries
- Corner searches
"""

from typing import Any, Dict, List, Optional
from bson import ObjectId
from pymongo.errors import PyMongoError

from .base_store import BaseStore


class CornerStore(BaseStore):
    """
    Storage operations for the corners collection.
    """
    
    collection_name = "corners"
    
    def create_corner(self, name: str, description: str,
                      latitude: float, longitude: float,
                      address: str, images: Optional[List[str]] = None,
                      creator_id: Optional[ObjectId] = None) -> ObjectId:
        """
        Create a new corner (location).
        
        Args:
            name: Unique corner name
            description: Corner description
            latitude: Latitude (-90 to 90)
            longitude: Longitude (-180 to 180)
            address: Human-readable address
            images: List of image file IDs
            creator_id: User ID who created this corner
            
        Returns:
            ObjectId of the created corner
            
        Raises:
            PyMongoError: If name already exists
        """
        document = {
            'name': name,
            'description': description,
            'location': {
                'type': 'Point',
                'coordinates': [longitude, latitude]  # GeoJSON format: [lng, lat]
            },
            'address': address,
            'images': images or [],
            'creator_id': creator_id
        }
        
        return self.create(document)
    
    def get_corner_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a corner by name.
        
        Args:
            name: Corner name
            
        Returns:
            Corner document or None
        """
        return self.find_one({'name': name})
    
    def get_corner_by_id(self, corner_id: ObjectId) -> Optional[Dict[str, Any]]:
        """
        Get a corner by ObjectId.
        
        Args:
            corner_id: Corner's ObjectId
            
        Returns:
            Corner document or None
        """
        return self.get_by_id(corner_id)
    
    def update_corner(self, corner_id: ObjectId, updates: Dict[str, Any]) -> bool:
        """
        Update corner fields.
        
        Args:
            corner_id: Corner's ObjectId
            updates: Fields to update
            
        Returns:
            True if updated successfully
        """
        return self.update(corner_id, updates)
    
    def delete_corner(self, corner_id: ObjectId) -> bool:
        """
        Delete a corner.
        
        Args:
            corner_id: Corner's ObjectId
            
        Returns:
            True if deleted successfully
        """
        return self.delete(corner_id)
    
    def get_nearby_corners(self, latitude: float, longitude: float,
                           max_distance: int = 10000,
                           limit: int = 20) -> List[Dict[str, Any]]:
        """
        Find corners near a location.
        
        Args:
            latitude: Search center latitude
            longitude: Search center longitude
            max_distance: Maximum distance in meters (default: 10km)
            limit: Maximum number of results
            
        Returns:
            List of nearby corners
        """
        query = {
            'location': {
                '$near': {
                    '$geometry': {
                        'type': 'Point',
                        'coordinates': [longitude, latitude]
                    },
                    '$maxDistance': max_distance
                }
            }
        }
        print(query)
        return self.find(query, limit=limit)
    
    def search_corners_by_name(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search corners by name (case-insensitive regex).
        
        Args:
            query: Search query string
            limit: Maximum number of results
            
        Returns:
            List of matching corners
        """
        return self.find(
            {'name': {'$regex': query, '$options': 'i'}},
            limit=limit
        )
    
    def get_all_corners(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all corners.

        Args:
            limit: Maximum number of results

        Returns:
            List of corners
        """
        return self.find({}, limit=limit)

    def calculate_distance(self, lat1: float, lng1: float,
                           lat2: float, lng2: float) -> float:
        """
        Calculate distance between two points using Haversine formula.

        Args:
            lat1: Latitude of point 1
            lng1: Longitude of point 1
            lat2: Latitude of point 2
            lng2: Longitude of point 2

        Returns:
            Distance in meters
        """
        from math import radians, sin, cos, sqrt, atan2

        # Convert to radians
        lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])

        # Haversine formula
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        # Earth radius in meters
        r = 6371000
        return c * r

    def create_indexes(self):
        """Create indexes for the corners collection."""
        self.collection.create_index('name', unique=True)
        self.collection.create_index([('location', '2dsphere')])
        self.collection.create_index('creator_id')
