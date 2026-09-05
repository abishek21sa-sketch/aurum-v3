from __future__ import annotations

import importlib
import json
from pathlib import Path


REQUIRED_MODULES = [
    "src.market.providers.provider_factory",
    "src.orchestration.live_market_refresh_orchestrator",
    "src.regimes.hmm_live_state_adapter",
    "src.intelligence.institutional_anomaly_signal_generator",
    "src.digital_twin.anomaly_aware_digital_twin_adapter",
]

REQUIRED_ARTIFACTS = [
    Path("results/sprint3/provider_abstraction_validation.json"),
    Path("results/sprint3/live_market_refresh_result.json"),
]


def main() -> None:
    print("=" * 80)
    print("AURUM SPRINT 3B LIVE REFRESH ORCHESTRATOR VALIDATION")
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
    print("LIVE REFRESH EXECUTION CHECK")
    print("-" * 80)

    try:
        from src.orchestration.live_market_refresh_orchestrator import (
            LiveMarketRefreshOrchestrator,
        )

        orchestrator = LiveMarketRefreshOrchestrator(
            provider_name="yfinance",
            tickers=["SPY", "QQQ", "DIA", "TLT", "GLD"],
            period="6mo",
            interval="1d",
        )

        result = orchestrator.run_once(publish_to_redis=False)

        assert result.provider == "yfinance"
        assert result.refresh_status == "completed"
        assert result.regime_probability_type == "filtered"
        assert result.feature_rows >= 80
        assert result.portfolio_os_action in {
            "normal",
            "watch",
            "reduce_risk",
            "block_execution_reduce_risk",
        }

        print("[PASS] live refresh completed")
        print(f"[INFO] provider: {result.provider}")
        print(f"[INFO] feature rows: {result.feature_rows}")
        print(f"[INFO] regime: state_{result.current_regime}")
        print(f"[INFO] anomaly severity: {result.anomaly_severity}")
        print(f"[INFO] stress score: {result.adjusted_stress_score:.4f}")
        print(f"[INFO] portfolio action: {result.portfolio_os_action}")

    except Exception as exc:
        passed = False
        print("[FAIL] live refresh execution")
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
            Path("results/sprint3/live_market_refresh_result.json").read_text()
        )

        required = [
            "event_type",
            "timestamp",
            "provider",
            "tickers",
            "rows_by_ticker",
            "feature_rows",
            "regime_probability_type",
            "current_regime",
            "anomaly_severity",
            "anomaly_score",
            "adjusted_stress_score",
            "digital_twin_state",
            "portfolio_os_action",
            "refresh_status",
        ]

        for key in required:
            assert key in data

        assert data["event_type"] == "live_market_refresh"
        assert data["provider"] == "yfinance"
        assert data["regime_probability_type"] == "filtered"
        assert data["refresh_status"] == "completed"

        print("[PASS] live refresh schema")

    except Exception as exc:
        passed = False
        print("[FAIL] live refresh schema")
        print(f"       {exc}")

    print()
    print("=" * 80)

    if passed:
        print("[PASS] SPRINT 3B LIVE REFRESH ORCHESTRATOR COMPLETE")
        print("AURUM now has a live market refresh cycle from provider data to Portfolio OS action.")
    else:
        print("[FAIL] SPRINT 3B LIVE REFRESH ORCHESTRATOR FAILED")

    print("=" * 80)

    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()