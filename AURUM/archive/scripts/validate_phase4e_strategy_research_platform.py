from __future__ import annotations

import importlib
from pathlib import Path


MODULES = [
    "src.research.strategy_registry",
    "src.research.strategy_stress_tester",
    "src.research.robustness_score_engine",
    "src.research.strategy_research_report",
]

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


def validate_imports() -> bool:
    ok = True
    print("\nMODULE IMPORT CHECKS")
    print("-" * 80)

    for module in MODULES:
        try:
            importlib.import_module(module)
            pass_msg(module)
        except Exception as exc:
            ok = False
            fail_msg(f"{module} | {exc}")

    return ok


def run_pipeline() -> bool:
    print("\nPIPELINE EXECUTION CHECK")
    print("-" * 80)

    try:
        from src.research.strategy_registry import build_strategy_registry
        from src.research.strategy_stress_tester import stress_test_strategies
        from src.research.robustness_score_engine import calculate_robustness_scores
        from src.research.strategy_research_report import generate_strategy_research_report

        build_strategy_registry()
        stress_test_strategies()
        calculate_robustness_scores()
        generate_strategy_research_report()

        pass_msg("Phase 4E research pipeline executed")
        return True

    except Exception as exc:
        fail_msg(f"Pipeline execution failed | {exc}")
        return False


def validate_outputs() -> bool:
    ok = True
    print("\nOUTPUT EXISTENCE CHECKS")
    print("-" * 80)

    for path in EXPECTED_OUTPUTS:
        if path.exists() and path.stat().st_size > 0:
            pass_msg(str(path))
        else:
            ok = False
            fail_msg(str(path))

    return ok


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 4E STRATEGY RESEARCH PLATFORM VALIDATION")
    print("=" * 80)

    imports_ok = validate_imports()
    pipeline_ok = run_pipeline()
    outputs_ok = validate_outputs()

    print("\nFINAL STATUS")
    print("-" * 80)

    if imports_ok and pipeline_ok and outputs_ok:
        print("[PASS] PHASE 4E STRATEGY RESEARCH PLATFORM COMPLETE")
    else:
        print("[FAIL] PHASE 4E STRATEGY RESEARCH PLATFORM INCOMPLETE")


if __name__ == "__main__":
    main()