from __future__ import annotations

import importlib
from pathlib import Path


MODULE = "src.dashboards.portfolio_lab_dashboard"

OUTPUTS = [
    Path("results/portfolio_lab/portfolio_lab_report.json"),
    Path("results/portfolio_lab/portfolio_lab_comparison.csv"),
    Path("results/portfolio_lab/portfolio_lab_report.txt"),
]


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 4I PORTFOLIO LAB DASHBOARD VALIDATION")
    print("=" * 80)

    ok = True

    print("\nMODULE IMPORT CHECK")
    print("-" * 80)

    try:
        module = importlib.import_module(MODULE)
        print(f"[PASS] {MODULE}")
    except Exception as exc:
        module = None
        ok = False
        print(f"[FAIL] {MODULE} | {exc}")

    print("\nDATA AVAILABILITY CHECK")
    print("-" * 80)

    if module:
        try:
            module.ensure_lab_outputs()
            print("[PASS] portfolio lab outputs generated or found")
        except Exception as exc:
            ok = False
            print(f"[FAIL] portfolio lab output check failed | {exc}")

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
        print("[PASS] PHASE 4I PORTFOLIO LAB DASHBOARD READY")
    else:
        print("[FAIL] PHASE 4I PORTFOLIO LAB DASHBOARD INCOMPLETE")


if __name__ == "__main__":
    main()