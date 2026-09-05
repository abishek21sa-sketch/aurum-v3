from __future__ import annotations

import importlib
from pathlib import Path


MODULE = "src.institutional.runtime_integrity_auditor"

OUTPUTS = [
    Path("results/institutional/runtime_integrity_audit.json"),
    Path("results/institutional/runtime_integrity_audit.txt"),
]


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 4G RUNTIME INTEGRITY VALIDATION")
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

    print("\nAUDIT EXECUTION CHECK")
    print("-" * 80)

    if module:
        try:
            report = module.run_runtime_integrity_audit()
            print(f"[PASS] runtime audit executed | readiness={report['readiness_status']}")
        except Exception as exc:
            ok = False
            print(f"[FAIL] runtime audit failed | {exc}")

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
        print("[PASS] PHASE 4G RUNTIME INTEGRITY AUDITOR READY")
    else:
        print("[FAIL] PHASE 4G RUNTIME INTEGRITY AUDITOR INCOMPLETE")


if __name__ == "__main__":
    main()