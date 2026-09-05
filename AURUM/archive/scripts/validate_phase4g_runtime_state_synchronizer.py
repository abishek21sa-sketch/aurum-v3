from __future__ import annotations

import importlib
from pathlib import Path


MODULE = "src.institutional.runtime_state_synchronizer"

OUTPUTS = [
    Path("results/institutional/latest_institutional_runtime_state.json"),
    Path("results/institutional/latest_institutional_runtime_state.txt"),
]


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 4G RUNTIME STATE SYNCHRONIZER VALIDATION")
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
            result = module.run_runtime_state_synchronizer()
            print(f"[PASS] synchronizer executed")
            print(result["summary"])
        except Exception as exc:
            ok = False
            print(f"[FAIL] synchronizer failed | {exc}")

    for path in OUTPUTS:
        if path.exists():
            print(f"[PASS] {path}")
        else:
            ok = False
            print(f"[FAIL] {path}")

    print("\nFINAL STATUS")
    print("-" * 80)

    if ok:
        print("[PASS] PHASE 4G RUNTIME STATE SYNCHRONIZER READY")
    else:
        print("[FAIL] PHASE 4G RUNTIME STATE SYNCHRONIZER INCOMPLETE")


if __name__ == "__main__":
    main()