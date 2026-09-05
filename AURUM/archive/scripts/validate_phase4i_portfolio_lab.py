from __future__ import annotations

import importlib
from pathlib import Path


MODULE = "src.lab.portfolio_lab_engine"

OUTPUTS = [
    Path("results/portfolio_lab/portfolio_lab_report.json"),
    Path("results/portfolio_lab/portfolio_lab_comparison.csv"),
    Path("results/portfolio_lab/portfolio_lab_report.txt"),
]


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 4I PORTFOLIO LAB VALIDATION")
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

    print("\nLAB EXECUTION CHECK")
    print("-" * 80)

    if module:
        try:
            report = module.run_portfolio_lab()
            print(f"[PASS] portfolio lab executed | status={report['status']}")
            print(f"[INFO] scenarios={report['scenario_count']}")
            print(f"[INFO] best_sharpe={report['summary']['best_sharpe_scenario']}")
        except Exception as exc:
            ok = False
            print(f"[FAIL] portfolio lab failed | {exc}")

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
        print("[PASS] PHASE 4I PORTFOLIO LAB READY")
    else:
        print("[FAIL] PHASE 4I PORTFOLIO LAB INCOMPLETE")


if __name__ == "__main__":
    main()