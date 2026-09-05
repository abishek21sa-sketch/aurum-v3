from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


VALIDATORS = [
    "scripts.validate_core_quant",
    "scripts.validate_realtime_stack",
    "scripts.validate_portfolio_os",
    "scripts.validate_ai_research_firm",
    "scripts.validate_platform_complete",
    "scripts.validate_sprint3a_provider_abstraction",
    "scripts.validate_sprint3b_live_refresh_orchestrator",
    "scripts.validate_sprint3c_scheduled_refresh_runner",
    "scripts.validate_sprint3d_dashboard_auto_refresh",
    "scripts.validate_sprint4_presentation_layer",
]


REQUIRED_ARTIFACTS = [
    "results/optimization/cvar_lp_optimizer_result.json",
    "results/regime/hmm_regime_engine_clean_result.json",
    "results/intelligence/institutional_anomaly_summary.json",
    "results/sprint3/provider_abstraction_validation.json",
    "results/sprint3/live_market_refresh_result.json",
    "results/sprint3/scheduled_refresh_summary.json",
    "results/sprint3/live_refresh_dashboard_state.json",
    "reports/aurum_v1_presentation_package/README_DRAFT.md",
    "reports/aurum_v1_presentation_package/AURUM_WHITEPAPER_DRAFT.md",
    "reports/aurum_v1_presentation_package/RESUME_SUMMARY.md",
]


def run_validator(module: str) -> bool:
    print()
    print("=" * 80)
    print(f"RUNNING {module}")
    print("=" * 80)

    result = subprocess.run([sys.executable, "-m", module])
    return result.returncode == 0


def main() -> None:
    print("=" * 80)
    print("AURUM V1.0 RELEASE VALIDATION")
    print("=" * 80)

    passed = True
    validator_results = {}

    for validator in VALIDATORS:
        ok = run_validator(validator)
        validator_results[validator] = "pass" if ok else "fail"

        if ok:
            print(f"[PASS] {validator}")
        else:
            passed = False
            print(f"[FAIL] {validator}")

    print()
    print("=" * 80)
    print("RELEASE ARTIFACT CHECKS")
    print("=" * 80)

    artifact_results = {}

    for artifact in REQUIRED_ARTIFACTS:
        path = Path(artifact)

        if path.exists():
            artifact_results[artifact] = "present"
            print(f"[PASS] {artifact}")
        else:
            artifact_results[artifact] = "missing"
            passed = False
            print(f"[FAIL] {artifact}")

    release_manifest = {
        "release": "AURUM v1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "passed" if passed else "failed",
        "validators": validator_results,
        "artifacts": artifact_results,
        "official_dashboard": "src/dashboard/institutional_command_center.py",
        "platform_summary": {
            "quant_core": "CVaR LP, HMM filtered probabilities, anomaly detection",
            "architecture": "central paths, dashboard consolidation, validator consolidation",
            "live_market": "provider abstraction, refresh orchestrator, scheduled runner",
            "presentation": "README, architecture diagram, whitepaper, resume summary",
        },
    }

    output = Path("reports/aurum_v1_release_manifest.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(release_manifest, indent=4), encoding="utf-8")

    print()
    print("=" * 80)

    if passed:
        print("[PASS] AURUM V1.0 RELEASE VALIDATION PASSED")
        print("AURUM v1.0 is ready to freeze.")
    else:
        print("[FAIL] AURUM V1.0 RELEASE VALIDATION FAILED")
        print("Fix failed validators/artifacts before freezing.")

    print(f"Manifest: {output}")
    print("=" * 80)

    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()