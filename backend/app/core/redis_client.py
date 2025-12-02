# app/core/redis_client.py
from functools import lru_cache
import redis


@lru_cache
def get_redis_client() -> redis.Redis:
    """
    Simple singleton Redis client.
    Host name 'redis' matches the docker-compose service name.
    """
    return redis.Redis(
        host="redis",
        port=6379,
        db=0,
        decode_responses=True,  # strings instead of bytes
    )
