from __future__ import annotations

import importlib
from pathlib import Path


MODULE = "src.institutional.decision_lineage_engine"

OUTPUTS = [
    Path("results/institutional/decision_lineage.json"),
    Path("results/institutional/decision_lineage.txt"),
]


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 4L DECISION LINEAGE VALIDATION")
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
            lineage = module.generate_decision_lineage()
            print("[PASS] decision lineage generated")
            print(f"[INFO] chain_id={lineage['decision_chain_id']}")
            print(f"[INFO] status={lineage['lineage_quality']['lineage_status']}")
        except Exception as exc:
            ok = False
            print(f"[FAIL] lineage generation failed | {exc}")

    for path in OUTPUTS:
        if path.exists() and path.stat().st_size > 0:
            print(f"[PASS] {path}")
        else:
            ok = False
            print(f"[FAIL] {path}")

    print("\nFINAL STATUS")
    print("-" * 80)

    if ok:
        print("[PASS] PHASE 4L DECISION LINEAGE READY")
    else:
        print("[FAIL] PHASE 4L DECISION LINEAGE INCOMPLETE")


if __name__ == "__main__":
    main()