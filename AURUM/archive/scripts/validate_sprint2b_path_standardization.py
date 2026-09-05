from __future__ import annotations

import json
from pathlib import Path


REQUIRED_ARTIFACTS = [
    Path("results/optimization/cvar_lp_optimizer_result.json"),
    Path("results/regime/hmm_regime_engine_clean_result.json"),
    Path("results/intelligence/institutional_anomaly_summary.json"),
    Path("results/intelligence/institutional_anomaly_timeseries.csv"),
    Path("results/sprint1b/quant_core_router_result.json"),
    Path("results/sprint1b/hmm_live_state_adapter_result.json"),
    Path("results/sprint1b/institutional_anomaly_signal.json"),
    Path("results/sprint1b/anomaly_aware_digital_twin_state.json"),
    Path("results/sprint1b/quant_core_cio_briefing.json"),
    Path("results/sprint_cleanup/hardcoded_path_audit.json"),
]


STANDARDIZED_MODULES = [
    Path("src/optimization/cvar_lp_optimizer.py"),
    Path("src/regimes/hmm_regime_engine_clean.py"),
    Path("src/intelligence/institutional_anomaly_detector.py"),
    Path("src/optimization/quant_core_router.py"),
    Path("src/regimes/hmm_live_state_adapter.py"),
    Path("src/intelligence/institutional_anomaly_signal_generator.py"),
    Path("src/digital_twin/anomaly_aware_digital_twin_adapter.py"),
    Path("src/cio/quant_core_cio_briefing_adapter.py"),
]


BAD_PATTERNS = [
    'Path("results',
    "Path('results",
    '"results/',
    "'results/",
    '"results\\',
    "'results\\",
]


def main() -> None:
    print("=" * 80)
    print("AURUM SPRINT 2B PATH STANDARDIZATION VALIDATION")
    print("=" * 80)

    passed = True

    print("RERUN CORE MODULES")
    print("-" * 80)

    try:
        from src.optimization.cvar_lp_optimizer import CVaRLPOptimizer, load_sample_returns

        returns = load_sample_returns()
        CVaRLPOptimizer(returns, beta=0.95, long_only=True, max_weight=0.35).optimize()

        print("[PASS] CVaR writes through storage_paths")
    except Exception as exc:
        passed = False
        print("[FAIL] CVaR storage path")
        print(f"       {exc}")

    try:
        from src.regimes.hmm_regime_engine_clean import CleanHMMRegimeEngine, load_sample_features

        features = load_sample_features()
        CleanHMMRegimeEngine(n_states=3).fit(features)

        print("[PASS] HMM writes through storage_paths")
    except Exception as exc:
        passed = False
        print("[FAIL] HMM storage path")
        print(f"       {exc}")

    try:
        from src.intelligence.institutional_anomaly_detector import (
            InstitutionalAnomalyDetector,
            load_sample_returns,
        )

        returns = load_sample_returns()
        InstitutionalAnomalyDetector().detect(returns)

        print("[PASS] anomaly detector writes through storage_paths")
    except Exception as exc:
        passed = False
        print("[FAIL] anomaly detector storage path")
        print(f"       {exc}")

    try:
        from src.optimization.cvar_lp_optimizer import load_sample_returns as load_cvar_returns
        from src.optimization.quant_core_router import QuantCoreRouter
        from src.regimes.hmm_regime_engine_clean import load_sample_features
        from src.regimes.hmm_live_state_adapter import HMMLiveStateAdapter
        from src.intelligence.institutional_anomaly_detector import load_sample_returns as load_anom_returns
        from src.intelligence.institutional_anomaly_signal_generator import InstitutionalAnomalySignalGenerator
        from src.digital_twin.anomaly_aware_digital_twin_adapter import AnomalyAwareDigitalTwinAdapter
        from src.cio.quant_core_cio_briefing_adapter import QuantCoreCIOBriefingAdapter

        cvar = QuantCoreRouter().run_cvar_lp(load_cvar_returns())
        hmm = HMMLiveStateAdapter().run(load_sample_features())
        anomaly = InstitutionalAnomalySignalGenerator().generate(
            load_anom_returns(),
            publish_to_redis=False,
        )
        twin = AnomalyAwareDigitalTwinAdapter().update_state(0.40, anomaly)

        QuantCoreCIOBriefingAdapter().generate(
            cvar_engine=cvar.optimizer_engine,
            cvar_method=cvar.cvar_method,
            hmm_probability_type=hmm.probability_type,
            anomaly_signal=anomaly,
            digital_twin_state=twin,
        )

        print("[PASS] Sprint 1B adapters write through storage_paths")
    except Exception as exc:
        passed = False
        print("[FAIL] Sprint 1B adapter storage paths")
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
    print("STANDARDIZED MODULE SOURCE CHECK")
    print("-" * 80)

    for module in STANDARDIZED_MODULES:
        text = module.read_text(encoding="utf-8", errors="ignore")

        has_bad = any(pattern in text for pattern in BAD_PATTERNS)
        has_storage_import = "storage_paths" in text or "artifact_path" in text

        if not has_bad and has_storage_import:
            print(f"[PASS] {module}")
        else:
            passed = False
            print(f"[FAIL] {module}")
            if has_bad:
                print("       hardcoded results path still present")
            if not has_storage_import:
                print("       storage_paths import missing")

    print()
    print("AUDIT SUMMARY")
    print("-" * 80)

    try:
        from scripts.audit_hardcoded_paths import audit

        result = audit()
        print(f"[INFO] total repo hardcoded path findings: {result.finding_count}")
        print("[PASS] hardcoded path audit generated")
    except Exception as exc:
        passed = False
        print("[FAIL] hardcoded path audit")
        print(f"       {exc}")

    print()
    print("=" * 80)

    if passed:
        print("[PASS] SPRINT 2B PATH STANDARDIZATION COMPLETE")
        print("New quant/integration modules now use centralized storage paths.")
    else:
        print("[FAIL] SPRINT 2B PATH STANDARDIZATION FAILED")

    print("=" * 80)

    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()