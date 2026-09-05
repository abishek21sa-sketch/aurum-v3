# src/execution/portfolio_lifecycle_manager.py

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

import pandas as pd


EXECUTION_DIR = Path("results/execution")

LIFECYCLE_REPORT_PATH = EXECUTION_DIR / "lifecycle_report.json"
LIFECYCLE_SUMMARY_PATH = EXECUTION_DIR / "lifecycle_summary.csv"

MODULE_SEQUENCE = [
    "src.execution.portfolio_state_engine",
    "src.execution.trade_generation_engine",
    "src.execution.turnover_control_engine",
    "src.execution.transaction_cost_engine",
    "src.execution.cost_aware_rebalancer",
    "src.execution.rebalance_scheduler",
    "src.execution.execution_priority_engine",
    "src.execution.cash_management_engine",
    "src.execution.paper_trading_engine",
]


REQUIRED_OUTPUTS = {
    "portfolio_state": EXECUTION_DIR / "current_portfolio_state.json",
    "target_portfolio": EXECUTION_DIR / "target_portfolio.json",
    "trade_recommendations": EXECUTION_DIR / "trade_recommendations.csv",
    "filtered_trades": EXECUTION_DIR / "filtered_trades.csv",
    "transaction_cost_report": EXECUTION_DIR / "transaction_cost_report.csv",
    "rebalance_decision": EXECUTION_DIR / "rebalance_decision.csv",
    "rebalance_schedule": EXECUTION_DIR / "rebalance_schedule.json",
    "execution_priority": EXECUTION_DIR / "execution_priority.csv",
    "cash_management_report": EXECUTION_DIR / "cash_management_report.json",
    "paper_trading_log": EXECUTION_DIR / "paper_trading_log.csv",
    "paper_trading_summary": EXECUTION_DIR / "paper_trading_summary.json",
    "post_trade_portfolio_state": EXECUTION_DIR / "post_trade_portfolio_state.json",
}


def ensure_execution_dir() -> None:
    EXECUTION_DIR.mkdir(parents=True, exist_ok=True)


def run_module(module_name: str) -> Dict[str, Any]:
    started_at = datetime.now()

    result = subprocess.run(
        [sys.executable, "-m", module_name],
        capture_output=True,
        text=True,
    )

    ended_at = datetime.now()

    return {
        "module": module_name,
        "status": "PASS" if result.returncode == 0 else "FAIL",
        "return_code": result.returncode,
        "started_at": started_at.isoformat(timespec="seconds"),
        "ended_at": ended_at.isoformat(timespec="seconds"),
        "stdout_tail": result.stdout[-1200:],
        "stderr_tail": result.stderr[-1200:],
    }


def validate_required_outputs() -> Dict[str, Any]:
    output_status = {}

    for name, path in REQUIRED_OUTPUTS.items():
        output_status[name] = {
            "path": str(path),
            "exists": path.exists(),
        }

    all_outputs_exist = all(item["exists"] for item in output_status.values())

    return {
        "all_outputs_exist": all_outputs_exist,
        "outputs": output_status,
    }


def load_json_if_exists(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_lifecycle_report(module_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    validation = validate_required_outputs()

    paper_summary = load_json_if_exists(EXECUTION_DIR / "paper_trading_summary.json")
    cash_report = load_json_if_exists(EXECUTION_DIR / "cash_management_report.json")
    schedule = load_json_if_exists(EXECUTION_DIR / "rebalance_schedule.json")
    priority_summary = load_json_if_exists(EXECUTION_DIR / "execution_priority_summary.json")
    cost_summary = load_json_if_exists(EXECUTION_DIR / "transaction_cost_summary.json")

    all_modules_passed = all(result["status"] == "PASS" for result in module_results)

    lifecycle_status = (
        "SUCCESS"
        if all_modules_passed and validation["all_outputs_exist"]
        else "FAILED"
    )

    report = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "lifecycle_status": lifecycle_status,
        "all_modules_passed": all_modules_passed,
        "required_outputs_valid": validation["all_outputs_exist"],
        "module_results": module_results,
        "output_validation": validation,
        "execution_summary": {
            "rebalance_recommendation": schedule.get("decision", {}).get(
                "recommendation"
            ),
            "should_rebalance": schedule.get("decision", {}).get(
                "should_rebalance"
            ),
            "priority_trades": priority_summary.get("number_of_priority_trades"),
            "cash_status": cash_report.get("liquidity_status"),
            "cash_buffer_passed": cash_report.get("cash_buffer_passed"),
            "total_trade_notional": paper_summary.get("total_trade_notional"),
            "total_transaction_cost": paper_summary.get("total_transaction_cost"),
            "post_trade_cash_weight": paper_summary.get("post_trade_cash_weight"),
            "paper_trading_status": paper_summary.get("paper_trading_status"),
            "estimated_cost_bps_of_portfolio": cost_summary.get(
                "total_estimated_cost_bps_of_portfolio"
            ),
        },
    }

    return report


def save_lifecycle_report(report: Dict[str, Any]) -> None:
    ensure_execution_dir()

    with LIFECYCLE_REPORT_PATH.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)


def save_lifecycle_summary(report: Dict[str, Any]) -> None:
    summary = report["execution_summary"]

    row = {
        "timestamp": report["timestamp"],
        "lifecycle_status": report["lifecycle_status"],
        "all_modules_passed": report["all_modules_passed"],
        "required_outputs_valid": report["required_outputs_valid"],
        **summary,
    }

    pd.DataFrame([row]).to_csv(LIFECYCLE_SUMMARY_PATH, index=False)


def print_lifecycle_report(report: Dict[str, Any]) -> None:
    print("=" * 80)
    print("AURUM PORTFOLIO LIFECYCLE MANAGER")
    print("=" * 80)

    print("\nMODULE STATUS")
    print("-" * 80)
    for result in report["module_results"]:
        print(f"[{result['status']}] {result['module']}")

    print("\nOUTPUT VALIDATION")
    print("-" * 80)
    for name, item in report["output_validation"]["outputs"].items():
        status = "PASS" if item["exists"] else "FAIL"
        print(f"[{status}] {name}: {item['path']}")

    summary = report["execution_summary"]

    print("\nLIFECYCLE EXECUTION SUMMARY")
    print("-" * 80)
    print(f"Lifecycle Status: {report['lifecycle_status']}")
    print(f"Rebalance Recommendation: {summary['rebalance_recommendation']}")
    print(f"Should Rebalance: {summary['should_rebalance']}")
    print(f"Priority Trades: {summary['priority_trades']}")
    print(f"Cash Status: {summary['cash_status']}")
    print(f"Cash Buffer Passed: {summary['cash_buffer_passed']}")
    print(f"Total Trade Notional: ${summary['total_trade_notional']:,.2f}")
    print(f"Total Transaction Cost: ${summary['total_transaction_cost']:,.2f}")
    print(f"Estimated Cost: {summary['estimated_cost_bps_of_portfolio']:.2f} bps")
    print(f"Post-Trade Cash Weight: {summary['post_trade_cash_weight']:.2%}")
    print(f"Paper Trading Status: {summary['paper_trading_status']}")

    print("\nOUTPUTS")
    print("-" * 80)
    print(f"Lifecycle Report: {LIFECYCLE_REPORT_PATH}")
    print(f"Lifecycle Summary: {LIFECYCLE_SUMMARY_PATH}")

    print("\nAURUM PORTFOLIO LIFECYCLE MANAGER COMPLETE")


def main() -> None:
    ensure_execution_dir()

    module_results = []

    for module_name in MODULE_SEQUENCE:
        result = run_module(module_name)
        module_results.append(result)

        if result["status"] == "FAIL":
            break

    report = build_lifecycle_report(module_results)

    save_lifecycle_report(report)
    save_lifecycle_summary(report)

    print_lifecycle_report(report)


if __name__ == "__main__":
    main()