from __future__ import annotations

import importlib
import json
from pathlib import Path


MODULES = [
    "src.institutional.runtime_integrity_auditor",
    "src.institutional.runtime_coherence_gate",
    "src.institutional.runtime_state_synchronizer",
    "src.institutional.institutional_decision_cycle_orchestrator",
    "src.institutional.institutional_readiness_report",
    "src.research.strategy_registry",
    "src.research.strategy_stress_tester",
    "src.research.robustness_score_engine",
    "src.research.strategy_research_report",
    "src.dashboards.strategy_research_dashboard",
]

REQUIRED_OUTPUTS = [
    Path("results/institutional/runtime_integrity_audit.json"),
    Path("results/institutional/runtime_coherence_gate.json"),
    Path("results/institutional/latest_institutional_runtime_state.json"),
    Path("results/institutional/institutional_decision_cycle_report.json"),
    Path("results/institutional/institutional_readiness_report.json"),
    Path("results/research/strategy_registry.json"),
    Path("results/research/strategy_stress_results.csv"),
    Path("results/research/robustness_scores.csv"),
    Path("results/research/strategy_research_report.json"),
    Path("results/phase4/phase4_full_institutional_lab_validation.json"),
    Path("results/phase4/phase4_master_status_report.json"),
    Path("results/phase4/PHASE4_ARCHITECTURE_SUMMARY.md"),
]


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def main() -> None:
    print("=" * 80)
    print("AURUM FINAL PHASE 4 COMPLETION VALIDATION")
    print("=" * 80)

    ok = True

    print("\nMODULE IMPORT CHECKS")
    print("-" * 80)

    for module in MODULES:
        try:
            importlib.import_module(module)
            print(f"[PASS] {module}")
        except Exception as exc:
            ok = False
            print(f"[FAIL] {module} | {exc}")

    print("\nOUTPUT CHECKS")
    print("-" * 80)

    for path in REQUIRED_OUTPUTS:
        if path.exists() and path.stat().st_size > 0:
            print(f"[PASS] {path}")
        else:
            ok = False
            print(f"[FAIL] {path}")

    print("\nREADINESS CHECK")
    print("-" * 80)

    readiness = load_json(
        Path("results/institutional/institutional_readiness_report.json")
    )

    status = readiness.get("overall_status", "UNKNOWN")
    research_ready = readiness.get("research_ready", False)
    production_ready = readiness.get("production_ready", False)

    print(f"Overall Readiness: {status}")
    print(f"Research Ready: {research_ready}")
    print(f"Production Ready: {production_ready}")

    if not research_ready:
        ok = False
        print("[FAIL] Phase 4 is not research-ready.")
    else:
        print("[PASS] Phase 4 is research-ready.")

    print("\nFINAL STATUS")
    print("-" * 80)

    if ok and research_ready:
        print("[PASS] PHASE 4 COMPLETE AS RESEARCH-GRADE INSTITUTIONAL MARKET LAB")
    else:
        print("[FAIL] PHASE 4 FINAL COMPLETION VALIDATION FAILED")


if __name__ == "__main__":
    main()