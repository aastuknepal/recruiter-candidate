def get_redis_cache_config(
    host="127.0.0.1",
    port=6379,
    db=0,
    password=None,
    timeout=300,
):
    """
    Returns a Redis-backed Django CACHES config.
    
    Your Django project can simply do:
                from common_core.cache.backends import get_redis_cache_config
                CACHES = get_redis_cache_config(host="my-redis-host", db=10)
    """

    location = f"redis://{password + '@' if password else ''}{host}:{port}/{db}"

    return {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": location,
            "TIMEOUT": timeout,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "SERIALIZER": "django_redis.serializers.json.JSONSerializer",
                "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
                "SOCKET_CONNECT_TIMEOUT": 2,  # Prevent hanging
                "SOCKET_TIMEOUT": 2,
            }
        }
    }