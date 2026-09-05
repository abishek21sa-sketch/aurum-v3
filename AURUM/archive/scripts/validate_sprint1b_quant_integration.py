from __future__ import annotations

import importlib
import json
from pathlib import Path


REQUIRED_MODULES = [
    "src.optimization.quant_core_router",
    "src.regimes.hmm_live_state_adapter",
    "src.intelligence.institutional_anomaly_signal_generator",
    "src.digital_twin.anomaly_aware_digital_twin_adapter",
    "src.cio.quant_core_cio_briefing_adapter",
]

REQUIRED_ARTIFACTS = [
    Path("results/sprint1b/quant_core_router_result.json"),
    Path("results/sprint1b/hmm_live_state_adapter_result.json"),
    Path("results/sprint1b/institutional_anomaly_signal.json"),
    Path("results/sprint1b/anomaly_aware_digital_twin_state.json"),
    Path("results/sprint1b/quant_core_cio_briefing.json"),
]


def check_imports() -> bool:
    print("MODULE IMPORT CHECKS")
    print("-" * 80)

    passed = True

    for module in REQUIRED_MODULES:
        try:
            importlib.import_module(module)
            print(f"[PASS] import {module}")
        except Exception as exc:
            passed = False
            print(f"[FAIL] import {module}")
            print(f"       {exc}")

    return passed


def run_integration() -> bool:
    print()
    print("SPRINT 1B INTEGRATION CHECKS")
    print("-" * 80)

    passed = True

    try:
        from src.optimization.cvar_lp_optimizer import load_sample_returns
        from src.optimization.quant_core_router import QuantCoreRouter

        returns = load_sample_returns()
        cvar = QuantCoreRouter().run_cvar_lp(returns)

        assert cvar.optimizer_engine == "CVaRLPOptimizer"
        assert "Rockafellar-Uryasev" in cvar.cvar_method
        assert cvar.integration_status == "connected"

        print("[PASS] LP optimizer connected")
    except Exception as exc:
        passed = False
        print("[FAIL] LP optimizer connected")
        print(f"       {exc}")

    try:
        from src.regimes.hmm_regime_engine_clean import load_sample_features
        from src.regimes.hmm_live_state_adapter import HMMLiveStateAdapter

        features = load_sample_features()
        hmm = HMMLiveStateAdapter().run(features)

        assert hmm.probability_type == "filtered"
        assert hmm.live_safe is True
        assert abs(sum(hmm.probabilities.values()) - 1.0) < 1e-5

        print("[PASS] filtered probabilities used")
    except Exception as exc:
        passed = False
        print("[FAIL] filtered probabilities used")
        print(f"       {exc}")

    try:
        from src.intelligence.institutional_anomaly_detector import load_sample_returns
        from src.intelligence.institutional_anomaly_signal_generator import (
            InstitutionalAnomalySignalGenerator,
        )

        anomaly_returns = load_sample_returns()
        anomaly_signal = InstitutionalAnomalySignalGenerator().generate(
            anomaly_returns,
            publish_to_redis=True,
        )

        assert anomaly_signal.event_type == "institutional_anomaly"
        assert anomaly_signal.redis_stream == "market_signals"
        assert anomaly_signal.severity in {
            "normal",
            "watch",
            "alert",
            "critical",
        }

        print("[PASS] anomaly stream active")
    except Exception as exc:
        passed = False
        print("[FAIL] anomaly stream active")
        print(f"       {exc}")

    try:
        from src.digital_twin.anomaly_aware_digital_twin_adapter import (
            AnomalyAwareDigitalTwinAdapter,
        )

        digital_twin = AnomalyAwareDigitalTwinAdapter(anomaly_weight=0.20).update_state(
            base_stress_score=0.40,
            anomaly_signal=anomaly_signal,
        )

        assert digital_twin.integration_status == "digital_twin_receives_anomaly_signal"
        assert digital_twin.adjusted_stress_score >= digital_twin.base_stress_score

        print("[PASS] digital twin receives anomaly signal")
    except Exception as exc:
        passed = False
        print("[FAIL] digital twin receives anomaly signal")
        print(f"       {exc}")

    try:
        from src.cio.quant_core_cio_briefing_adapter import QuantCoreCIOBriefingAdapter

        cio = QuantCoreCIOBriefingAdapter().generate(
            cvar_engine=cvar.optimizer_engine,
            cvar_method=cvar.cvar_method,
            hmm_probability_type=hmm.probability_type,
            anomaly_signal=anomaly_signal,
            digital_twin_state=digital_twin,
        )

        assert cio.cvar_engine == "CVaRLPOptimizer"
        assert cio.hmm_probability_type == "filtered"
        assert cio.anomaly_score == anomaly_signal.score

        print("[PASS] CIO receives anomaly briefing")
    except Exception as exc:
        passed = False
        print("[FAIL] CIO receives anomaly briefing")
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
        data = json.loads(Path("results/sprint1b/quant_core_router_result.json").read_text())
        assert data["optimizer_engine"] == "CVaRLPOptimizer"
        assert data["integration_status"] == "connected"
        print("[PASS] quant core router schema")
    except Exception as exc:
        passed = False
        print("[FAIL] quant core router schema")
        print(f"       {exc}")

    try:
        data = json.loads(Path("results/sprint1b/hmm_live_state_adapter_result.json").read_text())
        assert data["probability_type"] == "filtered"
        assert data["live_safe"] is True
        print("[PASS] HMM live adapter schema")
    except Exception as exc:
        passed = False
        print("[FAIL] HMM live adapter schema")
        print(f"       {exc}")

    try:
        data = json.loads(Path("results/sprint1b/institutional_anomaly_signal.json").read_text())
        assert data["event_type"] == "institutional_anomaly"
        assert data["redis_stream"] == "market_signals"
        print("[PASS] anomaly signal schema")
    except Exception as exc:
        passed = False
        print("[FAIL] anomaly signal schema")
        print(f"       {exc}")

    try:
        data = json.loads(Path("results/sprint1b/anomaly_aware_digital_twin_state.json").read_text())
        assert data["integration_status"] == "digital_twin_receives_anomaly_signal"
        print("[PASS] digital twin anomaly schema")
    except Exception as exc:
        passed = False
        print("[FAIL] digital twin anomaly schema")
        print(f"       {exc}")

    try:
        data = json.loads(Path("results/sprint1b/quant_core_cio_briefing.json").read_text())
        assert data["cvar_engine"] == "CVaRLPOptimizer"
        assert data["hmm_probability_type"] == "filtered"
        print("[PASS] CIO briefing schema")
    except Exception as exc:
        passed = False
        print("[FAIL] CIO briefing schema")
        print(f"       {exc}")

    return passed


def main() -> None:
    print("=" * 80)
    print("AURUM SPRINT 1B QUANT INTEGRATION VALIDATION")
    print("=" * 80)

    imports_ok = check_imports()
    integration_ok = run_integration()
    artifacts_ok = check_artifacts()
    schema_ok = check_schema()

    print()
    print("=" * 80)

    if imports_ok and integration_ok and artifacts_ok and schema_ok:
        print("[PASS] SPRINT 1B QUANT INTEGRATION COMPLETE")
        print("Hardened quant engines are now routed into AURUM decision infrastructure.")
    else:
        print("[FAIL] SPRINT 1B VALIDATION FAILED")
        print("Fix failed checks above before moving forward.")

    print("=" * 80)


if __name__ == "__main__":
    main()