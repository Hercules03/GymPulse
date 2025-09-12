"""
Cache management utilities for performance optimization
Provides in-memory caching, DynamoDB caching, and cache invalidation strategies
"""
import json
import time
import hashlib
from typing import Dict, Any, Optional, Callable
from functools import wraps
import boto3
from botocore.exceptions import ClientError


class InMemoryCache:
    """
    Simple in-memory cache with TTL support
    """
    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        self.cache = {}
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        if key in self.cache:
            item = self.cache[key]
            if time.time() < item['expires_at']:
                return item['data']
            else:
                # Expired, remove from cache
                del self.cache[key]
        return None
    
    def set(self, key: str, data: Any, ttl: Optional[int] = None) -> None:
        """Set item in cache"""
        if ttl is None:
            ttl = self.default_ttl
        
        self.cache[key] = {
            'data': data,
            'expires_at': time.time() + ttl
        }
    
    def invalidate(self, key: str) -> None:
        """Remove item from cache"""
        if key in self.cache:
            del self.cache[key]
    
    def clear(self) -> None:
        """Clear entire cache"""
        self.cache.clear()
    
    def cleanup_expired(self) -> int:
        """Remove expired items and return count removed"""
        current_time = time.time()
        expired_keys = [
            key for key, item in self.cache.items() 
            if current_time >= item['expires_at']
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        return len(expired_keys)


class DynamoDBCache:
    """
    DynamoDB-based cache for sharing data across Lambda invocations
    """
    def __init__(self, table_name: str, default_ttl: int = 300):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from DynamoDB cache"""
        try:
            response = self.table.get_item(Key={'cache_key': key})
            
            if 'Item' in response:
                item = response['Item']
                current_time = int(time.time())
                
                if current_time < item.get('ttl', 0):
                    return json.loads(item['data'])
                else:
                    # Expired, delete item
                    self.invalidate(key)
            
            return None
            
        except ClientError as e:
            print(f"DynamoDB cache get error for key {key}: {str(e)}")
            return None
    
    def set(self, key: str, data: Any, ttl: Optional[int] = None) -> bool:
        """Set item in DynamoDB cache"""
        try:
            if ttl is None:
                ttl = self.default_ttl
            
            ttl_timestamp = int(time.time()) + ttl
            
            self.table.put_item(
                Item={
                    'cache_key': key,
                    'data': json.dumps(data, default=str),
                    'ttl': ttl_timestamp,
                    'created_at': int(time.time())
                }
            )
            return True
            
        except ClientError as e:
            print(f"DynamoDB cache set error for key {key}: {str(e)}")
            return False
    
    def invalidate(self, key: str) -> bool:
        """Remove item from DynamoDB cache"""
        try:
            self.table.delete_item(Key={'cache_key': key})
            return True
        except ClientError as e:
            print(f"DynamoDB cache invalidate error for key {key}: {str(e)}")
            return False


# Global cache instances
branch_cache = InMemoryCache(ttl=30)  # 30 seconds for branch data
machine_cache = InMemoryCache(ttl=15)  # 15 seconds for machine data
aggregates_cache = InMemoryCache(ttl=300)  # 5 minutes for aggregates


def cache_key(*args, **kwargs) -> str:
    """Generate cache key from function arguments"""
    key_data = json.dumps({'args': args, 'kwargs': sorted(kwargs.items())}, sort_keys=True, default=str)
    return hashlib.md5(key_data.encode()).hexdigest()


def cached(ttl: int = 300, cache_instance: Optional[InMemoryCache] = None):
    """
    Decorator for caching function results
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Use provided cache instance or create default
            cache = cache_instance or InMemoryCache(ttl)
            
            # Generate cache key
            key = f"{func.__name__}:{cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_result = cache.get(key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(key, result, ttl)
            
            return result
        
        # Add cache management methods to the wrapper
        wrapper.cache_invalidate = lambda *args, **kwargs: cache_instance.invalidate(f"{func.__name__}:{cache_key(*args, **kwargs)}") if cache_instance else None
        wrapper.cache_clear = lambda: cache_instance.clear() if cache_instance else None
        
        return wrapper
    return decorator


def batch_cache_invalidation(patterns: list):
    """
    Invalidate multiple cache entries based on patterns
    """
    for pattern in patterns:
        if pattern.startswith('branch'):
            branch_cache.clear()
        elif pattern.startswith('machine'):
            machine_cache.clear()
        elif pattern.startswith('aggregate'):
            aggregates_cache.clear()


class CacheWarmer:
    """
    Cache warming utility for preloading frequently accessed data
    """
    def __init__(self):
        self.warm_functions = []
    
    def register(self, func: Callable, *args, **kwargs):
        """Register a function for cache warming"""
        self.warm_functions.append((func, args, kwargs))
    
    def warm_all(self) -> Dict[str, Any]:
        """Execute all registered warm functions"""
        results = {}
        
        for func, args, kwargs in self.warm_functions:
            try:
                start_time = time.time()
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                results[func.__name__] = {
                    'success': True,
                    'duration': duration,
                    'result_size': len(str(result))
                }
            except Exception as e:
                results[func.__name__] = {
                    'success': False,
                    'error': str(e)
                }
        
        return results


# Connection pooling for DynamoDB
class DynamoDBConnectionPool:
    """
    Simple connection pooling for DynamoDB resources
    """
    def __init__(self):
        self._resource = None
        self._tables = {}
    
    def get_resource(self):
        """Get or create DynamoDB resource"""
        if self._resource is None:
            self._resource = boto3.resource('dynamodb')
        return self._resource
    
    def get_table(self, table_name: str):
        """Get or create table reference with caching"""
        if table_name not in self._tables:
            self._tables[table_name] = self.get_resource().Table(table_name)
        return self._tables[table_name]


# Global connection pool instance
db_pool = DynamoDBConnectionPool()


# Cache invalidation strategies
class CacheInvalidationStrategy:
    """
    Smart cache invalidation based on data dependencies
    """
    
    @staticmethod
    def on_machine_update(machine_id: str, gym_id: str, category: str):
        """Invalidate caches when machine state changes"""
        # Invalidate specific machine cache
        machine_cache.invalidate(f"get_machines:{machine_id}")
        machine_cache.invalidate(f"get_machines:{gym_id}:{category}")
        
        # Invalidate branch summaries
        branch_cache.invalidate(f"get_branches")
        branch_cache.invalidate(f"get_branches:{gym_id}")
        
    @staticmethod
    def on_aggregate_update(machine_id: str):
        """Invalidate caches when aggregates are updated"""
        aggregates_cache.invalidate(f"get_machine_history:{machine_id}")
        
    @staticmethod
    def on_alert_change(user_id: str, machine_id: str):
        """Invalidate caches when alerts are modified"""
        # Alert-specific cache invalidation would go here
        pass


# Performance monitoring for cache operations
class CacheMetrics:
    """
    Track cache performance metrics
    """
    def __init__(self):
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'invalidations': 0
        }
    
    def hit(self):
        self.stats['hits'] += 1
    
    def miss(self):
        self.stats['misses'] += 1
    
    def set(self):
        self.stats['sets'] += 1
    
    def invalidate(self):
        self.stats['invalidations'] += 1
    
    def get_hit_ratio(self) -> float:
        total_requests = self.stats['hits'] + self.stats['misses']
        if total_requests == 0:
            return 0.0
        return self.stats['hits'] / total_requests
    
    def reset(self):
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'invalidations': 0
        }


# Global cache metrics instance
cache_metrics = CacheMetrics()