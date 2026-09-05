"""
AURUM Real-Time Tick Publisher

Reads normalized ticks from MarketDataGateway
and publishes them to Redis Stream: market_ticks.

Phase 4A.2
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import List

from dotenv import load_dotenv

from src.realtime.event_bus import RedisEventBus
from src.realtime.market_data_gateway import (
    FinnhubProvider,
    MarketDataGateway,
)


ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


MARKET_TICKS_STREAM = "market_ticks"


def build_gateway(
    finnhub_api_key: str,
    tickers: List[str],
) -> MarketDataGateway:
    gateway = MarketDataGateway()

    gateway.register_provider(
        "finnhub",
        FinnhubProvider(finnhub_api_key),
    )

    gateway.subscribe(tickers)

    gateway.connect_all()

    return gateway


def main() -> None:
    finnhub_api_key = os.getenv("FINNHUB_API_KEY")

    if not finnhub_api_key:
        raise ValueError(
            "FINNHUB_API_KEY missing. Add FINNHUB_API_KEY=<your_key> to .env"
        )

    tickers = [
        "BINANCE:BTCUSDT",
    ]

    bus = RedisEventBus()

    gateway = build_gateway(
        finnhub_api_key=finnhub_api_key,
        tickers=tickers,
    )

    logger.info(
        f"Publishing live ticks to Redis stream: {MARKET_TICKS_STREAM}"
    )

    tick_count = 0
    start_time = time.time()

    for tick in gateway.stream():
        bus.publish(
            MARKET_TICKS_STREAM,
            tick,
        )

        tick_count += 1

        if tick_count % 1000 == 0:
            elapsed = max(time.time() - start_time, 1)
            ticks_per_second = tick_count / elapsed

            logger.info(
                f"Published {tick_count} ticks "
                f"to {MARKET_TICKS_STREAM} "
                f"({ticks_per_second:.2f} ticks/sec)"
            )


if __name__ == "__main__":
    main()