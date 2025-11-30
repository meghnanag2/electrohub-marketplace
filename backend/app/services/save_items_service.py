import redis
from typing import List, Dict

class SaveItemsService:
    """
    Redis-backed saved items (wishlist)
    
    Datacenter Scaling:
    - O(1) operations
    - Distributed Redis cluster ready
    - Memory: ~100 bytes per saved item
    - Supports millions of users
    """
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    def save_item(self, user_id: str, item_id: int) -> bool:
        """Add item to saved list"""
        key = f"saved:{user_id}"
        
        # Add to set (no duplicates)
        result = self.redis.sadd(key, item_id)
        
        if result == 1:
            # Set expiration: 30 days
            self.redis.expire(key, 2592000)
            return True
        
        return False
    
    def unsave_item(self, user_id: str, item_id: int) -> bool:
        """Remove item from saved"""
        key = f"saved:{user_id}"
        result = self.redis.srem(key, item_id)
        return result == 1
    
    def get_saved_items(self, user_id: str) -> List[int]:
        """Get all saved item IDs"""
        key = f"saved:{user_id}"
        return list(self.redis.smembers(key))
    
    def is_saved(self, user_id: str, item_id: int) -> bool:
        """Check if item is saved"""
        key = f"saved:{user_id}"
        return self.redis.sismember(key, item_id)
    
    def get_saved_count(self, user_id: str) -> int:
        """Count saved items"""
        key = f"saved:{user_id}"
        return self.redis.scard(key)
    
    def clear_saved(self, user_id: str) -> bool:
        """Clear all saved items"""
        key = f"saved:{user_id}"
        return self.redis.delete(key) == 1
