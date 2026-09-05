from __future__ import annotations

import importlib
import json
from pathlib import Path


MODULES = [
    "src.optimization.cvar_lp_optimizer",
    "src.optimization.quant_core_router",
    "src.regimes.hmm_regime_engine_clean",
    "src.regimes.hmm_live_state_adapter",
    "src.intelligence.institutional_anomaly_detector",
    "src.intelligence.institutional_anomaly_signal_generator",
]


ARTIFACTS = [
    Path("results/optimization/cvar_lp_optimizer_result.json"),
    Path("results/regime/hmm_regime_engine_clean_result.json"),
    Path("results/intelligence/institutional_anomaly_summary.json"),
    Path("results/sprint1b/quant_core_router_result.json"),
    Path("results/sprint1b/hmm_live_state_adapter_result.json"),
    Path("results/sprint1b/institutional_anomaly_signal.json"),
]


def main() -> None:
    print("=" * 80)
    print("AURUM CORE QUANT VALIDATION")
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
    print("ARTIFACT CHECKS")
    print("-" * 80)
    for artifact in ARTIFACTS:
        if artifact.exists():
            print(f"[PASS] {artifact}")
        else:
            passed = False
            print(f"[FAIL] missing {artifact}")

    print()
    print("SCHEMA CHECKS")
    print("-" * 80)

    try:
        data = json.loads(Path("results/optimization/cvar_lp_optimizer_result.json").read_text())
        assert data["method"] == "Rockafellar-Uryasev CVaR LP via cvxpy"
        print("[PASS] CVaR LP schema")
    except Exception as exc:
        passed = False
        print("[FAIL] CVaR LP schema")
        print(f"       {exc}")

    try:
        data = json.loads(Path("results/regime/hmm_regime_engine_clean_result.json").read_text())
        assert data["live_probability_type"] == "filtered"
        print("[PASS] HMM filtered probability schema")
    except Exception as exc:
        passed = False
        print("[FAIL] HMM schema")
        print(f"       {exc}")

    try:
        data = json.loads(Path("results/intelligence/institutional_anomaly_summary.json").read_text())
        assert data["method"] == "rolling_z_score + isolation_forest"
        print("[PASS] anomaly detector schema")
    except Exception as exc:
        passed = False
        print("[FAIL] anomaly detector schema")
        print(f"       {exc}")

    print()
    print("=" * 80)
    print("[PASS] CORE QUANT VALIDATION COMPLETE" if passed else "[FAIL] CORE QUANT VALIDATION FAILED")
    print("=" * 80)


if __name__ == "__main__":
    main()