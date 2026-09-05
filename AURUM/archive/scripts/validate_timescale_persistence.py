# scripts/validate_timescale_persistence.py

from __future__ import annotations

import sys

from src.realtime.event_bus import RedisEventBus, EVENT_STREAMS
from src.storage.timescale_writer import TimescaleWriter


def pass_check(message: str) -> None:
    print(f"[PASS] {message}")


def fail_check(message: str) -> None:
    print(f"[FAIL] {message}")


def query_count(writer: TimescaleWriter, table_name: str) -> int:
    with writer.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {table_name};")
            return int(cur.fetchone()[0])


def main() -> None:
    print("=" * 80)
    print("AURUM TIMESCALEDB PERSISTENCE VALIDATION")
    print("=" * 80)

    try:
        bus = RedisEventBus()
        pass_check("Redis connection")
    except Exception as exc:
        fail_check(f"Redis connection failed: {exc}")
        sys.exit(1)

    try:
        writer = TimescaleWriter(event_bus=bus)
        writer.initialize_schema()
        pass_check("Timescale/Postgres connection and schema")
    except Exception as exc:
        fail_check(f"Timescale/Postgres connection failed: {exc}")
        print("Make sure TimescaleDB is running on localhost:5432.")
        sys.exit(1)

    try:
        tick_rows = bus.read_latest(EVENT_STREAMS["market_ticks"], count=20)
        feature_rows = bus.read_latest(EVENT_STREAMS["market_features"], count=20)
        alert_rows = bus.read_latest(EVENT_STREAMS["alerts"], count=20)

        inserted_ticks = writer.insert_market_ticks(tick_rows)
        inserted_features = writer.insert_market_features(feature_rows)
        inserted_alerts = writer.insert_alerts(alert_rows)

        pass_check(f"Inserted market_ticks rows: {inserted_ticks}")
        pass_check(f"Inserted market_features rows: {inserted_features}")
        pass_check(f"Inserted realtime_alerts rows: {inserted_alerts}")

    except Exception as exc:
        fail_check(f"Persistence insert failed: {exc}")
        sys.exit(1)

    try:
        tick_count = query_count(writer, "market_ticks")
        feature_count = query_count(writer, "market_features")
        alert_count = query_count(writer, "realtime_alerts")

        print("-" * 80)
        print("TABLE COUNTS")
        print("-" * 80)
        print(f"market_ticks: {tick_count}")
        print(f"market_features: {feature_count}")
        print(f"realtime_alerts: {alert_count}")

        if tick_count <= 0:
            fail_check("market_ticks table is empty")
            sys.exit(1)

        if feature_count <= 0:
            fail_check("market_features table is empty")
            sys.exit(1)

        pass_check("Timescale tables contain persisted events")

    except Exception as exc:
        fail_check(f"Could not query table counts: {exc}")
        sys.exit(1)

    print("=" * 80)
    print("TIMESCALEDB PERSISTENCE: PASS")
    print("=" * 80)


if __name__ == "__main__":
    main()