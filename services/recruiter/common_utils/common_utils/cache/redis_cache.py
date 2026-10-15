from django_redis import get_redis_connection

class RedisClient:
    """
    Wrapper over django_redis connection with common helpers.
    from common_core.cache.redis_cache import redis_client
            redis_client.set("count", 10)
            value = redis_client.get("count")
    """

    def __init__(self, alias="default"):
        self.alias = alias
        
    @property
    def conn(self):
        return get_redis_connection(self.alias)

    def set(self, key, value, ttl=None):
        self.conn.set(key, value, ex=ttl)

    def get(self, key):
        return self.conn.get(key)

    def delete(self, key):
        return self.conn.delete(key)

    def incr(self, key, amount=1):
        return self.conn.incr(key, amount)

    def exists(self, key):
        return self.conn.exists(key)

    def expire(self, key, ttl):
        self.conn.expire(key, ttl)

    def ping(self):
        return self.conn.ping()


redis_client = None

def get_redis_client(alias="default"):
    global redis_client
    if redis_client is None:
        redis_client = RedisClient(alias)
    return redis_client