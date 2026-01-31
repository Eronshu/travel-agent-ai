# backend/app/tools/cache.py
import functools
import json
import hashlib
import os
from datetime import timedelta

# 尝试导入 redis，如果没有安装或连不上，就用内存字典代替
try:
    import redis
    # 尝试连接本地 Redis (默认端口 6379)
    redis_client = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=1)
    redis_client.ping() # 测试连接
    HAS_REDIS = True
    print("✅ Redis 连接成功，启用高性能分布式缓存。")
except Exception as e:
    HAS_REDIS = False
    print(f"⚠️ 未检测到 Redis 服务 ({str(e)})，降级使用本地内存缓存。")
    # 内存缓存字典 (key: value)
    _local_cache = {}

def get_cache_key(func_name, args, kwargs):
    """生成唯一的缓存 Key"""
    # 把参数序列化，防止字典顺序不同导致 key 不同
    arg_str = json.dumps(args, sort_keys=True) + json.dumps(kwargs, sort_keys=True)
    # 用 MD5 生成短 hash
    hash_str = hashlib.md5(arg_str.encode()).hexdigest()
    return f"cache:{func_name}:{hash_str}"

def cached_tool(ttl_seconds=300):
    """
    缓存装饰器：给工具加上记忆能力
    :param ttl_seconds: 缓存有效期 (默认 5 分钟)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 1. 生成 Key
            cache_key = get_cache_key(func.__name__, args, kwargs)
            
            # 2. 查缓存
            if HAS_REDIS:
                cached_result = redis_client.get(cache_key)
                if cached_result:
                    print(f"⚡ [Cache Hit] 命中缓存: {func.__name__}")
                    return cached_result.decode('utf-8')
            else:
                if cache_key in _local_cache:
                    print(f"⚡ [Local Cache Hit] 命中内存缓存: {func.__name__}")
                    return _local_cache[cache_key]

            # 3. 没命中，执行原函数
            print(f"🐢 [Cache Miss] 调用 API: {func.__name__}")
            result = func(*args, **kwargs)
            
            # 4. 存入缓存
            if HAS_REDIS:
                redis_client.setex(cache_key, timedelta(seconds=ttl_seconds), str(result))
            else:
                _local_cache[cache_key] = str(result)
                
            return result
        return wrapper
    return decorator