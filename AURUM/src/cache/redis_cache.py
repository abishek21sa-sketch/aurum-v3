# src/cache/redis_cache.py

import json
from typing import Any

import redis

from src.config.config_loader import load_config
from src.logging.runtime_logger import get_logger


config = load_config()
logger = get_logger("cache.redis")


CACHE_CONFIG = config.get("cache", {})

REDIS_HOST = CACHE_CONFIG.get("host", "localhost")
REDIS_PORT = CACHE_CONFIG.get("port", 6379)
REDIS_DB = CACHE_CONFIG.get("db", 0)
DEFAULT_TTL_SECONDS = CACHE_CONFIG.get("default_ttl_seconds", 3600)


class RedisCache:

    def __init__(self):
        self.client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1,
            retry_on_timeout=False,
        )

    def ping(self) -> bool:
        try:
            result = self.client.ping()

            logger.info(
                "Redis ping successful | host=%s | port=%s",
                REDIS_HOST,
                REDIS_PORT,
            )

            return bool(result)

        except Exception as exc:
            logger.error("Redis ping failed: %s", exc)
            return False

    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
    ) -> bool:

        ttl = ttl_seconds or DEFAULT_TTL_SECONDS

        try:
            self.client.setex(
                key,
                ttl,
                json.dumps(value),
            )

            logger.info(
                "Redis cache set | key=%s | ttl_seconds=%s",
                key,
                ttl,
            )

            return True

        except Exception as exc:
            logger.error(
                "Redis cache set failed | key=%s | error=%s",
                key,
                exc,
            )

            return False

    def get(self, key: str) -> Any:

        try:
            value = self.client.get(key)

            if value is None:
                logger.info(
                    "Redis cache miss | key=%s",
                    key,
                )
                return None

            logger.info(
                "Redis cache hit | key=%s",
                key,
            )

            return json.loads(value)

        except Exception as exc:
            logger.error(
                "Redis cache get failed | key=%s | error=%s",
                key,
                exc,
            )

            return None

    def delete(self, key: str) -> bool:

        try:
            self.client.delete(key)

            logger.info(
                "Redis cache delete | key=%s",
                key,
            )

            return True

        except Exception as exc:
            logger.error(
                "Redis cache delete failed | key=%s | error=%s",
                key,
                exc,
            )

            return False


def main():

    logger.info("=" * 90)
    logger.info("AURUM REDIS CACHE LAYER")
    logger.info("=" * 90)

    cache = RedisCache()

    if cache.ping():

        cache.set(
            "aurum_test",
            {
                "status": "alive",
                "source": "aurum",
            },
            ttl_seconds=60,
        )

        result = cache.get("aurum_test")

        logger.info(
            "Redis test result: %s",
            result,
        )

        cache.delete("aurum_test")

        logger.info("Redis cache validation completed successfully.")

    else:
        logger.error("Redis unavailable.")


if __name__ == "__main__":
    main()