"""
缓存处理器
提供内存缓存和Redis缓存支持，提高数据库查询性能
"""

import asyncio
import hashlib
import json
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Optional


class MemoryCache:
    """内存缓存实现"""

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self._lock:
            if key in self._cache:
                item = self._cache[key]
                if item["expires_at"] > datetime.now():
                    return item["value"]
                else:
                    del self._cache[key]
            return None

    def set(self, key: str, value: Any, ttl: int = 3600):
        """设置缓存值"""
        with self._lock:
            expires_at = datetime.now() + timedelta(seconds=ttl)
            self._cache[key] = {
                "value": value,
                "expires_at": expires_at,
                "created_at": datetime.now(),
            }

    def delete(self, key: str):
        """删除缓存值"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]

    def clear(self):
        """清空所有缓存"""
        with self._lock:
            self._cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self._lock:
            total_items = len(self._cache)
            expired_items = sum(
                1
                for item in self._cache.values()
                if item["expires_at"] <= datetime.now()
            )
            return {
                "total_items": total_items,
                "expired_items": expired_items,
                "active_items": total_items - expired_items,
            }


class RedisCache:
    """Redis缓存实现"""

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        try:
            import redis

            self._redis = redis.Redis(
                host=host, port=port, db=db, decode_responses=True
            )
            self._redis.ping()  # 测试连接
            self._available = True
        except ImportError:
            print("Redis库未安装，将使用内存缓存")
            self._available = False
        except Exception as e:
            print(f"Redis连接失败: {e}，将使用内存缓存")
            self._available = False

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if not self._available:
            return None

        try:
            value = self._redis.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            print(f"Redis获取缓存失败: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 3600):
        """设置缓存值"""
        if not self._available:
            return

        try:
            self._redis.setex(key, ttl, json.dumps(value))
        except Exception as e:
            print(f"Redis设置缓存失败: {e}")

    def delete(self, key: str):
        """删除缓存值"""
        if not self._available:
            return

        try:
            self._redis.delete(key)
        except Exception as e:
            print(f"Redis删除缓存失败: {e}")

    def clear(self):
        """清空所有缓存"""
        if not self._available:
            return

        try:
            self._redis.flushdb()
        except Exception as e:
            print(f"Redis清空缓存失败: {e}")


class CacheHandler:
    """缓存处理器主类"""

    def __init__(self, cache_type: str = "memory", **kwargs):
        """
        初始化缓存处理器

        Args:
            cache_type: 缓存类型 ('memory' 或 'redis')
            **kwargs: Redis连接参数
        """
        self.cache_type = cache_type

        if cache_type == "redis":
            self._cache = RedisCache(**kwargs)
        else:
            self._cache = MemoryCache()

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        return self._cache.get(key)

    def set(self, key: str, value: Any, ttl: int = 3600):
        """设置缓存值"""
        self._cache.set(key, value, ttl)

    def delete(self, key: str):
        """删除缓存值"""
        self._cache.delete(key)

    def clear(self):
        """清空所有缓存"""
        self._cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        if hasattr(self._cache, "get_stats"):
            return self._cache.get_stats()
        return {"cache_type": self.cache_type}

    def generate_cache_key(self, *args, **kwargs) -> str:
        """生成缓存键"""
        # 将参数转换为字符串并生成MD5哈希
        key_parts = []

        for arg in args:
            key_parts.append(str(arg))

        for key, value in sorted(kwargs.items()):
            key_parts.append(f"{key}:{value}")

        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    def cache_query_result(
        self, query: str, params: tuple = None, result: Any = None, ttl: int = 1800
    ):
        """缓存查询结果"""
        cache_key = self.generate_cache_key("query", query, params)
        self.set(
            cache_key,
            {
                "query": query,
                "params": params,
                "result": result,
                "cached_at": datetime.now().isoformat(),
            },
            ttl,
        )
        return cache_key

    def get_cached_query_result(
        self, query: str, params: tuple = None
    ) -> Optional[Any]:
        """获取缓存的查询结果"""
        cache_key = self.generate_cache_key("query", query, params)
        cached_data = self.get(cache_key)
        if cached_data:
            return cached_data.get("result")
        return None


# 缓存装饰器
def cached(ttl: int = 1800, key_prefix: str = ""):
    """缓存装饰器"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            # 获取缓存服务
            from .dependency_injection import get_service

            cache_service = get_service("ICacheService")

            # 生成缓存键
            cache_key = cache_service.generate_cache_key(
                key_prefix, func.__name__, *args, **kwargs
            )

            # 尝试从缓存获取
            cached_result = cache_service.get(cache_key)
            if cached_result is not None:
                return cached_result

            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache_service.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator


class AsyncCacheHandler:
    """异步缓存处理器"""

    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self.memory_cache = {}
        self.memory_expirations = {}

    async def get(self, key: str, default: Optional[Any] = None) -> Any:
        """获取缓存值"""
        try:
            if self.redis_client:
                value = await self.redis_client.get(key)
                if value is None:
                    return default
                return json.loads(value)
            else:
                return self.memory_cache.get(key, default)
        except Exception:
            return default

    async def set(
        self, key: str, value: Any, ttl: Optional[int] = None
    ) -> bool:
        """设置缓存值"""
        try:
            if self.redis_client:
                serialized_value = json.dumps(value, default=str)
                if ttl:
                    await self.redis_client.setex(key, ttl, serialized_value)
                else:
                    await self.redis_client.set(key, serialized_value)
            else:
                self.memory_cache[key] = value
                if ttl:
                    self.memory_expirations[key] = time.time() + ttl
            return True
        except Exception:
            return False

    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        try:
            if self.redis_client:
                await self.redis_client.delete(key)
            else:
                self.memory_cache.pop(key, None)
                self.memory_expirations.pop(key, None)
            return True
        except Exception:
            return False

    async def execute_with_cache(
        self,
        key: str,
        func: Callable,
        params: Optional[tuple] = None,
        ttl: int = 300,
    ) -> Any:
        """执行函数并缓存结果"""
        if params is None:
            params = ()
            
        # 尝试从缓存获取
        cached_result = await self.get(key)
        if cached_result is not None:
            return cached_result

        # 执行函数
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*params)
            else:
                result = func(*params)
            
            # 缓存结果
            await self.set(key, result, ttl)
            return result
        except Exception as e:
            raise e

    async def execute_with_cache_async(
        self,
        key: str,
        func: Callable,
        params: Optional[tuple] = None,
        ttl: int = 300,
    ) -> Any:
        """异步执行函数并缓存结果"""
        if params is None:
            params = ()
            
        # 尝试从缓存获取
        cached_result = await self.get(key)
        if cached_result is not None:
            return cached_result

        # 执行函数
        result = await func(*params)
        
        # 缓存结果
        await self.set(key, result, ttl)
        return result
