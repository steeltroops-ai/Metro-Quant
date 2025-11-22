"""Cache manager with TTL support for data persistence.

This module provides caching functionality to support fallback when data sources fail.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from collections import OrderedDict

from loguru import logger


class CacheManager:
    """
    Cache manager with time-to-live (TTL) support.
    
    Implements LRU eviction when max_size is reached.
    """
    
    def __init__(self, ttl: int = 300, max_size: int = 1000):
        """
        Initialize cache manager.
        
        Args:
            ttl: Time-to-live in seconds (default: 300)
            max_size: Maximum number of cached items (default: 1000)
        """
        self.ttl = ttl
        self.max_size = max_size
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        logger.info(f"CacheManager initialized with TTL={ttl}s, max_size={max_size}")
    
    def store(self, key: str, data: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """
        Store data with time-to-live.
        
        Args:
            key: Cache key
            data: Data to cache
            ttl: Optional custom TTL in seconds (uses default if not provided)
        """
        # Use custom TTL or default
        cache_ttl = ttl if ttl is not None else self.ttl
        
        # Create cache entry with expiration time
        entry = {
            'data': data,
            'expires_at': datetime.now() + timedelta(seconds=cache_ttl),
            'stored_at': datetime.now()
        }
        
        # Remove key if it exists (to update LRU order)
        if key in self._cache:
            del self._cache[key]
        
        # Add to cache
        self._cache[key] = entry
        
        # Evict oldest item if max size exceeded
        if len(self._cache) > self.max_size:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            logger.debug(f"Cache evicted oldest entry: {oldest_key}")
        
        logger.debug(f"Cached data for key: {key} (TTL={cache_ttl}s)")
    
    def retrieve(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached data if available and fresh.
        
        Args:
            key: Cache key
            
        Returns:
            Cached data if available and not expired, None otherwise
        """
        if key not in self._cache:
            logger.debug(f"Cache miss: {key}")
            return None
        
        entry = self._cache[key]
        
        # Check if expired
        if datetime.now() > entry['expires_at']:
            logger.debug(f"Cache expired: {key}")
            del self._cache[key]
            return None
        
        # Move to end (mark as recently used)
        self._cache.move_to_end(key)
        
        logger.debug(f"Cache hit: {key}")
        return entry['data']
    
    def is_stale(self, key: str, max_age_seconds: int = 300) -> bool:
        """
        Check if cached data is stale (older than max_age).
        
        Args:
            key: Cache key
            max_age_seconds: Maximum age in seconds (default: 300)
            
        Returns:
            True if data is stale or missing, False if fresh
        """
        if key not in self._cache:
            return True
        
        entry = self._cache[key]
        age = (datetime.now() - entry['stored_at']).total_seconds()
        
        return age > max_age_seconds
    
    def invalidate(self, key: str) -> None:
        """
        Invalidate (remove) cached data.
        
        Args:
            key: Cache key to invalidate
        """
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Cache invalidated: {key}")
    
    def clear(self) -> None:
        """Clear all cached data."""
        self._cache.clear()
        logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        now = datetime.now()
        valid_entries = sum(1 for entry in self._cache.values() if now <= entry['expires_at'])
        
        return {
            'total_entries': len(self._cache),
            'valid_entries': valid_entries,
            'expired_entries': len(self._cache) - valid_entries,
            'max_size': self.max_size,
            'utilization': len(self._cache) / self.max_size if self.max_size > 0 else 0
        }
