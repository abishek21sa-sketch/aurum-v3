"""
AURUM Tick Storage Consumer

Consumes market_ticks from Redis Streams
and stores them in Postgres/Timescale.

Phase 4A.3
"""

from __future__ import annotations

import logging
import time

from src.realtime.event_bus import RedisEventBus
from src.storage.timescale_market_store import TimescaleMarketStore


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


STREAM_NAME = "market_ticks"
GROUP_NAME = "tick_storage_group"
CONSUMER_NAME = "tick_storage_consumer_1"


def main() -> None:
    bus = RedisEventBus()

    bus.create_consumer_group(
        stream_name=STREAM_NAME,
        group_name=GROUP_NAME,
    )

    store = TimescaleMarketStore()
    store.initialize_schema()

    stored_count = 0
    start_time = time.time()

    logger.info("Tick storage consumer started")

    while True:
        events = bus.consume(
            stream_name=STREAM_NAME,
            group_name=GROUP_NAME,
            consumer_name=CONSUMER_NAME,
            count=100,
            block_ms=5000,
        )

        if not events:
            logger.info("No new ticks received")
            continue

        for item in events:
            message_id = item["message_id"]
            tick = item["event"]

            store.insert_tick(tick)

            bus.acknowledge(
                stream_name=STREAM_NAME,
                group_name=GROUP_NAME,
                message_id=message_id,
            )

            stored_count += 1

        if stored_count % 1000 == 0:
            elapsed = max(time.time() - start_time, 1)
            rate = stored_count / elapsed

            logger.info(
                f"Stored {stored_count} ticks "
                f"from {STREAM_NAME} "
                f"({rate:.2f} ticks/sec)"
            )


if __name__ == "__main__":
    main()