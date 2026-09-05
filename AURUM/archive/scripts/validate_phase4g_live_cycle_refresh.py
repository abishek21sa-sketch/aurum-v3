from __future__ import annotations

import importlib
from pathlib import Path


MODULE = "src.institutional.live_cycle_refresh_runner"

OUTPUTS = [
    Path("results/institutional/live_cycle_refresh_report.json"),
    Path("results/institutional/live_cycle_refresh_report.txt"),
    Path("results/institutional/runtime_integrity_audit.json"),
    Path("results/institutional/runtime_coherence_gate.json"),
]


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 4G LIVE CYCLE REFRESH VALIDATION")
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

    print("\nLIVE CYCLE EXECUTION CHECK")
    print("-" * 80)

    if module:
        try:
            report = module.run_live_cycle_refresh()
            print(f"[PASS] live cycle refresh executed | status={report['overall_status']}")
            print(
                "[INFO] post-refresh gate="
                f"{report['post_refresh_integrity']['gate_status']}"
            )
        except Exception as exc:
            ok = False
            print(f"[FAIL] live cycle refresh failed | {exc}")

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
        print("[PASS] PHASE 4G LIVE CYCLE REFRESH RUNNER READY")
    else:
        print("[FAIL] PHASE 4G LIVE CYCLE REFRESH RUNNER INCOMPLETE")


if __name__ == "__main__":
    main()