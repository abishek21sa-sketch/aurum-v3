from __future__ import annotations

import importlib
from pathlib import Path


MODULE = "src.dashboards.strategy_research_dashboard"

EXPECTED_OUTPUTS = [
    Path("results/research/strategy_registry.json"),
    Path("results/research/strategy_stress_results.csv"),
    Path("results/research/robustness_scores.csv"),
    Path("results/research/strategy_research_report.json"),
    Path("results/research/strategy_research_report.txt"),
]


def pass_msg(message: str) -> None:
    print(f"[PASS] {message}")


def fail_msg(message: str) -> None:
    print(f"[FAIL] {message}")


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 4E STRATEGY RESEARCH DASHBOARD VALIDATION")
    print("=" * 80)

    ok = True

    print("\nMODULE IMPORT CHECK")
    print("-" * 80)

    try:
        dashboard = importlib.import_module(MODULE)
        pass_msg(MODULE)
    except Exception as exc:
        ok = False
        fail_msg(f"{MODULE} | {exc}")
        dashboard = None

    print("\nDATA LOADING CHECK")
    print("-" * 80)

    if dashboard is not None:
        try:
            dashboard.ensure_research_outputs()
            pass_msg("research outputs generated or found")
        except Exception as exc:
            ok = False
            fail_msg(f"research output check failed | {exc}")

    print("\nOUTPUT EXISTENCE CHECKS")
    print("-" * 80)

    for path in EXPECTED_OUTPUTS:
        if path.exists() and path.stat().st_size > 0:
            pass_msg(str(path))
        else:
            ok = False
            fail_msg(str(path))

    print("\nFINAL STATUS")
    print("-" * 80)

    if ok:
        print("[PASS] PHASE 4E STRATEGY RESEARCH DASHBOARD READY")
    else:
        print("[FAIL] PHASE 4E STRATEGY RESEARCH DASHBOARD INCOMPLETE")


if __name__ == "__main__":
    main()