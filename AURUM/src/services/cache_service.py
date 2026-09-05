import json
from src.services.redis_client import get_redis_client


CACHE_TTL_SECONDS = 300


def set_cache(key: str, value: dict, ttl: int = CACHE_TTL_SECONDS):

    redis_client = get_redis_client()

    redis_client.set(
        key,
        json.dumps(value),
        ex=ttl,
    )


def get_cache(key: str):

    redis_client = get_redis_client()

    value = redis_client.get(key)

    if value is None:
        return None

    return json.loads(value)