"""
Multi-Layer Caching System

Implements a sophisticated caching strategy:
- L1 Cache: In-memory LRU cache (fastest)
- L2 Cache: Redis cache (distributed, persistent)
- Cache warming, invalidation, and analytics
"""

import hashlib
import json
import time
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timedelta
from threading import Lock
from typing import Any, Callable, Dict, Optional, Tuple

from src.core import get_logger

logger = get_logger(__name__)


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class CacheEntry:
    """Single cache entry."""
    
    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime]
    hit_count: int = 0
    last_accessed: datetime = None
    
    def is_expired(self) -> bool:
        """Check if entry is expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def ttl(self) -> Optional[float]:
        """Time to live in seconds."""
        if self.expires_at is None:
            return None
        return (self.expires_at - datetime.now()).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'key': self.key,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'hit_count': self.hit_count,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
            'ttl_seconds': self.ttl(),
        }


@dataclass
class CacheStats:
    """Cache statistics."""
    
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    expirations: int = 0
    total_gets: int = 0
    total_sets: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        if self.total_gets == 0:
            return 0.0
        return self.hits / self.total_gets
    
    @property
    def miss_rate(self) -> float:
        """Calculate cache miss rate."""
        return 1.0 - self.hit_rate
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'hits': self.hits,
            'misses': self.misses,
            'evictions': self.evictions,
            'expirations': self.expirations,
            'total_gets': self.total_gets,
            'total_sets': self.total_sets,
            'hit_rate': self.hit_rate,
            'miss_rate': self.miss_rate,
        }


# ============================================================================
# LRU Cache (L1 - In-Memory)
# ============================================================================

class LRUCache:
    """
    Least Recently Used (LRU) cache.
    
    In-memory cache with automatic eviction of least recently used items.
    """
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize LRU cache.
        
        Args:
            max_size: Maximum number of items to cache
        """
        self.max_size = max_size
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stats = CacheStats()
        
        self._lock = Lock()
        
        logger.info(f"Initialized LRUCache: max_size={max_size}")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            self.stats.total_gets += 1
            
            if key not in self.cache:
                self.stats.misses += 1
                return None
            
            entry = self.cache[key]
            
            # Check expiration
            if entry.is_expired():
                self.stats.misses += 1
                self.stats.expirations += 1
                del self.cache[key]
                return None
            
            # Hit - move to end (most recently used)
            self.cache.move_to_end(key)
            entry.hit_count += 1
            entry.last_accessed = datetime.now()
            
            self.stats.hits += 1
            return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (None = no expiration)
        """
        with self._lock:
            self.stats.total_sets += 1
            
            # Create entry
            expires_at = datetime.now() + timedelta(seconds=ttl) if ttl else None
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                expires_at=expires_at,
                last_accessed=datetime.now(),
            )
            
            # Add or update
            if key in self.cache:
                del self.cache[key]
            
            self.cache[key] = entry
            self.cache.move_to_end(key)
            
            # Evict if over capacity
            if len(self.cache) > self.max_size:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                self.stats.evictions += 1
                logger.debug(f"Evicted LRU entry: {oldest_key}")
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        with self._lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            self.cache.clear()
            logger.info("LRU cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats_dict = self.stats.to_dict()
        stats_dict['current_size'] = len(self.cache)
        stats_dict['max_size'] = self.max_size
        stats_dict['utilization'] = len(self.cache) / self.max_size if self.max_size > 0 else 0
        return stats_dict
    
    def get_all_entries(self) -> Dict[str, Dict[str, Any]]:
        """Get all cache entries (for debugging)."""
        with self._lock:
            return {k: v.to_dict() for k, v in self.cache.items()}


# ============================================================================
# Multi-Layer Cache Manager
# ============================================================================

class CacheManager:
    """
    Multi-layer cache manager.
    
    Implements tiered caching strategy:
    - L1: In-memory LRU cache (fastest)
    - L2: Redis cache (distributed) - placeholder for now
    """
    
    def __init__(
        self,
        l1_size: int = 1000,
        default_ttl: int = 300,  # 5 minutes
    ):
        """
        Initialize cache manager.
        
        Args:
            l1_size: Size of L1 cache
            default_ttl: Default TTL in seconds
        """
        self.l1_cache = LRUCache(max_size=l1_size)
        self.default_ttl = default_ttl
        
        # TODO: Initialize Redis cache (L2)
        self.l2_cache = None  # Placeholder
        
        logger.info(
            f"Initialized CacheManager: "
            f"l1_size={l1_size}, default_ttl={default_ttl}s"
        )
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache (checks L1, then L2).
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        # Try L1 first
        value = self.l1_cache.get(key)
        if value is not None:
            return value
        
        # Try L2 (Redis) - not yet implemented
        # if self.l2_cache:
        #     value = self.l2_cache.get(key)
        #     if value is not None:
        #         # Promote to L1
        #         self.l1_cache.set(key, value, self.default_ttl)
        #         return value
        
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set value in cache (writes to both L1 and L2).
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        ttl = ttl or self.default_ttl
        
        # Write to L1
        self.l1_cache.set(key, value, ttl)
        
        # Write to L2 (Redis) - not yet implemented
        # if self.l2_cache:
        #     self.l2_cache.set(key, value, ttl)
    
    def delete(self, key: str):
        """Delete key from all cache layers."""
        self.l1_cache.delete(key)
        # TODO: Delete from L2
    
    def clear(self):
        """Clear all cache layers."""
        self.l1_cache.clear()
        # TODO: Clear L2
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'l1': self.l1_cache.get_stats(),
            'l2': {'status': 'not_implemented'},  # Placeholder
        }
    
    def cached(self, ttl: Optional[int] = None, key_func: Optional[Callable] = None):
        """
        Decorator for caching function results.
        
        Args:
            ttl: Cache TTL in seconds
            key_func: Custom function to generate cache key
            
        Returns:
            Decorated function
        """
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    cache_key = self._make_key(func.__name__, args, kwargs)
                
                # Try to get from cache
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    logger.debug(f"Cache hit: {cache_key}")
                    return cached_value
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Cache result
                self.set(cache_key, result, ttl)
                logger.debug(f"Cached result: {cache_key}")
                
                return result
            
            return wrapper
        return decorator
    
    def _make_key(self, func_name: str, args: Tuple, kwargs: Dict) -> str:
        """Generate cache key from function signature."""
        # Create deterministic key from function name + args
        key_parts = [func_name]
        key_parts.extend(str(arg) for arg in args)
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        
        key_str = '|'.join(key_parts)
        return hashlib.md5(key_str.encode()).hexdigest()


# ============================================================================
# Singleton Instance
# ============================================================================

cache_manager = CacheManager(
    l1_size=1000,
    default_ttl=300,
)
