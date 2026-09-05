from pathlib import Path
import importlib
import json

from src.portfolio_lab_2.portfolio_lab_engine import PortfolioLabEngine
from src.portfolio_lab_2.scenario_library import ScenarioLibrary


REQUIRED_SCENARIOS = {
    "SCENARIO_INFLATION_SPIKE",
    "SCENARIO_RATES_UP_100BPS",
    "SCENARIO_NVDA_DOWN_30",
    "SCENARIO_LIQUIDITY_DISAPPEARS",
    "SCENARIO_CRYPTO_CRASH",
}


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


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 6B.7 PORTFOLIO LABORATORY 2.0 VALIDATION")
    print("=" * 80)

    importlib.import_module("src.portfolio_lab_2.scenario_library")
    importlib.import_module("src.portfolio_lab_2.portfolio_lab_engine")
    importlib.import_module("src.portfolio_lab_2.portfolio_lab_report_generator")
    check(True, "portfolio lab 2 modules import")

    library = ScenarioLibrary().save()
    results = PortfolioLabEngine().run()

    scenario_path = Path("results/portfolio_lab_2/scenario_library.json")
    results_path = Path("results/portfolio_lab_2/portfolio_lab_results.json")

    check(scenario_path.exists(), "scenario_library.json exists")
    check(results_path.exists(), "portfolio_lab_results.json exists")

    check(library["scenario_count"] >= 5, "at least 5 scenarios defined", str(library["scenario_count"]))
    check(results["scenario_count"] == library["scenario_count"], "all scenarios evaluated")

    scenario_ids = {scenario["scenario_id"] for scenario in library["scenarios"]}

    for scenario_id in REQUIRED_SCENARIOS:
        check(scenario_id in scenario_ids, f"{scenario_id} exists")

    check(results["worst_scenario"] is not None, "worst scenario identified")
    check("portfolio_impact" in results["worst_scenario"], "worst scenario has impact")
    check("recommended_response" in results["worst_scenario"], "worst scenario has response")

    valid_severities = {"low", "medium", "high", "critical"}

    for scenario in results["scenario_results"]:
        check(scenario["severity"] in valid_severities, f"{scenario['scenario_id']} has valid severity")
        check(isinstance(scenario["asset_impacts"], dict), f"{scenario['scenario_id']} has asset impacts")
        check(scenario["institutional_logic"], f"{scenario['scenario_id']} has institutional logic")
        check(scenario["recommended_response"], f"{scenario['scenario_id']} has recommended response")

    print("=" * 80)
    print("[PASS] PHASE 6B.7 PORTFOLIO LABORATORY 2.0 COMPLETE")
    print("AURUM now simulates institutional what-if portfolio scenarios.")
    print("=" * 80)


if __name__ == "__main__":
    main()