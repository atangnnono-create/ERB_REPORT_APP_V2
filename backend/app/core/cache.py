import redis
from functools import wraps
import json
import hashlib
from typing import Any, Optional
import logging


logger = logging.getLogger(__name__)


class CacheService:

    def __init__(self):
        try:
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                decode_responses=False  # We want bytes for JSON
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established successfully")
        except redis.ConnectionError as e:
            logger.error(f"Redis connection failed: {e}")
            self.redis_client = None

    def invalidate_user_reports(self, user_id: int):
        """Invalidate all cache keys for user's reports"""
        pattern = f"get_reports:*:user_id:{user_id}:*"
        keys = self.redis_client.keys(pattern)
        if keys:
            self.redis_client.delete(*keys)


    def cache_key(self, func_name: str, *args, **kwargs) -> str:
        """Create stable cache key without pickle"""
        # Convert args and kwargs to stable string representation
        args_str = str(args)
        kwargs_str = str(sorted(kwargs.items()))
        key_data = f"{func_name}:{args_str}:{kwargs_str}"
        return f"app:{func_name}:{hashlib.sha256(key_data.encode()).hexdigest()}"

    def cached(self, ttl: int = 300):
        """Decorator for caching function results with JSON serialization"""

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # If Redis is not available, bypass cache
                if not self.redis_client:
                    return func(*args, **kwargs)

                key = self.cache_key(func.__name__, *args, **kwargs)
                try:
                    cached = self.redis_client.get(key)
                    if cached:
                        logger.debug(f"Cache hit for {key}")
                        return json.loads(cached)
                except (redis.RedisError, json.JSONDecodeError) as e:
                    logger.warning(f"Cache read error for {key}: {e}")

                # Execute function and cache result
                result = func(*args, **kwargs)
                try:
                    # Use default=str to handle datetime and other non-serializable objects
                    serialized_result = json.dumps(result, default=str, ensure_ascii=False)
                    self.redis_client.setex(key, ttl, serialized_result)
                    logger.debug(f"Cached result for {key} with TTL {ttl}")
                except (redis.RedisError, TypeError) as e:
                    logger.warning(f"Cache write error for {key}: {e}")

                return result

            return wrapper

        return decorator

    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate cache keys matching pattern"""
        if not self.redis_client:
            return 0

        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"Invalidated {deleted} cache keys matching {pattern}")
                return deleted
        except redis.RedisError as e:
            logger.error(f"Cache invalidation error for pattern {pattern}: {e}")
        return 0

    def invalidate_user_data(self, user_id: int):
        """Invalidate all cache entries for a specific user"""
        patterns = [
            f"app:get_user:*:user_id:{user_id}:*",
            f"app:get_reports:*:user_id:{user_id}:*",
            f"app:get_report:*:user_id:{user_id}:*"
        ]
        total_deleted = 0
        for pattern in patterns:
            total_deleted += self.invalidate_pattern(pattern)
        return total_deleted

    def health_check(self) -> bool:
        """Check if cache service is healthy"""
        if not self.redis_client:
            return False
        try:
            return self.redis_client.ping()
        except redis.RedisError:
            return False





cache_service = CacheService()