import redis
from typing import List


class SaveItemsService:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    def save_item(self, user_id: str, item_id: int) -> bool:
        key = f"saved:{user_id}"
        result = self.redis.sadd(key, item_id)
        self.redis.expire(key, 2592000)  # always refresh the 30-day TTL
        return result == 1

    def unsave_item(self, user_id: str, item_id: int) -> bool:
        key = f"saved:{user_id}"
        return self.redis.srem(key, item_id) == 1

    def get_saved_items(self, user_id: str) -> List[int]:
        key = f"saved:{user_id}"
        return list(self.redis.smembers(key))

    def is_saved(self, user_id: str, item_id: int) -> bool:
        key = f"saved:{user_id}"
        return self.redis.sismember(key, item_id)

    def get_saved_count(self, user_id: str) -> int:
        key = f"saved:{user_id}"
        return self.redis.scard(key)

    def clear_saved(self, user_id: str) -> bool:
        key = f"saved:{user_id}"
        return self.redis.delete(key) == 1
