"""
Recommendation service - 推荐算法服务.

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
    推荐算法服务类.

    综合考虑地理位置、兴趣标签、社交关系和行为历史计算推荐分数。
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        初始化推荐服务.

        Args:
            weights: 推荐权重配置，默认为:
                - geo: 0.4 (地理位置)
                - interest: 0.3 (兴趣标签)
                - social: 0.2 (社交关系)
                - behavior: 0.1 (行为历史)
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
        为用户生成推荐信息流.

        Args:
            user_id: 用户 ID(可选，未登录用户使用匿名推荐)
            user_location: 用户位置 (lat, lng),可选
            limit: 返回帖子数量

        Returns:
            按推荐分数排序的帖子列表
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

        # 1. 获取候选帖子 (公开帖子)
        candidates = self._get_candidate_posts()

        # 2. 获取用户信息
        user = None
        if user_id:
            try:
                user_obj = ObjectId(user_id)
                user = self.user_store.get_user_by_id(user_obj)
            except Exception as e:
                logger.warning(f"Failed to get user {user_id}: {e}")

        # 3. 计算每个帖子的推荐分数
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

        # 4. 按分数排序
        scored_posts.sort(key=lambda x: x['score'], reverse=True)

        # 5. 返回前 N 个帖子
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
        获取候选帖子列表.

        Args:
            limit: 最大候选数量

        Returns:
            候选帖子列表 (仅公开帖子)
        """
        return self.post_store.get_posts_by_visibility('public', limit=limit)

    def _calculate_post_score(self, post: Dict[str, Any],
                               user: Optional[Dict[str, Any]],
                               user_location: Optional[Tuple[float, float]],
                               user_id: Optional[str]) -> Tuple[float, Dict[str, float]]:
        """
        计算帖子的推荐分数.

        Args:
            post: 帖子数据
            user: 用户数据
            user_location: 用户位置
            user_id: 用户 ID

        Returns:
            (总分数，分数分解字典)
        """
        # 计算各维度分数
        geo_score = self._calculate_geo_score(post, user_location)
        interest_score = self._calculate_interest_score(post, user)
        social_score = self._calculate_social_score(post, user_id)
        behavior_score = self._calculate_behavior_score(post, user_id)

        # 加权计算总分
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
        计算地理位置分数 (40%).

        距离越近，分数越高:
        - 距离 < 1km: 100 分
        - 距离 1-5km: 80 分
        - 距离 5-10km: 60 分
        - 距离 10-20km: 40 分
        - 距离 > 20km: 20 分

        Args:
            post: 帖子数据
            user_location: 用户位置 (lat, lng)

        Returns:
            地理位置分数 (0-100)
        """
        if not user_location:
            return 50  # 没有位置信息，给中等分数

        # 获取帖子关联的地点
        corner_ids = post.get('corner_ids', [])
        if not corner_ids:
            return 30  # 没有关联地点，给较低分数

        # 计算到最近地点的距离
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
            return 30  # 没有找到有效地点

        # 根据距离计算分数
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
        计算兴趣标签分数 (30%).

        根据帖子标签和用户兴趣标签的重叠度计算:
        - 完全匹配：100 分
        - 部分匹配：按比例计算
        - 无匹配：20 分

        Args:
            post: 帖子数据
            user: 用户数据

        Returns:
            兴趣标签分数 (0-100)
        """
        if not user:
            return 50  # 没有用户信息，给中等分数

        user_tags = set(user.get('interest_tags', []))
        post_tags = set(post.get('tags', []))

        if not user_tags:
            return 50  # 用户没有设置兴趣，给中等分数

        if not post_tags:
            return 30  # 帖子没有标签，给较低分数

        # 计算标签重叠
        overlap = len(user_tags & post_tags)
        total = len(post_tags)

        if overlap == 0:
            return 20  # 无重叠

        # 按比例计算分数
        match_ratio = overlap / total
        score = int(match_ratio * 100)

        return min(score, 100)

    def _calculate_social_score(self, post: Dict[str, Any],
                                 user_id: Optional[str]) -> float:
        """
        计算社交关系分数 (20%).

        - 自己的帖子：100 分
        - 关注用户的帖子：80 分
        - 互相关注用户的帖子：90 分
        - 其他人的帖子：40 分

        Args:
            post: 帖子数据
            user_id: 用户 ID

        Returns:
            社交关系分数 (0-100)
        """
        if not user_id:
            return 40  # 未登录用户，无社交关系

        post_user_id = str(post.get('user_id'))

        if post_user_id == user_id:
            return 100  # 自己的帖子

        # 检查是否关注了帖子创建者
        try:
            if is_following_user(user_id, post_user_id):
                # 检查是否互相关注
                if is_following_user(post_user_id, user_id):
                    return 90  # 互相关注
                else:
                    return 80  # 单向关注
            else:
                return 40  # 无社交关系
        except Exception:
            return 40  # 检查失败，给默认分数

    def _calculate_behavior_score(self, post: Dict[str, Any],
                                   user_id: Optional[str]) -> float:
        """
        计算行为历史分数 (10%).

        基于用户的历史行为:
        - 是否点赞过该帖子：+30 分
        - 是否收藏过该帖子：+30 分
        - 是否浏览过该帖子：+20 分
        - 浏览时长：额外加分

        Args:
            post: 帖子数据
            user_id: 用户 ID

        Returns:
            行为历史分数 (0-100)
        """
        if not user_id:
            return 10  # 未登录用户，无行为历史

        try:
            user_obj = ObjectId(user_id)
            post_obj = post['_id']
        except Exception:
            return 10

        score = 10  # 基础分

        # 检查点赞
        try:
            if self.like_store.is_liked(user_obj, post_obj):
                score += 30
        except Exception:
            pass

        # 检查收藏
        try:
            if self.favorite_store.is_favorite(user_obj, post_obj):
                score += 30
        except Exception:
            pass

        # 检查浏览
        try:
            total_duration = self.view_history_store.get_total_view_duration(
                user_obj, post_obj
            )
            if total_duration > 0:
                score += 20
                # 浏览时长加分
                if total_duration > 10000:  # > 10 秒
                    score += 10
        except Exception:
            pass

        return min(score, 100)

    def _calculate_distance(self, location1: Tuple[float, float],
                            location2: Dict[str, Any]) -> float:
        """
        使用 Haversine 公式计算两点之间的球面距离.

        Args:
            location1: (lat, lng)
            location2: GeoJSON Point {"coordinates": [lng, lat]}

        Returns:
            距离 (米)
        """
        from math import radians, sin, cos, sqrt, atan2

        lat1, lng1 = location1
        lat2, lng2 = location2['coordinates'][1], location2['coordinates'][0]

        # 转换为弧度
        lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])

        # Haversine 公式
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        # 地球半径 (米)
        r = 6371000
        return c * r

    def recommend_corners(self, user_id: Optional[str],
                           user_location: Optional[Tuple[float, float]] = None,
                           radius: int = 10000,
                           limit: int = 10) -> List[Dict[str, Any]]:
        """
        基于用户位置推荐可能感兴趣的地点.

        Args:
            user_id: 用户 ID(可选)
            user_location: 用户位置 (lat, lng)
            radius: 搜索半径 (米)
            limit: 返回地点数量

        Returns:
            推荐地点列表
        """
        if not user_location:
            # 没有位置信息，返回热门地点
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
            limit=limit * 2  # 获取更多以便排序
        )

        # 统计每个地点的帖子数量
        result = []
        for corner in corners:
            post_count = self.post_store.count_posts_by_corner(corner['_id'])

            # 计算距离
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

        # 按帖子数量和距离综合排序
        result.sort(key=lambda x: (x['post_count'], -x['distance']), reverse=True)

        return result[:limit]


def get_recommendation_service() -> RecommendationService:
    """
    获取推荐服务实例 (单例模式).

    Returns:
        RecommendationService 实例
    """
    if not hasattr(get_recommendation_service, '_instance'):
        get_recommendation_service._instance = RecommendationService()
    return get_recommendation_service._instance
