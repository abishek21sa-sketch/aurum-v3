from __future__ import annotations

import importlib
from pathlib import Path


MODULE = "src.institutional.decision_explanation_engine"

OUTPUTS = [
    Path("results/institutional/decision_explanation.json"),
    Path("results/institutional/decision_explanation.txt"),
]


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 4K DECISION EXPLANATION VALIDATION")
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
            explanation = module.generate_decision_explanation()
            print(f"[PASS] explanation generated")
            print(f"[INFO] decision={explanation['decision']}")
            print(f"[INFO] confidence={explanation['confidence']:.2f}")
        except Exception as exc:
            ok = False
            print(f"[FAIL] explanation generation failed | {exc}")

    for path in OUTPUTS:
        if path.exists() and path.stat().st_size > 0:
            print(f"[PASS] {path}")
        else:
            ok = False
            print(f"[FAIL] {path}")

    print("\nFINAL STATUS")
    print("-" * 80)

    if ok:
        print("[PASS] PHASE 4K DECISION EXPLANATION READY")
    else:
        print("[FAIL] PHASE 4K DECISION EXPLANATION INCOMPLETE")


if __name__ == "__main__":
    main()