from __future__ import annotations

import importlib
import json
from pathlib import Path


REQUIRED_MODULES = [
    "src.orchestration.live_market_refresh_orchestrator",
    "src.orchestration.scheduled_refresh_runner",
]

REQUIRED_ARTIFACTS = [
    Path("results/sprint3/live_market_refresh_result.json"),
    Path("results/sprint3/scheduled_refresh_summary.json"),
    Path("results/sprint3/scheduled_refresh_history.jsonl"),
]


def main() -> None:
    print("=" * 80)
    print("AURUM SPRINT 3C SCHEDULED REFRESH RUNNER VALIDATION")
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
    print("SCHEDULED RUNNER EXECUTION CHECK")
    print("-" * 80)

    try:
        from src.orchestration.scheduled_refresh_runner import ScheduledRefreshRunner

        runner = ScheduledRefreshRunner(
            provider_name="yfinance",
            tickers=["SPY", "QQQ", "DIA", "TLT", "GLD"],
            period="6mo",
            interval="1d",
            interval_seconds=1,
        )

        summary = runner.run(
            max_cycles=2,
            publish_to_redis=False,
            sleep_between_cycles=False,
        )

        assert summary.event_type == "scheduled_live_market_refresh"
        assert summary.provider == "yfinance"
        assert summary.cycles_requested == 2
        assert summary.cycles_completed == 2
        assert summary.latest_refresh_status == "completed"
        assert summary.latest_portfolio_action in {
            "normal",
            "watch",
            "reduce_risk",
            "block_execution_reduce_risk",
        }

        print("[PASS] scheduled runner completed two cycles")
        print(f"[INFO] latest action: {summary.latest_portfolio_action}")
        print(f"[INFO] latest stress: {summary.latest_stress_score:.4f}")
        print(f"[INFO] history path: {summary.history_path}")

    except Exception as exc:
        passed = False
        print("[FAIL] scheduled runner execution")
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
    print("HISTORY CHECK")
    print("-" * 80)

    try:
        history = Path("results/sprint3/scheduled_refresh_history.jsonl")
        lines = [line for line in history.read_text(encoding="utf-8").splitlines() if line.strip()]

        assert len(lines) >= 2

        latest = json.loads(lines[-1])
        assert latest["event_type"] == "live_market_refresh"
        assert latest["refresh_status"] == "completed"
        assert latest["regime_probability_type"] == "filtered"

        print("[PASS] scheduled refresh history valid")
        print(f"[INFO] history events: {len(lines)}")

    except Exception as exc:
        passed = False
        print("[FAIL] scheduled refresh history")
        print(f"       {exc}")

    print()
    print("SUMMARY SCHEMA CHECK")
    print("-" * 80)

    try:
        summary = json.loads(
            Path("results/sprint3/scheduled_refresh_summary.json").read_text()
        )

        required = [
            "event_type",
            "timestamp",
            "provider",
            "tickers",
            "interval_seconds",
            "cycles_requested",
            "cycles_completed",
            "latest_refresh_status",
            "latest_portfolio_action",
            "latest_stress_score",
            "latest_digital_twin_state",
            "history_path",
            "status",
        ]

        for key in required:
            assert key in summary

        assert summary["event_type"] == "scheduled_live_market_refresh"
        assert summary["provider"] == "yfinance"
        assert summary["status"] == "completed"

        print("[PASS] scheduled refresh summary schema")

    except Exception as exc:
        passed = False
        print("[FAIL] scheduled refresh summary schema")
        print(f"       {exc}")

    print()
    print("=" * 80)

    if passed:
        print("[PASS] SPRINT 3C SCHEDULED REFRESH RUNNER COMPLETE")
        print("AURUM can now run live market refresh cycles repeatedly and persist refresh history.")
    else:
        print("[FAIL] SPRINT 3C SCHEDULED REFRESH RUNNER FAILED")

    print("=" * 80)

    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()