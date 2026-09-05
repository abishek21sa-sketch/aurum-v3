# src/storage/timescale_writer.py

from __future__ import annotations

import argparse
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import psycopg2
from psycopg2.extras import execute_values

from src.realtime.event_bus import RedisEventBus, EVENT_STREAMS


DEFAULT_DATABASE_URL = os.getenv(
    "TIMESCALE_DATABASE_URL",
    "postgresql://aurum:aurum@localhost:5432/aurum",
)


class TimescaleWriter:
    """
    Persists Redis Stream events into TimescaleDB/Postgres.

    Redis = live event bus
    TimescaleDB = durable historical storage
    """

    def __init__(
        self,
        event_bus: RedisEventBus,
        database_url: str = DEFAULT_DATABASE_URL,
        block_ms: int = 5000,
    ) -> None:
        self.event_bus = event_bus
        self.database_url = database_url
        self.block_ms = block_ms

        self.last_ids = {
            EVENT_STREAMS["market_ticks"]: "$",
            EVENT_STREAMS["market_features"]: "$",
            EVENT_STREAMS["alerts"]: "$",
        }

    @staticmethod
    def utc_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
        try:
            if value in ("", None):
                return default
            return float(value)
        except Exception:
            return default

    @staticmethod
    def safe_int(value: Any, default: Optional[int] = None) -> Optional[int]:
        try:
            if value in ("", None):
                return default
            return int(float(value))
        except Exception:
            return default

    @staticmethod
    def safe_text(value: Any, default: str = "") -> str:
        if value is None:
            return default
        return str(value)

    @staticmethod
    def parse_time(value: Any) -> str:
        if value in ("", None):
            return TimescaleWriter.utc_now()
        return str(value)

    def connect(self):
        return psycopg2.connect(self.database_url)

    def initialize_schema(self, schema_path: str = "src/storage/timescale_schema.sql") -> None:
        sql = Path(schema_path).read_text(encoding="utf-8")

        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)

        print("[PASS] Timescale schema initialized")

    def insert_market_ticks(self, rows: List[Dict[str, Any]]) -> int:
        if not rows:
            return 0

        values = []

        for row in rows:
            values.append(
                (
                    self.parse_time(row.get("timestamp")),
                    row.get("redis_id"),
                    row.get("event_type"),
                    row.get("source"),
                    row.get("ticker"),
                    self.safe_float(row.get("price")),
                    self.safe_float(row.get("volume")),
                    self.parse_time(row.get("ingested_at")),
                )
            )

        sql = """
        INSERT INTO market_ticks (
            time, redis_id, event_type, source, ticker, price, volume, ingested_at
        )
        VALUES %s
        """

        with self.connect() as conn:
            with conn.cursor() as cur:
                execute_values(cur, sql, values)

        return len(values)

    def insert_market_features(self, rows: List[Dict[str, Any]]) -> int:
        if not rows:
            return 0

        values = []

        for row in rows:
            values.append(
                (
                    self.parse_time(row.get("timestamp")),
                    row.get("redis_id"),
                    row.get("event_type"),
                    row.get("ticker"),
                    row.get("source"),
                    self.safe_float(row.get("price")),
                    self.safe_float(row.get("volume")),
                    self.safe_float(row.get("return_1m")),
                    self.safe_float(row.get("return_5m")),
                    self.safe_float(row.get("rolling_volatility")),
                    self.safe_float(row.get("momentum")),
                    self.safe_float(row.get("volume_zscore")),
                    row.get("liquidity_state"),
                    row.get("volatility_state"),
                    self.safe_int(row.get("history_size")),
                    self.parse_time(row.get("computed_at")),
                    self.parse_time(row.get("ingested_at")),
                )
            )

        sql = """
        INSERT INTO market_features (
            time, redis_id, event_type, ticker, source, price, volume,
            return_1m, return_5m, rolling_volatility, momentum, volume_zscore,
            liquidity_state, volatility_state, history_size, computed_at, ingested_at
        )
        VALUES %s
        """

        with self.connect() as conn:
            with conn.cursor() as cur:
                execute_values(cur, sql, values)

        return len(values)

    def insert_alerts(self, rows: List[Dict[str, Any]]) -> int:
        if not rows:
            return 0

        values = []

        for row in rows:
            values.append(
                (
                    self.parse_time(row.get("alerted_at")),
                    row.get("redis_id"),
                    row.get("event_type"),
                    row.get("alert_id"),
                    row.get("alert_type"),
                    row.get("ticker"),
                    row.get("severity"),
                    self.safe_int(row.get("severity_rank")),
                    row.get("message"),
                    row.get("metric_name"),
                    self.safe_float(row.get("metric_value")),
                    self.safe_float(row.get("threshold")),
                    self.safe_float(row.get("price")),
                    self.parse_time(row.get("source_event_timestamp")),
                    self.parse_time(row.get("computed_at")),
                    self.parse_time(row.get("alerted_at")),
                    self.parse_time(row.get("ingested_at")),
                )
            )

        sql = """
        INSERT INTO realtime_alerts (
            time, redis_id, event_type, alert_id, alert_type, ticker,
            severity, severity_rank, message, metric_name, metric_value,
            threshold, price, source_event_timestamp, computed_at, alerted_at,
            ingested_at
        )
        VALUES %s
        """

        with self.connect() as conn:
            with conn.cursor() as cur:
                execute_values(cur, sql, values)

        return len(values)

    def persist_stream_batch(self, stream_name: str, rows: List[Dict[str, Any]]) -> int:
        if stream_name == EVENT_STREAMS["market_ticks"]:
            return self.insert_market_ticks(rows)

        if stream_name == EVENT_STREAMS["market_features"]:
            return self.insert_market_features(rows)

        if stream_name == EVENT_STREAMS["alerts"]:
            return self.insert_alerts(rows)

        return 0

    def run_forever(self) -> None:
        print("=" * 80)
        print("AURUM TIMESCALEDB PERSISTENCE WRITER")
        print("=" * 80)
        print(f"Database URL: {self.database_url}")
        print("Streams: market_ticks, market_features, alerts")
        print("=" * 80)

        self.initialize_schema()

        while True:
            total_inserted = 0

            for stream_name in list(self.last_ids.keys()):
                events = self.event_bus.read_from(
                    stream_name=stream_name,
                    last_id=self.last_ids[stream_name],
                    block_ms=self.block_ms,
                    count=250,
                )

                if not events:
                    continue

                self.last_ids[stream_name] = events[-1]["redis_id"]

                inserted = self.persist_stream_batch(stream_name, events)
                total_inserted += inserted

                print(
                    f"[PERSIST] {stream_name} | "
                    f"events={len(events)} | inserted={inserted} | "
                    f"last_id={self.last_ids[stream_name]}"
                )

            if total_inserted == 0:
                time.sleep(0.25)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run AURUM TimescaleDB writer.")
    parser.add_argument("--database-url", default=DEFAULT_DATABASE_URL)
    parser.add_argument("--block-ms", type=int, default=5000)
    parser.add_argument("--init-only", action="store_true")

    args = parser.parse_args()

    bus = RedisEventBus()
    writer = TimescaleWriter(
        event_bus=bus,
        database_url=args.database_url,
        block_ms=args.block_ms,
    )

    if args.init_only:
        writer.initialize_schema()
    else:
        writer.run_forever()


if __name__ == "__main__":
    main()