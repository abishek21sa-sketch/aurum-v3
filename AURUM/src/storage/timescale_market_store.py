"""
AURUM Timescale/Postgres Market Store

Phase 4A.3
Stores real-time market events.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Dict

import psycopg2
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


class TimescaleMarketStore:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            dbname=os.getenv("POSTGRES_DB", "aurum"),
            user=os.getenv("POSTGRES_USER", "aurum"),
            password=os.getenv("POSTGRES_PASSWORD", "aurum"),
        )

        self.conn.autocommit = True
        logger.info("Connected to Postgres/Timescale market store")

    def initialize_schema(self) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS market_ticks (
                    event_id UUID PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    ticker TEXT NOT NULL,
                    timestamp TIMESTAMPTZ NOT NULL,
                    price DOUBLE PRECISION NOT NULL,
                    volume DOUBLE PRECISION,
                    provider TEXT NOT NULL,
                    inserted_at TIMESTAMPTZ DEFAULT NOW()
                );
                """
            )

            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_market_ticks_ticker_time
                ON market_ticks (ticker, timestamp DESC);
                """
            )

        logger.info("Market tick schema initialized")

    def insert_tick(self, tick: Dict) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO market_ticks (
                    event_id,
                    event_type,
                    ticker,
                    timestamp,
                    price,
                    volume,
                    provider
                )
                VALUES (
                    %(event_id)s,
                    %(event_type)s,
                    %(ticker)s,
                    %(timestamp)s,
                    %(price)s,
                    %(volume)s,
                    %(provider)s
                )
                ON CONFLICT (event_id) DO NOTHING;
                """,
                tick,
            )

    def close(self) -> None:
        self.conn.close()


if __name__ == "__main__":
    store = TimescaleMarketStore()
    store.initialize_schema()
    store.close()