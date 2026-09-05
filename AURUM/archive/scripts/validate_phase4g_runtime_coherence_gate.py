from __future__ import annotations

import importlib
from pathlib import Path


MODULE = "src.institutional.runtime_coherence_gate"

OUTPUTS = [
    Path("results/institutional/runtime_coherence_gate.json"),
    Path("results/institutional/runtime_coherence_gate.txt"),
]


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 4G RUNTIME COHERENCE GATE VALIDATION")
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

    print("\nGATE EXECUTION CHECK")
    print("-" * 80)

    if module:
        try:
            report = module.run_runtime_coherence_gate()
            print(f"[PASS] gate executed | status={report['gate_status']}")
            print(f"[INFO] allow_new_portfolio_decision={report['allow_new_portfolio_decision']}")
            print(f"[INFO] allow_execution_release={report['allow_execution_release']}")
        except Exception as exc:
            ok = False
            print(f"[FAIL] gate execution failed | {exc}")

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
        print("[PASS] PHASE 4G RUNTIME COHERENCE GATE READY")
    else:
        print("[FAIL] PHASE 4G RUNTIME COHERENCE GATE INCOMPLETE")


if __name__ == "__main__":
    main()