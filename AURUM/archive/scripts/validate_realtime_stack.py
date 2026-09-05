from __future__ import annotations

import importlib
from pathlib import Path


MODULES = [
    "src.digital_twin.anomaly_aware_digital_twin_adapter",
    "src.intelligence.institutional_anomaly_signal_generator",
]

STREAM_NAMES = [
    "market_ticks",
    "market_features",
    "market_signals",
    "risk_events",
    "optimizer_events",
    "portfolio_decisions",
]


def main() -> None:
    print("=" * 80)
    print("AURUM REALTIME STACK VALIDATION")
    print("=" * 80)

    passed = True

    print("MODULE CHECKS")
    print("-" * 80)
    for module in MODULES:
        try:
            importlib.import_module(module)
            print(f"[PASS] import {module}")
        except Exception as exc:
            passed = False
            print(f"[FAIL] import {module}")
            print(f"       {exc}")

    print()
    print("REDIS STREAM CHECKS")
    print("-" * 80)

    try:
        import redis

        client = redis.Redis.from_url("redis://localhost:6379/0", decode_responses=True)

        for stream in STREAM_NAMES:
            length = client.xlen(stream)
            if length >= 0:
                print(f"[PASS] {stream} length={length}")
            else:
                passed = False
                print(f"[FAIL] {stream}")

    except Exception as exc:
        passed = False
        print("[FAIL] Redis unavailable")
        print(f"       {exc}")

    print()
    print("ARTIFACT CHECKS")
    print("-" * 80)

    artifacts = [
        Path("results/sprint1b/anomaly_aware_digital_twin_state.json"),
        Path("results/sprint1b/institutional_anomaly_signal.json"),
    ]

    for artifact in artifacts:
        if artifact.exists():
            print(f"[PASS] {artifact}")
        else:
            passed = False
            print(f"[FAIL] missing {artifact}")

    print()
    print("=" * 80)
    print("[PASS] REALTIME STACK VALIDATION COMPLETE" if passed else "[FAIL] REALTIME STACK VALIDATION FAILED")
    print("=" * 80)


if __name__ == "__main__":
    main()