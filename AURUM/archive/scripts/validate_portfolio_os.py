from __future__ import annotations

import importlib
from pathlib import Path


MODULES = [
    "src.portfolio_os.portfolio_state_machine",
    "src.portfolio_os.portfolio_director",
    "src.portfolio_os.daily_portfolio_cycle",
    "src.portfolio_os.portfolio_operating_system",
]


ARTIFACTS = [
    Path("results/portfolio_os/portfolio_state_machine.json"),
    Path("results/portfolio_os/portfolio_directive.json"),
    Path("results/portfolio_os/daily_portfolio_cycle.json"),
    Path("results/portfolio_os/portfolio_operating_system.json"),
]


def main() -> None:
    print("=" * 80)
    print("AURUM PORTFOLIO OS VALIDATION")
    print("=" * 80)

    passed = True

    print("MODULE CHECKS")
    print("-" * 80)
    for module in MODULES:
        try:
            importlib.import_module(module)
            print(f"[PASS] import {module}")
        except Exception as exc:
            passed = False
            print(f"[FAIL] import {module}")
            print(f"       {exc}")

    print()
    print("ARTIFACT CHECKS")
    print("-" * 80)
    for artifact in ARTIFACTS:
        if artifact.exists():
            print(f"[PASS] {artifact}")
        else:
            passed = False
            print(f"[FAIL] missing {artifact}")

    print()
    print("=" * 80)
    print("[PASS] PORTFOLIO OS VALIDATION COMPLETE" if passed else "[FAIL] PORTFOLIO OS VALIDATION FAILED")
    print("=" * 80)


if __name__ == "__main__":
    main()