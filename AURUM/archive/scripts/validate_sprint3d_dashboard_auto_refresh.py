from __future__ import annotations

import importlib
import json
from pathlib import Path


REQUIRED_MODULES = [
    "src.dashboard.live_refresh_dashboard_adapter",
    "src.orchestration.scheduled_refresh_runner",
]

REQUIRED_ARTIFACTS = [
    Path("results/sprint3/live_market_refresh_result.json"),
    Path("results/sprint3/scheduled_refresh_summary.json"),
    Path("results/sprint3/live_refresh_dashboard_state.json"),
]


def main() -> None:
    print("=" * 80)
    print("AURUM SPRINT 3D DASHBOARD AUTO-REFRESH VALIDATION")
    print("=" * 80)

    passed = True

    print("MODULE CHECKS")
    print("-" * 80)

    for module in REQUIRED_MODULES:
        try:
            importlib.import_module(module)
            print(f"[PASS] import {module}")
        except Exception as exc:
            passed = False
            print(f"[FAIL] import {module}")
            print(f"       {exc}")

    print()
    print("DASHBOARD STATE CHECK")
    print("-" * 80)

    try:
        from src.dashboard.live_refresh_dashboard_adapter import LiveRefreshDashboardAdapter

        state = LiveRefreshDashboardAdapter().load_state()

        assert state.live_refresh_available is True
        assert state.scheduled_refresh_available is True
        assert state.provider == "yfinance"
        assert state.probability_type == "filtered"
        assert state.status == "completed"
        assert state.portfolio_action in {
            "normal",
            "watch",
            "reduce_risk",
            "block_execution_reduce_risk",
        }

        print("[PASS] dashboard state loaded")
        print(f"[INFO] provider: {state.provider}")
        print(f"[INFO] regime: {state.regime}")
        print(f"[INFO] anomaly severity: {state.anomaly_severity}")
        print(f"[INFO] stress score: {state.stress_score:.4f}")
        print(f"[INFO] portfolio action: {state.portfolio_action}")

    except Exception as exc:
        passed = False
        print("[FAIL] dashboard state")
        print(f"       {exc}")

    print()
    print("ARTIFACT CHECKS")
    print("-" * 80)

    for artifact in REQUIRED_ARTIFACTS:
        if artifact.exists():
            print(f"[PASS] {artifact}")
        else:
            passed = False
            print(f"[FAIL] missing {artifact}")

    print()
    print("SCHEMA CHECK")
    print("-" * 80)

    try:
        data = json.loads(
            Path("results/sprint3/live_refresh_dashboard_state.json").read_text()
        )

        required = [
            "live_refresh_available",
            "scheduled_refresh_available",
            "provider",
            "timestamp",
            "regime",
            "probability_type",
            "anomaly_severity",
            "anomaly_score",
            "stress_score",
            "digital_twin_state",
            "portfolio_action",
            "cycles_completed",
            "status",
        ]

        for key in required:
            assert key in data

        assert data["provider"] == "yfinance"
        assert data["probability_type"] == "filtered"

        print("[PASS] dashboard state schema")

    except Exception as exc:
        passed = False
        print("[FAIL] dashboard state schema")
        print(f"       {exc}")

    print()
    print("=" * 80)

    if passed:
        print("[PASS] SPRINT 3D DASHBOARD AUTO-REFRESH COMPLETE")
        print("Official dashboard can now read latest live refresh state.")
    else:
        print("[FAIL] SPRINT 3D DASHBOARD AUTO-REFRESH FAILED")

    print("=" * 80)

    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()