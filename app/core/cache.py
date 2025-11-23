import redis.asyncio as redis

from .config import settings


class CacheManager:
    def __init__(self):
        self.redis_client = None

    async def init_redis(self):
        self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def get_redis(self):
        if self.redis_client is None:
            await self.init_redis()
        return self.redis_client

    async def close_redis(self):
        if self.redis_client:
            await self.redis_client.close()


cache_manager = CacheManager()
