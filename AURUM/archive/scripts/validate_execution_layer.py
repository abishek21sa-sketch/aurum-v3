# scripts/validate_execution_layer.py

import importlib
from pathlib import Path

import pandas as pd


MODULES = [
    "src.execution.portfolio_state_engine",
    "src.execution.trade_generation_engine",
    "src.execution.turnover_control_engine",
    "src.execution.transaction_cost_engine",
    "src.execution.cost_aware_rebalancer",
    "src.execution.rebalance_scheduler",
    "src.execution.execution_priority_engine",
    "src.execution.cash_management_engine",
    "src.execution.paper_trading_engine",
    "src.execution.portfolio_lifecycle_manager",
]

OUTPUTS = [
    "results/execution/current_portfolio_state.json",
    "results/execution/portfolio_history.csv",
    "results/execution/portfolio_state_summary.json",
    "results/execution/target_portfolio.json",
    "results/execution/trade_recommendations.csv",
    "results/execution/filtered_trades.csv",
    "results/execution/transaction_cost_report.csv",
    "results/execution/transaction_cost_summary.json",
    "results/execution/rebalance_decision.csv",
    "results/execution/rebalance_decision_summary.json",
    "results/execution/rebalance_schedule.json",
    "results/execution/execution_priority.csv",
    "results/execution/execution_priority_summary.json",
    "results/execution/cash_flow_report.csv",
    "results/execution/cash_management_report.json",
    "results/execution/paper_trading_log.csv",
    "results/execution/paper_trading_summary.json",
    "results/execution/post_trade_portfolio_state.json",
    "results/execution/lifecycle_report.json",
    "results/execution/lifecycle_summary.csv",
]


def check_module_imports() -> list[tuple[str, bool, str]]:
    results = []

    for module in MODULES:
        try:
            importlib.import_module(module)
            results.append((module, True, "import ok"))
        except Exception as exc:
            results.append((module, False, str(exc)))

    return results


def check_outputs_exist() -> list[tuple[str, bool, str]]:
    results = []

    for output in OUTPUTS:
        path = Path(output)
        if path.exists():
            results.append((output, True, "exists"))
        else:
            results.append((output, False, "missing"))

    return results


def check_csv_readability() -> list[tuple[str, bool, str]]:
    csv_outputs = [path for path in OUTPUTS if path.endswith(".csv")]
    results = []

    for output in csv_outputs:
        path = Path(output)

        if not path.exists():
            results.append((output, False, "missing"))
            continue

        try:
            pd.read_csv(path)
            results.append((output, True, "readable"))
        except Exception as exc:
            results.append((output, False, str(exc)))

    return results


def print_section(title: str) -> None:
    print("\n" + title)
    print("-" * 80)


def print_results(results: list[tuple[str, bool, str]]) -> bool:
    all_passed = True

    for name, passed, message in results:
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {name}")
        if not passed:
            print(f"       {message}")
            all_passed = False

    return all_passed


def main() -> None:
    print("=" * 80)
    print("AURUM EXECUTION LAYER VALIDATION")
    print("=" * 80)

    print_section("MODULE IMPORT CHECKS")
    module_passed = print_results(check_module_imports())

    print_section("OUTPUT EXISTENCE CHECKS")
    output_passed = print_results(check_outputs_exist())

    print_section("CSV READABILITY CHECKS")
    csv_passed = print_results(check_csv_readability())

    all_passed = module_passed and output_passed and csv_passed

    print("\n" + "=" * 80)
    if all_passed:
        print("EXECUTION LAYER VALIDATION COMPLETE: PASS")
    else:
        print("EXECUTION LAYER VALIDATION COMPLETE: FAIL")
    print("=" * 80)


if __name__ == "__main__":
    main()