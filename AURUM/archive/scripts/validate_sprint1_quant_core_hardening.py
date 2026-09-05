"""
AURUM Sprint 1 Quant Core Hardening Validation
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path


REQUIRED_MODULES = [
    "src.optimization.cvar_lp_optimizer",
    "src.regimes.hmm_regime_engine_clean",
    "src.intelligence.institutional_anomaly_detector",
]

REQUIRED_ARTIFACTS = [
    Path("results/optimization/cvar_lp_optimizer_result.json"),
    Path("results/regime/hmm_regime_engine_clean_result.json"),
    Path("results/intelligence/institutional_anomaly_summary.json"),
    Path("results/intelligence/institutional_anomaly_timeseries.csv"),
]


def check_imports() -> bool:
    print("MODULE IMPORT CHECKS")
    print("-" * 80)

    passed = True

    for module_name in REQUIRED_MODULES:
        try:
            importlib.import_module(module_name)
            print(f"[PASS] import {module_name}")
        except Exception as exc:
            passed = False
            print(f"[FAIL] import {module_name}")
            print(f"       {exc}")

    return passed


def run_modules() -> bool:
    print()
    print("MODULE EXECUTION CHECKS")
    print("-" * 80)

    passed = True

    try:
        from src.optimization.cvar_lp_optimizer import CVaRLPOptimizer, load_sample_returns

        returns = load_sample_returns()
        result = CVaRLPOptimizer(returns, beta=0.95, long_only=True, max_weight=0.35).optimize()

        assert result.status in {"optimal", "optimal_inaccurate"}
        assert abs(sum(result.weights.values()) - 1.0) < 1e-5
        assert result.method.startswith("Rockafellar-Uryasev")

        print("[PASS] CVaR LP optimizer")
    except Exception as exc:
        passed = False
        print("[FAIL] CVaR LP optimizer")
        print(f"       {exc}")

    try:
        from src.regimes.hmm_regime_engine_clean import CleanHMMRegimeEngine, load_sample_features

        features = load_sample_features()
        result = CleanHMMRegimeEngine(n_states=3).fit(features)

        assert result.live_probability_type == "filtered"
        assert "Smoothed probabilities use full-sample hindsight" in result.warning
        assert abs(sum(result.current_filtered_probabilities.values()) - 1.0) < 1e-5

        print("[PASS] HMM filtered vs smoothed cleanup")
    except Exception as exc:
        passed = False
        print("[FAIL] HMM filtered vs smoothed cleanup")
        print(f"       {exc}")

    try:
        from src.intelligence.institutional_anomaly_detector import (
            InstitutionalAnomalyDetector,
            load_sample_returns,
        )

        returns = load_sample_returns()
        detector = InstitutionalAnomalyDetector()
        detected = detector.detect(returns)
        summary = detector.summarize(detected)

        assert "rolling_z_score" in detected.columns
        assert "isolation_score" in detected.columns
        assert "combined_score" in detected.columns
        assert summary.method == "rolling_z_score + isolation_forest"
        assert summary.anomaly_count > 0

        print("[PASS] institutional anomaly detector")
    except Exception as exc:
        passed = False
        print("[FAIL] institutional anomaly detector")
        print(f"       {exc}")

    return passed


def check_artifacts() -> bool:
    print()
    print("ARTIFACT CHECKS")
    print("-" * 80)

    passed = True

    for path in REQUIRED_ARTIFACTS:
        if path.exists():
            print(f"[PASS] artifact exists: {path}")
        else:
            passed = False
            print(f"[FAIL] artifact missing: {path}")

    return passed


def check_schema() -> bool:
    print()
    print("SCHEMA CHECKS")
    print("-" * 80)

    passed = True

    try:
        path = Path("results/optimization/cvar_lp_optimizer_result.json")
        data = json.loads(path.read_text())

        required = [
            "status",
            "beta",
            "alpha_var",
            "cvar_objective",
            "expected_return",
            "volatility",
            "sharpe",
            "weights",
            "method",
        ]

        for key in required:
            assert key in data

        assert data["method"] == "Rockafellar-Uryasev CVaR LP via cvxpy"

        print("[PASS] CVaR LP schema")
    except Exception as exc:
        passed = False
        print("[FAIL] CVaR LP schema")
        print(f"       {exc}")

    try:
        path = Path("results/regime/hmm_regime_engine_clean_result.json")
        data = json.loads(path.read_text())

        required = [
            "current_regime",
            "current_filtered_probabilities",
            "current_smoothed_probabilities",
            "transition_matrix",
            "expected_durations",
            "regime_counts",
            "live_probability_type",
            "warning",
        ]

        for key in required:
            assert key in data

        assert data["live_probability_type"] == "filtered"

        print("[PASS] HMM cleanup schema")
    except Exception as exc:
        passed = False
        print("[FAIL] HMM cleanup schema")
        print(f"       {exc}")

    try:
        path = Path("results/intelligence/institutional_anomaly_summary.json")
        data = json.loads(path.read_text())

        required = [
            "latest_timestamp",
            "latest_return",
            "latest_rolling_z_score",
            "latest_isolation_score",
            "latest_combined_score",
            "latest_is_anomaly",
            "latest_severity",
            "anomaly_count",
            "anomaly_rate",
            "method",
        ]

        for key in required:
            assert key in data

        assert data["method"] == "rolling_z_score + isolation_forest"

        print("[PASS] anomaly detector schema")
    except Exception as exc:
        passed = False
        print("[FAIL] anomaly detector schema")
        print(f"       {exc}")

    return passed


def main() -> None:
    print("=" * 80)
    print("AURUM SPRINT 1 QUANT CORE HARDENING VALIDATION")
    print("=" * 80)

    imports_ok = check_imports()
    execution_ok = run_modules()
    artifacts_ok = check_artifacts()
    schema_ok = check_schema()

    print()
    print("=" * 80)

    if imports_ok and execution_ok and artifacts_ok and schema_ok:
        print("[PASS] SPRINT 1 QUANT CORE HARDENING COMPLETE")
        print("AURUM CVaR, HMM, and anomaly detection core are now interview-defensible.")
    else:
        print("[FAIL] SPRINT 1 VALIDATION FAILED")
        print("Fix failed checks above before moving forward.")

    print("=" * 80)


if __name__ == "__main__":
    main()