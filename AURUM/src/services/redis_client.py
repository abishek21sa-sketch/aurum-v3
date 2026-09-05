import redis

from src.core.config import settings
from src.core.logger import get_logger


logger = get_logger("aurum.redis")


def get_redis_client() -> redis.Redis:
    return redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        decode_responses=True,
    )


def check_redis_connection() -> dict:
    try:
        client = get_redis_client()
        client.ping()

        logger.info("Redis connection healthy.")

        return {
            "status": "healthy",
            "host": settings.REDIS_HOST,
            "port": settings.REDIS_PORT,
        }

    except Exception as error:
        logger.error(f"Redis connection failed: {error}")

        return {
            "status": "unhealthy",
            "host": settings.REDIS_HOST,
            "port": settings.REDIS_PORT,
            "error": str(error),
        }


if __name__ == "__main__":
    print(check_redis_connection())