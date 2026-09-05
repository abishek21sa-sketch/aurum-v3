from pathlib import Path
import importlib
import subprocess
import sys


REQUIRED_MODULES = [
    "src.universe.asset_universe",
    "src.intelligence.cross_asset_engine",
    "src.factors.factor_engine",
    "src.alpha.alpha_factory",
    "src.research_scientist.research_scientist_agent",
    "src.autonomous_research.autonomous_research_loop",
    "src.portfolio_lab_2.portfolio_lab_engine",
    "src.cio.chief_investment_officer_agent",
    "src.alpha_ranking.alpha_scorecard",
    "src.alpha_ranking.strategy_ranker",
    "src.research_firm.ai_research_firm_mode",
]

REQUIRED_ARTIFACTS = [
    "results/universe/institutional_asset_universe.json",
    "results/intelligence/cross_asset_dependency_report.json",
    "results/factors/factor_definitions.json",
    "results/alpha/alpha_registry.json",
    "results/research_scientist/research_hypotheses.json",
    "results/autonomous_research/autonomous_research_loop.json",
    "results/portfolio_lab_2/portfolio_lab_results.json",
    "results/cio/cio_market_thesis.json",
    "results/alpha_ranking/institutional_research_rankings.json",
    "results/research_firm/ai_research_firm_mode.json",
]

VALIDATORS = [
    "scripts.validate_phase6b1_multi_asset_universe",
    "scripts.validate_phase6b2_cross_asset_intelligence",
    "scripts.validate_phase6b3_factor_platform",
    "scripts.validate_phase6b4_alpha_factory",
    "scripts.validate_phase6b5_research_scientist",
    "scripts.validate_phase6b6_autonomous_research_loop",
    "scripts.validate_phase6b7_portfolio_lab_2",
    "scripts.validate_phase6b8_ai_cio",
    "scripts.validate_phase6b9_alpha_ranking",
    "scripts.validate_phase6b10_ai_research_firm_mode",
]


def check(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        print(f"[PASS] {label}")
        if detail:
            print(f"       {detail}")
    else:
        print(f"[FAIL] {label}")
        if detail:
            print(f"       {detail}")
        raise SystemExit(1)


def run_validator(module_name: str) -> None:
    result = subprocess.run(
        [sys.executable, "-m", module_name],
        capture_output=True,
        text=True,
    )

    detail = ""
    if result.stdout:
        lines = [line for line in result.stdout.splitlines() if line.strip()]
        detail = lines[-2] if len(lines) >= 2 else lines[-1]
    elif result.stderr:
        detail = result.stderr.splitlines()[-1]

    check(result.returncode == 0, f"{module_name} passed", detail)


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 6B COMPLETE VALIDATION")
    print("=" * 80)

    print("\nMODULE CHECKS")
    print("-" * 80)
    for module in REQUIRED_MODULES:
        importlib.import_module(module)
        check(True, f"import {module}")

    print("\nARTIFACT CHECKS")
    print("-" * 80)
    for artifact in REQUIRED_ARTIFACTS:
        check(Path(artifact).exists(), f"{artifact} exists")

    print("\nVALIDATOR CHECKS")
    print("-" * 80)
    for validator in VALIDATORS:
        run_validator(validator)

    print("=" * 80)
    print("[PASS] PHASE 6B INSTITUTIONAL INTELLIGENCE COMPLETE")
    print("AURUM now operates as an AI Research Firm.")
    print("=" * 80)


if __name__ == "__main__":
    main()