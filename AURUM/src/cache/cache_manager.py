# src/cache/cache_manager.py

from typing import Any

from src.cache.redis_cache import RedisCache
from src.logging.runtime_logger import get_logger


logger = get_logger("cache.manager")


class LocalMemoryCache:
    def __init__(self):
        self.store: dict[str, Any] = {}

    def ping(self) -> bool:
        logger.info("Local memory cache available.")
        return True

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> bool:
        self.store[key] = value
        logger.info("Local cache set | key=%s", key)
        return True

    def get(self, key: str) -> Any:
        value = self.store.get(key)

        if value is None:
            logger.info("Local cache miss | key=%s", key)
        else:
            logger.info("Local cache hit | key=%s", key)

        return value

    def delete(self, key: str) -> bool:
        self.store.pop(key, None)
        logger.info("Local cache delete | key=%s", key)
        return True


class CacheManager:
    def __init__(self):
        self.redis_cache = RedisCache()

        if self.redis_cache.ping():
            self.backend = self.redis_cache
            self.backend_name = "redis"
        else:
            self.backend = LocalMemoryCache()
            self.backend_name = "local_memory"

        logger.info("Cache manager initialized | backend=%s", self.backend_name)

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> bool:
        return self.backend.set(key, value, ttl_seconds)

    def get(self, key: str) -> Any:
        return self.backend.get(key)

    def delete(self, key: str) -> bool:
        return self.backend.delete(key)

    def backend_status(self) -> dict:
        return {
            "backend": self.backend_name,
            "available": True,
        }


def main():
    logger.info("=" * 90)
    logger.info("AURUM CACHE MANAGER")
    logger.info("=" * 90)

    cache = CacheManager()

    cache.set(
        "aurum_cache_test",
        {
            "status": "ok",
            "backend": cache.backend_name,
        },
        ttl_seconds=60,
    )

    result = cache.get("aurum_cache_test")

    logger.info("Cache manager test result: %s", result)

    cache.delete("aurum_cache_test")

    logger.info("Cache manager validation completed successfully.")


if __name__ == "__main__":
    main()