from redis.asyncio import Redis

from app.config import REDIS_URL

_redis_client: Redis | None = None


async def get_redis() -> Redis:
    """Redis接続を取得"""
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
    return _redis_client


async def close_redis() -> None:
    """Redis接続を閉じる"""
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None
