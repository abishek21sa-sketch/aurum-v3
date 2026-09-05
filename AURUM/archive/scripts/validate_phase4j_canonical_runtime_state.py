from __future__ import annotations

import importlib
from pathlib import Path


MODULE = "src.institutional.canonical_runtime_state_engine"

OUTPUTS = [
    Path("results/institutional/canonical_runtime_state.json"),
    Path("results/institutional/canonical_runtime_state.txt"),
]


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 4J CANONICAL RUNTIME STATE VALIDATION")
    print("=" * 80)

    ok = True

    try:
        module = importlib.import_module(MODULE)
        print(f"[PASS] {MODULE}")
    except Exception as exc:
        module = None
        ok = False
        print(f"[FAIL] {MODULE} | {exc}")

    if module:
        try:
            state = module.run_canonical_runtime_state_engine()
            print(f"[PASS] canonical state generated")
            print(f"[INFO] regime={state['current_regime']}")
            print(f"[INFO] risk={state['risk_level']}")
            print(f"[INFO] governance={state['governance_status']}")
            print(f"[INFO] consistency={state['consistency_status']}")
        except Exception as exc:
            ok = False
            print(f"[FAIL] canonical state generation failed | {exc}")

    for path in OUTPUTS:
        if path.exists() and path.stat().st_size > 0:
            print(f"[PASS] {path}")
        else:
            ok = False
            print(f"[FAIL] {path}")

    print("\nFINAL STATUS")
    print("-" * 80)

    if ok:
        print("[PASS] PHASE 4J CANONICAL RUNTIME STATE READY")
    else:
        print("[FAIL] PHASE 4J CANONICAL RUNTIME STATE INCOMPLETE")


if __name__ == "__main__":
    main()