from __future__ import annotations

import importlib
from pathlib import Path


MODULE = "src.institutional.institutional_decision_cycle_orchestrator"

OUTPUTS = [
    Path("results/institutional/institutional_decision_cycle_report.json"),
    Path("results/institutional/institutional_decision_cycle_report.txt"),
    Path("results/institutional/runtime_integrity_audit.json"),
    Path("results/institutional/runtime_coherence_gate.json"),
]


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 4G INSTITUTIONAL DECISION CYCLE VALIDATION")
    print("=" * 80)

    ok = True

    print("\nMODULE IMPORT CHECK")
    print("-" * 80)

    try:
        module = importlib.import_module(MODULE)
        print(f"[PASS] {MODULE}")
    except Exception as exc:
        ok = False
        module = None
        print(f"[FAIL] {MODULE} | {exc}")

    print("\nCYCLE EXECUTION CHECK")
    print("-" * 80)

    if module:
        try:
            report = module.run_institutional_decision_cycle()
            print(f"[PASS] institutional cycle executed | status={report['cycle_status']}")
        except Exception as exc:
            ok = False
            print(f"[FAIL] institutional cycle failed | {exc}")

    print("\nOUTPUT CHECKS")
    print("-" * 80)

    for path in OUTPUTS:
        if path.exists() and path.stat().st_size > 0:
            print(f"[PASS] {path}")
        else:
            ok = False
            print(f"[FAIL] {path}")

    print("\nFINAL STATUS")
    print("-" * 80)

    if ok:
        print("[PASS] PHASE 4G INSTITUTIONAL DECISION CYCLE READY")
    else:
        print("[FAIL] PHASE 4G INSTITUTIONAL DECISION CYCLE INCOMPLETE")


if __name__ == "__main__":
    main()