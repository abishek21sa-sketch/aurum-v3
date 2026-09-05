from __future__ import annotations

import importlib
from pathlib import Path


MODULE = "src.institutional.institutional_readiness_report"

OUTPUTS = [
    Path("results/institutional/institutional_readiness_report.json"),
    Path("results/institutional/institutional_readiness_report.txt"),
]


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 4G INSTITUTIONAL READINESS VALIDATION")
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

    print("\nREPORT GENERATION CHECK")
    print("-" * 80)

    if module:
        try:
            report = module.generate_institutional_readiness_report()
            print(f"[PASS] report generated | status={report['overall_status']}")
            print(f"[INFO] platform_score={report['platform_score']}")
            print(f"[INFO] research_ready={report['research_ready']}")
            print(f"[INFO] production_ready={report['production_ready']}")
        except Exception as exc:
            ok = False
            print(f"[FAIL] report generation failed | {exc}")

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
        print("[PASS] PHASE 4G INSTITUTIONAL READINESS REPORT READY")
    else:
        print("[FAIL] PHASE 4G INSTITUTIONAL READINESS REPORT INCOMPLETE")


if __name__ == "__main__":
    main()