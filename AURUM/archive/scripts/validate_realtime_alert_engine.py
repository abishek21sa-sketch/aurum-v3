# scripts/validate_realtime_alert_engine.py

from __future__ import annotations

import sys

from src.realtime.event_bus import RedisEventBus, EVENT_STREAMS
from src.realtime.realtime_alert_engine import RealtimeAlertEngine


def pass_check(message: str) -> None:
    print(f"[PASS] {message}")


def fail_check(message: str) -> None:
    print(f"[FAIL] {message}")


def main() -> None:
    print("=" * 80)
    print("AURUM REAL-TIME ALERT ENGINE VALIDATION")
    print("=" * 80)

    try:
        bus = RedisEventBus()
        pass_check("Redis connection")
    except Exception as exc:
        fail_check(f"Redis connection failed: {exc}")
        sys.exit(1)

    try:
        feature_count = bus.stream_length(EVENT_STREAMS["market_features"])
        print(f"market_features length: {feature_count}")

        if feature_count <= 0:
            fail_check("market_features is empty. Run streaming feature engine first.")
            sys.exit(1)

        pass_check("market_features stream exists")
    except Exception as exc:
        fail_check(f"Could not inspect market_features: {exc}")
        sys.exit(1)

    try:
        latest_features = bus.read_latest(EVENT_STREAMS["market_features"], count=100)

        engine = RealtimeAlertEngine(event_bus=bus)

        generated = 0

        for feature in reversed(latest_features):
            alerts = engine.process_feature(feature)
            generated += len(alerts)

        pass_check(f"Alert evaluation completed. Generated {generated} alert events.")

    except Exception as exc:
        fail_check(f"Alert evaluation failed: {exc}")
        sys.exit(1)

    try:
        alert_count = bus.stream_length(EVENT_STREAMS["alerts"])
        latest_alerts = bus.read_latest(EVENT_STREAMS["alerts"], count=5)

        print(f"alerts length: {alert_count}")

        if alert_count <= 0:
            print("[WARN] No alerts generated yet. This can be normal if the market stream is calm.")
            print("[WARN] Engine logic is still valid if alert evaluation passed.")
        else:
            pass_check("alerts stream exists")

            print("-" * 80)
            print("LATEST ALERT")
            print("-" * 80)

            newest = latest_alerts[0]
            for key, value in newest.items():
                print(f"{key}: {value}")

    except Exception as exc:
        fail_check(f"Could not inspect alerts stream: {exc}")
        sys.exit(1)

    print("=" * 80)
    print("REAL-TIME ALERT ENGINE: PASS")
    print("=" * 80)


if __name__ == "__main__":
    main()