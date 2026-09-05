# scripts/validate_phase4a_full_realtime_stack.py

from __future__ import annotations

import os
import sys
import time
from typing import Dict

from src.realtime.event_bus import RedisEventBus, EVENT_STREAMS
from src.storage.timescale_writer import TimescaleWriter


DATABASE_URL = os.getenv(
    "TIMESCALE_DATABASE_URL",
    "postgresql://aurum:aurum@127.0.0.1:5434/aurum",
)


def pass_check(message: str) -> None:
    print(f"[PASS] {message}")


def fail_check(message: str) -> None:
    print(f"[FAIL] {message}")


def warn_check(message: str) -> None:
    print(f"[WARN] {message}")


def get_table_count(writer: TimescaleWriter, table_name: str) -> int:
    with writer.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {table_name};")
            return int(cur.fetchone()[0])


def get_latest_stream_ids(bus: RedisEventBus) -> Dict[str, str]:
    ids = {}
    active_streams = {
        "market_ticks": EVENT_STREAMS["market_ticks"],
        "market_features": EVENT_STREAMS["market_features"],
        "alerts": EVENT_STREAMS["alerts"],
    }

    for name, stream in EVENT_STREAMS.items():
        rows = bus.read_latest(stream, count=1)

        if rows and "redis_id" in rows[0]:
            ids[name] = rows[0]["redis_id"]
        else:
            ids[name] = ""

    return ids

def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 4A FULL REAL-TIME STACK VALIDATION")
    print("=" * 80)

    try:
        bus = RedisEventBus()
        pass_check("Redis connection")
    except Exception as exc:
        fail_check(f"Redis connection failed: {exc}")
        sys.exit(1)

    try:
        writer = TimescaleWriter(event_bus=bus, database_url=DATABASE_URL)
        writer.initialize_schema()
        pass_check("TimescaleDB connection and schema")
    except Exception as exc:
        fail_check(f"TimescaleDB connection failed: {exc}")
        sys.exit(1)

    print("-" * 80)
    print("CHECKING REDIS STREAM ACTIVITY")
    print("-" * 80)

    before = get_latest_stream_ids(bus)
    time.sleep(5)
    after = get_latest_stream_ids(bus)

    for stream_name in before:
        print(
            f"{stream_name}: "
            f"before={before[stream_name]} "
            f"after={after[stream_name]}"
        )

    if after["market_ticks"] == before["market_ticks"]:
        fail_check("market_ticks latest ID did not change.")
        sys.exit(1)

    pass_check("market_ticks active")

    if after["market_features"] == before["market_features"]:
        fail_check("market_features latest ID did not change.")
        sys.exit(1)

    pass_check("market_features active")

    if after["alerts"] == before["alerts"]:
        warn_check(
            "alerts latest ID did not change during sample window."
        )
    else:
        pass_check("alerts active")

    print("-" * 80)
    print("CHECKING TIMESCALE TABLE COUNTS")
    print("-" * 80)

    try:
        tick_count = get_table_count(writer, "market_ticks")
        feature_count = get_table_count(writer, "market_features")
        alert_count = get_table_count(writer, "realtime_alerts")

        print(f"market_ticks: {tick_count}")
        print(f"market_features: {feature_count}")
        print(f"realtime_alerts: {alert_count}")

        if tick_count <= 0:
            fail_check("Timescale market_ticks table is empty.")
            sys.exit(1)

        if feature_count <= 0:
            fail_check("Timescale market_features table is empty.")
            sys.exit(1)

        pass_check("TimescaleDB contains persisted live events")

        if alert_count <= 0:
            warn_check("Timescale realtime_alerts is empty. This can be normal if writer started before alerts.")
        else:
            pass_check("TimescaleDB contains persisted alerts")

    except Exception as exc:
        fail_check(f"Timescale table validation failed: {exc}")
        sys.exit(1)

    print("-" * 80)
    print("LATEST REDIS EVENTS")
    print("-" * 80)

    latest_tick = bus.read_latest(EVENT_STREAMS["market_ticks"], count=1)
    latest_feature = bus.read_latest(EVENT_STREAMS["market_features"], count=1)
    latest_alert = bus.read_latest(EVENT_STREAMS["alerts"], count=1)

    if latest_tick:
        print("Latest tick:", latest_tick[0])

    if latest_feature:
        print("Latest feature:", latest_feature[0])

    if latest_alert:
        print("Latest alert:", latest_alert[0])
    else:
        print("Latest alert: none")

    print("=" * 80)
    print("PHASE 4A FULL REAL-TIME STACK: PASS")
    print("=" * 80)


if __name__ == "__main__":
    main()