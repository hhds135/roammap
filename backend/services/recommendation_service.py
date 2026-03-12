"""
Recommendation service - Personalized content recommendation algorithm.

Implements personalized content recommendation based on:
- Geographic proximity (40%)
- Interest tag matching (30%)
- Social relationships (20%)
- User behavior history (10%)
"""

import time
import logging
import hashlib
from typing import Any, Dict, List, Optional, Tuple
from functools import lru_cache
from bson import ObjectId

from storage.post_store import PostStore
from storage.user_store import UserStore
from storage.corner_store import CornerStore
from storage.like_store import LikeStore
from storage.favorite_store import FavoriteStore
from storage.view_history_store import ViewHistoryStore
from utils import is_following_user
from config import Config

# Configure logging
logger = logging.getLogger('recommendations')

# Cache TTL in seconds (5 minutes default)
RECOMMENDATION_CACHE_TTL = getattr(Config, 'RECOMMENDATION_CACHE_TTL', 300)


class RecommendationService:
    """
    Recommendation algorithm service class.

    Calculates recommendation scores by comprehensively considering geographic location, 
    interest tags, social relationships, and behavior history.
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        Initialize recommendation service.

        Args:
            weights: Recommendation weight configuration, defaults to:
                - geo: 0.4 (geographic location)
                - interest: 0.3 (interest tags)
                - social: 0.2 (social relationships)
                - behavior: 0.1 (behavior history)
        """
        self.weights = weights or {
            'geo': 0.4,
            'interest': 0.3,
            'social': 0.2,
            'behavior': 0.1
        }

        # Initialize storage instances
        self.post_store = PostStore()
        self.user_store = UserStore()
        self.corner_store = CornerStore()
        self.like_store = LikeStore()
        self.favorite_store = FavoriteStore()
        self.view_history_store = ViewHistoryStore()

        # Initialize cache: {cache_key: (timestamp, result)}
        self._cache: Dict[str, Tuple[float, List[Dict[str, Any]]]] = {}

    def _generate_cache_key(self, user_id: Optional[str],
                            user_location: Optional[Tuple[float, float]],
                            limit: int) -> str:
        """
        Generate a cache key for recommendation request.

        Args:
            user_id: User ID
            user_location: User location (lat, lng)
            limit: Number of results

        Returns:
            Cache key string
        """
        key_string = f"{user_id}:{user_location}:{limit}"
        return hashlib.md5(key_string.encode()).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get result from cache if not expired.

        Args:
            cache_key: Cache key

        Returns:
            Cached result or None if expired/not found
        """
        if cache_key in self._cache:
            timestamp, result = self._cache[cache_key]
            if time.time() - timestamp < RECOMMENDATION_CACHE_TTL:
                return result
            else:
                # Remove expired entry
                del self._cache[cache_key]
        return None

    def _set_to_cache(self, cache_key: str, result: List[Dict[str, Any]]) -> None:
        """
        Set result to cache with current timestamp.

        Args:
            cache_key: Cache key
            result: Result to cache
        """
        self._cache[cache_key] = (time.time(), result)

        # Limit cache size (keep max 100 entries)
        if len(self._cache) > 100:
            # Remove oldest entries
            sorted_keys = sorted(self._cache.keys(),
                                key=lambda k: self._cache[k][0])
            for key in sorted_keys[:10]:
                del self._cache[key]

    def clear_cache(self) -> None:
        """Clear all cached recommendations."""
        self._cache.clear()

    def recommend_feed(self, user_id: Optional[str],
                       user_location: Optional[Tuple[float, float]] = None,
                       limit: int = 20) -> List[Dict[str, Any]]:
        """
        Generate personalized recommendation feed for users.

        Args:
            user_id: User ID (optional, anonymous users use anonymous recommendations)
            user_location: User location (lat, lng), optional
            limit: Number of posts to return

        Returns:
            List of posts sorted by recommendation score
        """
        start_time = time.time()

        # Generate cache key
        cache_key = self._generate_cache_key(user_id, user_location, limit)

        # Try to get from cache
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache hit for user={user_id}, location={user_location}")
            return cached_result

        logger.info(f"Generating recommendations for user={user_id}, location={user_location}")

        # 1. Get candidate posts (public posts)
        candidates = self._get_candidate_posts()

        # 2. Get user information
        user = None
        if user_id:
            try:
                user_obj = ObjectId(user_id)
                user = self.user_store.get_user_by_id(user_obj)
            except Exception as e:
                logger.warning(f"Failed to get user {user_id}: {e}")

        # 3. Calculate recommendation score for each post
        scored_posts = []
        for post in candidates:
            score, breakdown = self._calculate_post_score(
                post, user, user_location, user_id
            )
            scored_posts.append({
                'post': post,
                'score': score,
                'breakdown': breakdown
            })

        # 4. Sort by score
        scored_posts.sort(key=lambda x: x['score'], reverse=True)

        # 5. Return top N posts
        result = [sp['post'] for sp in scored_posts[:limit]]

        # Cache the result
        self._set_to_cache(cache_key, result)

        # Log top recommendations in debug mode
        if getattr(Config, 'DEBUG', False):
            logger.debug(f"Top {min(5, len(scored_posts))} recommendations:")
            for sp in scored_posts[:5]:
                logger.debug(
                    f"  Post {sp['post']['_id']}: score={sp['score']:.2f}, "
                    f"breakdown={sp['breakdown']}"
                )

        elapsed = time.time() - start_time
        logger.info(f"Recommendation generation completed in {elapsed:.3f}s, "
                   f"returned {len(result)} posts")

        return result

    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache info
        """
        return {
            'cache_size': len(self._cache),
            'cache_ttl': RECOMMENDATION_CACHE_TTL,
            'max_cache_size': 100
        }

    def _get_candidate_posts(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Get list of candidate posts.

        Args:
            limit: Maximum number of candidates

        Returns:
            List of candidate posts (public posts only)
        """
        return self.post_store.get_posts_by_visibility('public', limit=limit)

    def _calculate_post_score(self, post: Dict[str, Any],
                               user: Optional[Dict[str, Any]],
                               user_location: Optional[Tuple[float, float]],
                               user_id: Optional[str]) -> Tuple[float, Dict[str, float]]:
        """
        Calculate recommendation score for a post.

        Args:
            post: Post data
            user: User data
            user_location: User location
            user_id: User ID

        Returns:
            (total score, score breakdown dictionary)
        """
        # Calculate scores for each dimension
        geo_score = self._calculate_geo_score(post, user_location)
        interest_score = self._calculate_interest_score(post, user)
        social_score = self._calculate_social_score(post, user_id)
        behavior_score = self._calculate_behavior_score(post, user_id)

        # Calculate weighted total score
        total_score = (
            geo_score * self.weights['geo'] +
            interest_score * self.weights['interest'] +
            social_score * self.weights['social'] +
            behavior_score * self.weights['behavior']
        )

        breakdown = {
            'geo': geo_score,
            'interest': interest_score,
            'social': social_score,
            'behavior': behavior_score,
            'total': total_score
        }

        return total_score, breakdown

    def _calculate_geo_score(self, post: Dict[str, Any],
                              user_location: Optional[Tuple[float, float]]) -> float:
        """
        Calculate geographic location score (40%).

        Closer distance results in higher score:
        - Distance < 1km: 100 points
        - Distance 1-5km: 80 points
        - Distance 5-10km: 60 points
        - Distance 10-20km: 40 points
        - Distance > 20km: 20 points

        Args:
            post: Post data
            user_location: User location (lat, lng)

        Returns:
            Geographic location score (0-100)
        """
        if not user_location:
            return 50  # No location info, give medium score

        # Get corners associated with the post
        corner_ids = post.get('corner_ids', [])
        if not corner_ids:
            return 30  # No associated corners, give lower score

        # Calculate distance to nearest corner
        min_distance = float('inf')
        for corner_id in corner_ids:
            corner = self.corner_store.get_corner_by_id(corner_id)
            if corner and 'location' in corner:
                distance = self._calculate_distance(
                    user_location,
                    corner['location']
                )
                if distance < min_distance:
                    min_distance = distance

        if min_distance == float('inf'):
            return 30  # No valid corners found

        # Calculate score based on distance
        if min_distance < 1000:  # < 1km
            return 100
        elif min_distance < 5000:  # 1-5km
            return 80
        elif min_distance < 10000:  # 5-10km
            return 60
        elif min_distance < 20000:  # 10-20km
            return 40
        else:  # > 20km
            return 20

    def _calculate_interest_score(self, post: Dict[str, Any],
                                   user: Optional[Dict[str, Any]]) -> float:
        """
        Calculate interest tag score (30%).

        Calculate based on overlap between post tags and user interest tags:
        - Complete match: 100 points
        - Partial match: calculated proportionally
        - No match: 20 points

        Args:
            post: Post data
            user: User data

        Returns:
            Interest tag score (0-100)
        """
        if not user:
            return 50  # No user info, give medium score

        user_tags = set(user.get('interest_tags', []))
        post_tags = set(post.get('tags', []))

        if not user_tags:
            return 50  # User hasn't set interests, give medium score

        if not post_tags:
            return 30  # Post has no tags, give lower score

        # Calculate tag overlap
        overlap = len(user_tags & post_tags)
        total = len(post_tags)

        if overlap == 0:
            return 20  # No overlap

        # Calculate score proportionally
        match_ratio = overlap / total
        score = int(match_ratio * 100)

        return min(score, 100)

    def _calculate_social_score(self, post: Dict[str, Any],
                                 user_id: Optional[str]) -> float:
        """
        Calculate social relationship score (20%).

        - Own posts: 100 points
        - Posts from followed users: 80 points
        - Posts from mutually followed users: 90 points
        - Posts from others: 40 points

        Args:
            post: Post data
            user_id: User ID

        Returns:
            Social relationship score (0-100)
        """
        if not user_id:
            return 40  # Not logged in, no social relationships

        post_user_id = str(post.get('user_id'))

        if post_user_id == user_id:
            return 100  # Own post

        # Check if following post creator
        try:
            if is_following_user(user_id, post_user_id):
                # Check if mutually following
                if is_following_user(post_user_id, user_id):
                    return 90  # Mutually following
                else:
                    return 80  # One-way follow
            else:
                return 40  # No social relationship
        except Exception:
            return 40  # Check failed, give default score

    def _calculate_behavior_score(self, post: Dict[str, Any],
                                   user_id: Optional[str]) -> float:
        """
        Calculate behavior history score (10%).

        Based on user's historical behavior:
        - Whether liked the post: +30 points
        - Whether favorited the post: +30 points
        - Whether viewed the post: +20 points
        - View duration: extra points

        Args:
            post: Post data
            user_id: User ID

        Returns:
            Behavior history score (0-100)
        """
        if not user_id:
            return 10  # Not logged in, no behavior history

        try:
            user_obj = ObjectId(user_id)
            post_obj = post['_id']
        except Exception:
            return 10

        score = 10  # Base score

        # Check like
        try:
            if self.like_store.is_liked(user_obj, post_obj):
                score += 30
        except Exception:
            pass

        # Check favorite
        try:
            if self.favorite_store.is_favorite(user_obj, post_obj):
                score += 30
        except Exception:
            pass

        # Check view
        try:
            total_duration = self.view_history_store.get_total_view_duration(
                user_obj, post_obj
            )
            if total_duration > 0:
                score += 20
                # View duration bonus points
                if total_duration > 10000:  # > 10 seconds
                    score += 10
        except Exception:
            pass

        return min(score, 100)

    def _calculate_distance(self, location1: Tuple[float, float],
                            location2: Dict[str, Any]) -> float:
        """
        Calculate spherical distance between two points using Haversine formula.

        Args:
            location1: (lat, lng)
            location2: GeoJSON Point {"coordinates": [lng, lat]}

        Returns:
            距离 (米)
        """
        from math import radians, sin, cos, sqrt, atan2

        lat1, lng1 = location1
        lat2, lng2 = location2['coordinates'][1], location2['coordinates'][0]

        # Convert to radians
        lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])

        # Haversine formula
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        # Earth radius (meters)
        r = 6371000
        return c * r

    def recommend_corners(self, user_id: Optional[str],
                           user_location: Optional[Tuple[float, float]] = None,
                           radius: int = 10000,
                           limit: int = 10) -> List[Dict[str, Any]]:
        """
        Recommend potentially interesting corners based on user location.

        Args:
            user_id: User ID (optional)
            user_location: User location (lat, lng)
            radius: Search radius (meters)
            limit: Number of corners to return

        Returns:
            List of recommended corners
        """
        if not user_location:
            # No location info, return popular corners
            corners = self.corner_store.get_all_corners(limit=limit)
            # Convert ObjectId to string for JSON serialization
            result = []
            for corner in corners:
                corner_data = {
                    '_id': str(corner['_id']),
                    'name': corner['name'],
                    'description': corner.get('description', ''),
                    'location': corner['location'],
                    'address': corner.get('address', '')
                }
                result.append(corner_data)
            return result

        lat, lng = user_location
        corners = self.corner_store.get_nearby_corners(
            latitude=lat,
            longitude=lng,
            max_distance=radius,
            limit=limit * 2  # Get more for sorting
        )

        # Count posts for each corner
        result = []
        for corner in corners:
            post_count = self.post_store.count_posts_by_corner(corner['_id'])

            # Calculate distance
            distance = self._calculate_distance(
                user_location,
                corner['location']
            )

            corner_data = {
                '_id': str(corner['_id']),
                'name': corner['name'],
                'description': corner.get('description', ''),
                'location': corner['location'],
                'address': corner.get('address', ''),
                'distance': round(distance, 2),
                'post_count': post_count
            }
            result.append(corner_data)

        # Sort comprehensively by post count and distance
        result.sort(key=lambda x: (x['post_count'], -x['distance']), reverse=True)

        return result[:limit]


def get_recommendation_service() -> RecommendationService:
    """
    Get recommendation service instance (singleton pattern).

    Returns:
        RecommendationService instance
    """
    if not hasattr(get_recommendation_service, '_instance'):
        get_recommendation_service._instance = RecommendationService()
    return get_recommendation_service._instance
