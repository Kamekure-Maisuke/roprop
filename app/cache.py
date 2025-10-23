import json

from redis.asyncio import Redis

from app.config import REDIS_URL

redis = Redis.from_url(REDIS_URL, decode_responses=True)


async def get_cached(key: str):
    if data := await redis.get(key):
        return json.loads(data)


async def set_cached(key: str, value, ttl: int = 300):
    await redis.setex(key, ttl, json.dumps(value, default=str))


async def delete_cached(*keys: str):
    if keys:
        await redis.delete(*keys)
