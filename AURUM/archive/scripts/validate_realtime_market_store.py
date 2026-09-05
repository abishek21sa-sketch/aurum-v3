"""
Validate AURUM Real-Time Market Store

Checks:
- Redis connection
- market_ticks stream exists
- Postgres connection
- market_ticks table exists
- latest stored tick is readable
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

import psycopg2
import redis
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


def validate_redis() -> None:
    client = redis.Redis(
        host="localhost",
        port=6379,
        db=0,
        decode_responses=True,
    )

    client.ping()
    logger.info("[PASS] Redis connection")

    stream_name = "market_ticks"

    stream_length = client.xlen(stream_name)

    if stream_length <= 0:
        raise RuntimeError("[FAIL] Redis stream market_ticks is empty")

    logger.info(f"[PASS] Redis stream market_ticks length = {stream_length}")

    latest = client.xrevrange(stream_name, count=1)[0]

    message_id, fields = latest
    event = json.loads(fields["event"])

    logger.info(
        f"[PASS] Latest Redis tick: "
        f"id={message_id}, "
        f"ticker={event.get('ticker')}, "
        f"price={event.get('price')}"
    )


def validate_postgres() -> None:
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=os.getenv("POSTGRES_DB", "aurum"),
        user=os.getenv("POSTGRES_USER", "aurum"),
        password=os.getenv("POSTGRES_PASSWORD", "aurum"),
    )

    logger.info("[PASS] Postgres connection")

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'market_ticks'
            );
            """
        )

        table_exists = cur.fetchone()[0]

        if not table_exists:
            raise RuntimeError("[FAIL] market_ticks table does not exist")

        logger.info("[PASS] market_ticks table exists")

        cur.execute("SELECT COUNT(*) FROM market_ticks;")
        row_count = cur.fetchone()[0]

        if row_count <= 0:
            raise RuntimeError("[FAIL] market_ticks table is empty")

        logger.info(f"[PASS] market_ticks row count = {row_count}")

        cur.execute(
            """
            SELECT event_id, ticker, timestamp, price, volume, provider
            FROM market_ticks
            ORDER BY timestamp DESC
            LIMIT 1;
            """
        )

        latest = cur.fetchone()

        logger.info(
            "[PASS] Latest Postgres tick: "
            f"event_id={latest[0]}, "
            f"ticker={latest[1]}, "
            f"timestamp={latest[2]}, "
            f"price={latest[3]}, "
            f"volume={latest[4]}, "
            f"provider={latest[5]}"
        )

    conn.close()


def main() -> None:
    logger.info("=" * 80)
    logger.info("AURUM REAL-TIME MARKET STORE VALIDATION")
    logger.info("=" * 80)

    validate_redis()
    validate_postgres()

    logger.info("=" * 80)
    logger.info("VALIDATION COMPLETE: REAL-TIME MARKET STORE ONLINE")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()