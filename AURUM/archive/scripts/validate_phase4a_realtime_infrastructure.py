# scripts/validate_phase4a_realtime_infrastructure.py

from __future__ import annotations

import sys
from typing import Any, Dict

from src.realtime.event_bus import RedisEventBus, EVENT_STREAMS


def pass_check(message: str) -> None:
    print(f"[PASS] {message}")


def fail_check(message: str) -> None:
    print(f"[FAIL] {message}")


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 4A REAL-TIME INFRASTRUCTURE VALIDATION")
    print("=" * 80)

    try:
        bus = RedisEventBus()
        health = bus.health()
        pass_check(f"Redis connection: {health}")
    except Exception as exc:
        fail_check(f"Redis connection failed: {exc}")
        sys.exit(1)

    test_event = {
        "event_type": "validation_tick",
        "source": "phase4a_validator",
        "ticker": "SPY",
        "price": 500.0,
        "volume": 1000,
        "timestamp": RedisEventBus.utc_now(),
    }

    try:
        event_id = bus.publish(EVENT_STREAMS["market_ticks"], test_event)
        pass_check(f"Published validation event to market_ticks: {event_id}")
    except Exception as exc:
        fail_check(f"Could not publish validation event: {exc}")
        sys.exit(1)

    try:
        latest = bus.read_latest(EVENT_STREAMS["market_ticks"], count=5)
        if not latest:
            fail_check("market_ticks stream exists but returned no events")
            sys.exit(1)

        pass_check(f"Read latest market_ticks events: count={len(latest)}")

        newest = latest[0]
        print("-" * 80)
        print("LATEST MARKET TICK")
        print("-" * 80)
        for key, value in newest.items():
            print(f"{key}: {value}")

    except Exception as exc:
        fail_check(f"Could not read latest market_ticks events: {exc}")
        sys.exit(1)

    print("-" * 80)
    print("STREAM LENGTHS")
    print("-" * 80)

    for name in EVENT_STREAMS.values():
        try:
            length = bus.stream_length(name)
            print(f"{name}: {length}")
        except Exception:
            print(f"{name}: not created yet")

    print("=" * 80)
    print("PHASE 4A BASE REAL-TIME INFRASTRUCTURE: PASS")
    print("=" * 80)


if __name__ == "__main__":
    main()