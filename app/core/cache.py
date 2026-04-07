from functools import wraps
from typing import Any, Callable, Optional
import asyncio
from datetime import datetime, timedelta

class SimpleCache:
    """Simple in-memory cache with TTL support"""
    
    def __init__(self):
        self._cache: dict[str, tuple[Any, datetime]] = {}
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        async with self._lock:
            if key in self._cache:
                value, expiry = self._cache[key]
                if datetime.now() < expiry:
                    return value
                else:
                    del self._cache[key]
            return None
    
    async def set(self, key: str, value: Any, ttl_seconds: int = 300):
        """Set value in cache with TTL"""
        async with self._lock:
            expiry = datetime.now() + timedelta(seconds=ttl_seconds)
            self._cache[key] = (value, expiry)
    
    async def delete(self, key: str):
        """Delete key from cache"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
    
    async def clear(self):
        """Clear all cache"""
        async with self._lock:
            self._cache.clear()
    
    async def cleanup_expired(self):
        """Remove expired entries"""
        async with self._lock:
            now = datetime.now()
            expired_keys = [k for k, (_, exp) in self._cache.items() if now >= exp]
            for key in expired_keys:
                del self._cache[key]

# Global cache instance
cache = SimpleCache()

def cached(ttl_seconds: int = 300, key_prefix: str = ""):
    """Decorator for caching async function results"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl_seconds)
            return result
        
        return wrapper
    return decorator
