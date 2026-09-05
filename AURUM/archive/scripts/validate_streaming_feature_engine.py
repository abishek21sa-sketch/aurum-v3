# scripts/validate_streaming_feature_engine.py

from __future__ import annotations

import sys
import time

from src.realtime.event_bus import RedisEventBus, EVENT_STREAMS
from src.realtime.streaming_feature_engine import StreamingFeatureEngine


def pass_check(message: str) -> None:
    print(f"[PASS] {message}")


def fail_check(message: str) -> None:
    print(f"[FAIL] {message}")


def main() -> None:
    print("=" * 80)
    print("AURUM STREAMING FEATURE ENGINE VALIDATION")
    print("=" * 80)

    try:
        bus = RedisEventBus()
        pass_check("Redis connection")
    except Exception as exc:
        fail_check(f"Redis connection failed: {exc}")
        sys.exit(1)

    try:
        tick_count = bus.stream_length(EVENT_STREAMS["market_ticks"])
        print(f"market_ticks length: {tick_count}")

        if tick_count <= 0:
            fail_check("market_ticks is empty. Run market gateway first.")
            sys.exit(1)

        pass_check("market_ticks stream exists")
    except Exception as exc:
        fail_check(f"Could not inspect market_ticks: {exc}")
        sys.exit(1)

    try:
        latest_ticks = bus.read_latest(EVENT_STREAMS["market_ticks"], count=50)
        engine = StreamingFeatureEngine(event_bus=bus)

        generated = 0

        for tick in reversed(latest_ticks):
            feature = engine.process_tick(tick)
            if feature:
                generated += 1

        if generated <= 0:
            fail_check("No features generated")
            sys.exit(1)

        pass_check(f"Feature computation generated {generated} feature events")

    except Exception as exc:
        fail_check(f"Feature computation failed: {exc}")
        sys.exit(1)

    try:
        feature_count = bus.stream_length(EVENT_STREAMS["market_features"])
        latest_features = bus.read_latest(EVENT_STREAMS["market_features"], count=5)

        print(f"market_features length: {feature_count}")

        if feature_count <= 0 or not latest_features:
            fail_check("market_features stream is empty")
            sys.exit(1)

        pass_check("market_features stream exists")

        print("-" * 80)
        print("LATEST MARKET FEATURE")
        print("-" * 80)

        newest = latest_features[0]
        for key, value in newest.items():
            print(f"{key}: {value}")

    except Exception as exc:
        fail_check(f"Could not inspect market_features: {exc}")
        sys.exit(1)

    print("=" * 80)
    print("STREAMING FEATURE ENGINE: PASS")
    print("=" * 80)


if __name__ == "__main__":
    main()