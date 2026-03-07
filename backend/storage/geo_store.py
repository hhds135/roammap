"""
Geospatial storage module.

Provides geospatial query helpers including:
- Nearby location queries
- Distance calculations
- Location-based searches
"""

from typing import Any, Dict, List, Optional, Tuple
from bson import ObjectId
from pymongo.errors import PyMongoError

from .base_store import BaseStore


class GeoStore(BaseStore):
    """
    Geospatial query operations.
    
    Provides helpers for location-based queries across collections.
    """
    
    collection_name = "corners"

    def get_collection(self, collection_name: str):
        """
        Get a collection by name.

        Args:
            collection_name: Name of the collection

        Returns:
            Collection instance
        """
        from .connection import get_collection
        return get_collection(collection_name)

    def create_location_index(self, collection_name: str = "corners"):
        """
        Create a 2dsphere index on a collection's location field.
        
        Args:
            collection_name: Name of the collection
        """
        collection = self.get_collection(collection_name)
        collection.create_index('location', sphere=True)
    
    def find_nearby(self, latitude: float, longitude: float,
                    max_distance: int = 10000,
                    limit: int = 20,
                    collection_name: str = "corners") -> List[Dict[str, Any]]:
        """
        Find documents near a location.
        
        Args:
            latitude: Search center latitude
            longitude: Search center longitude
            max_distance: Maximum distance in meters
            limit: Maximum number of results
            collection_name: Collection to search
            
        Returns:
            List of nearby documents
        """
        collection = self.get_collection(collection_name)
        
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
        
        return list(collection.find(query).limit(limit))
    
    def find_within_radius(self, latitude: float, longitude: float,
                           radius: int,
                           collection_name: str = "corners") -> List[Dict[str, Any]]:
        """
        Find documents within a radius using $geoWithin.
        
        Args:
            latitude: Search center latitude
            longitude: Search center longitude
            radius: Radius in meters
            collection_name: Collection to search
            
        Returns:
            List of documents within radius
        """
        collection = self.get_collection(collection_name)
        
        query = {
            'location': {
                '$geoWithin': {
                    '$centerSphere': {
                        'coordinates': [longitude, latitude],
                        'maxDistance': radius / 6378100  # Convert to radians
                    }
                }
            }
        }
        
        return list(collection.find(query))
    
    def find_in_polygon(self, coordinates: List[List[float]],
                        collection_name: str = "corners") -> List[Dict[str, Any]]:
        """
        Find documents within a polygon area.
        
        Args:
            coordinates: List of [longitude, latitude] pairs defining polygon
            collection_name: Collection to search
            
        Returns:
            List of documents within polygon
        """
        collection = self.get_collection(collection_name)
        
        query = {
            'location': {
                '$geoWithin': {
                    '$geometry': {
                        'type': 'Polygon',
                        'coordinates': [coordinates]
                    }
                }
            }
        }
        
        return list(collection.find(query))
    
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
        
        R = 6378100  # Earth's radius in meters
        
        lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
        
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        
        return R * c
    
    def get_location_stats(self, object_id: ObjectId,
                           collection_name: str = "corners") -> Optional[Dict[str, Any]]:
        """
        Get location statistics for a document.
        
        Args:
            object_id: Document's ObjectId
            collection_name: Collection name
            
        Returns:
            Location stats dict or None
        """
        collection = self.get_collection(collection_name)
        doc = collection.find_one({'_id': object_id})
        
        if not doc or 'location' not in doc:
            return None
        
        return {
            'type': doc['location'].get('type'),
            'coordinates': doc['location'].get('coordinates'),
            'latitude': doc['location']['coordinates'][1],
            'longitude': doc['location']['coordinates'][0]
        }
    
    def geo_search(self, query: str,
                   latitude: Optional[float] = None,
                   longitude: Optional[float] = None,
                   max_distance: int = 10000,
                   limit: int = 20) -> List[Dict[str, Any]]:
        """
        Combined text and geospatial search.
        
        Args:
            query: Text search query
            latitude: Optional latitude for location filter
            longitude: Optional longitude for location filter
            max_distance: Maximum distance in meters
            limit: Maximum number of results
            
        Returns:
            List of matching documents
        """
        filter_query = {}
        
        # Add text search if query provided
        if query:
            filter_query['$text'] = {'$search': query}
        
        # Add location filter if coordinates provided
        if latitude is not None and longitude is not None:
            filter_query['location'] = {
                '$near': {
                    '$geometry': {
                        'type': 'Point',
                        'coordinates': [longitude, latitude]
                    },
                    '$maxDistance': max_distance
                }
            }
        
        return self.find(filter_query, limit=limit)
    
    def create_indexes(self):
        """Create geospatial indexes."""
        self.create_location_index("corners")
        self.create_location_index("users")
