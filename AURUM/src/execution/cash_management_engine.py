# src/execution/cash_management_engine.py

import json
from pathlib import Path
from typing import Dict, Any

import pandas as pd

from src.execution.portfolio_state_engine import load_portfolio_state


EXECUTION_DIR = Path("results/execution")

EXECUTION_PRIORITY_PATH = EXECUTION_DIR / "execution_priority.csv"
CASH_REPORT_PATH = EXECUTION_DIR / "cash_management_report.json"
CASH_FLOW_REPORT_PATH = EXECUTION_DIR / "cash_flow_report.csv"

DEFAULT_MINIMUM_CASH_BUFFER = 0.05
DEFAULT_PORTFOLIO_VALUE = 1_000_000.0


def ensure_execution_dir() -> None:
    EXECUTION_DIR.mkdir(parents=True, exist_ok=True)


def load_execution_priority() -> pd.DataFrame:
    if not EXECUTION_PRIORITY_PATH.exists():
        raise FileNotFoundError(
            f"Missing execution priority file: {EXECUTION_PRIORITY_PATH}. "
            "Run python -m src.execution.execution_priority_engine first."
        )

    try:
        priority = pd.read_csv(EXECUTION_PRIORITY_PATH)
    except pd.errors.EmptyDataError:
        return pd.DataFrame(
            columns=[
                "asset",
                "execution_action",
                "trade_weight",
                "absolute_trade_weight",
                "trade_notional",
                "estimated_cost_dollars",
                "execution_rank",
                "execution_bucket",
            ]
        )

    required_columns = {
        "asset",
        "execution_action",
        "trade_weight",
        "absolute_trade_weight",
        "trade_notional",
        "estimated_cost_dollars",
        "execution_rank",
        "execution_bucket",
    }

    missing = required_columns - set(priority.columns)
    if missing:
        return pd.DataFrame(columns=list(required_columns))

    return priority


def calculate_cash_flows(
    priority: pd.DataFrame,
    portfolio_value: float,
) -> pd.DataFrame:
    columns = [
        "execution_rank",
        "asset",
        "execution_action",
        "trade_weight",
        "trade_notional",
        "estimated_cost_dollars",
        "cash_inflow",
        "cash_outflow",
        "net_cash_effect",
        "net_cash_effect_weight",
        "execution_bucket",
    ]

    if priority.empty:
        return pd.DataFrame(columns=columns)

    rows = []

    for _, row in priority.iterrows():
        asset = row["asset"]
        action = row["execution_action"]
        trade_weight = float(row["trade_weight"])
        trade_notional = float(row["trade_notional"])
        cost = float(row["estimated_cost_dollars"])

        if action == "SELL":
            cash_inflow = trade_notional - cost
            cash_outflow = 0.0
            net_cash_effect = cash_inflow
        elif action == "BUY":
            cash_inflow = 0.0
            cash_outflow = trade_notional + cost
            net_cash_effect = -cash_outflow
        else:
            cash_inflow = 0.0
            cash_outflow = 0.0
            net_cash_effect = 0.0

        rows.append(
            {
                "execution_rank": row["execution_rank"],
                "asset": asset,
                "execution_action": action,
                "trade_weight": trade_weight,
                "trade_notional": trade_notional,
                "estimated_cost_dollars": cost,
                "cash_inflow": cash_inflow,
                "cash_outflow": cash_outflow,
                "net_cash_effect": net_cash_effect,
                "net_cash_effect_weight": net_cash_effect / portfolio_value,
                "execution_bucket": row["execution_bucket"],
            }
        )

    return pd.DataFrame(rows, columns=columns)


def evaluate_cash_position(
    current_cash_weight: float,
    cash_flows: pd.DataFrame,
    portfolio_value: float,
    minimum_cash_buffer: float,
) -> Dict[str, Any]:
    current_cash_dollars = current_cash_weight * portfolio_value

    total_cash_inflow = cash_flows["cash_inflow"].sum()
    total_cash_outflow = cash_flows["cash_outflow"].sum()
    net_cash_effect = cash_flows["net_cash_effect"].sum()

    projected_cash_dollars = current_cash_dollars + net_cash_effect
    projected_cash_weight = projected_cash_dollars / portfolio_value

    minimum_cash_required_dollars = minimum_cash_buffer * portfolio_value
    excess_cash_dollars = projected_cash_dollars - minimum_cash_required_dollars

    cash_buffer_passed = projected_cash_weight >= minimum_cash_buffer

    if cash_buffer_passed:
        liquidity_status = "PASS"
        recommendation = "Cash buffer remains sufficient after approved trades."
    else:
        liquidity_status = "FAIL"
        recommendation = "Projected cash falls below minimum buffer; reduce buy orders or increase sells."

    return {
        "portfolio_value": float(portfolio_value),
        "current_cash_weight": float(current_cash_weight),
        "current_cash_dollars": float(current_cash_dollars),
        "minimum_cash_buffer": float(minimum_cash_buffer),
        "minimum_cash_required_dollars": float(minimum_cash_required_dollars),
        "total_cash_inflow": float(total_cash_inflow),
        "total_cash_outflow": float(total_cash_outflow),
        "net_cash_effect": float(net_cash_effect),
        "projected_cash_dollars": float(projected_cash_dollars),
        "projected_cash_weight": float(projected_cash_weight),
        "excess_cash_dollars": float(excess_cash_dollars),
        "cash_buffer_passed": bool(cash_buffer_passed),
        "liquidity_status": liquidity_status,
        "recommendation": recommendation,
    }


def save_cash_flow_report(cash_flows: pd.DataFrame) -> None:
    ensure_execution_dir()
    cash_flows.to_csv(CASH_FLOW_REPORT_PATH, index=False)


def save_cash_report(report: Dict[str, Any]) -> None:
    ensure_execution_dir()

    with CASH_REPORT_PATH.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)


def print_cash_report(cash_flows: pd.DataFrame, report: Dict[str, Any]) -> None:
    print("=" * 80)
    print("AURUM CASH MANAGEMENT ENGINE")
    print("=" * 80)

    print("\nCASH FLOW REPORT")
    print("-" * 80)

    display = cash_flows.copy()

    display["trade_weight"] = display["trade_weight"].map(lambda x: f"{x:+.2%}")
    display["trade_notional"] = display["trade_notional"].map(lambda x: f"${x:,.2f}")
    display["estimated_cost_dollars"] = display["estimated_cost_dollars"].map(
        lambda x: f"${x:,.2f}"
    )
    display["cash_inflow"] = display["cash_inflow"].map(lambda x: f"${x:,.2f}")
    display["cash_outflow"] = display["cash_outflow"].map(lambda x: f"${x:,.2f}")
    display["net_cash_effect"] = display["net_cash_effect"].map(lambda x: f"${x:,.2f}")
    display["net_cash_effect_weight"] = display["net_cash_effect_weight"].map(
        lambda x: f"{x:+.4%}"
    )

    print(display.to_string(index=False))

    print("\nCASH MANAGEMENT SUMMARY")
    print("-" * 80)
    print(f"Portfolio Value: ${report['portfolio_value']:,.2f}")
    print(f"Current Cash: {report['current_cash_weight']:.2%}")
    print(f"Current Cash Dollars: ${report['current_cash_dollars']:,.2f}")
    print(f"Minimum Cash Buffer: {report['minimum_cash_buffer']:.2%}")
    print(f"Minimum Cash Required: ${report['minimum_cash_required_dollars']:,.2f}")
    print(f"Total Cash Inflow: ${report['total_cash_inflow']:,.2f}")
    print(f"Total Cash Outflow: ${report['total_cash_outflow']:,.2f}")
    print(f"Net Cash Effect: ${report['net_cash_effect']:,.2f}")
    print(f"Projected Cash: ${report['projected_cash_dollars']:,.2f}")
    print(f"Projected Cash Weight: {report['projected_cash_weight']:.2%}")
    print(f"Excess Cash: ${report['excess_cash_dollars']:,.2f}")
    print(f"Cash Buffer Passed: {report['cash_buffer_passed']}")
    print(f"Liquidity Status: {report['liquidity_status']}")
    print(f"Recommendation: {report['recommendation']}")

    print("\nOUTPUTS")
    print("-" * 80)
    print(f"Cash Flow Report: {CASH_FLOW_REPORT_PATH}")
    print(f"Cash Management Report: {CASH_REPORT_PATH}")

    print("\nAURUM CASH MANAGEMENT ENGINE COMPLETE")


def main() -> None:
    ensure_execution_dir()

    state = load_portfolio_state()
    positions = state["positions"]

    portfolio_value = float(state.get("portfolio_value", DEFAULT_PORTFOLIO_VALUE))
    current_cash_weight = float(positions.get("CASH", 0.0))

    priority = load_execution_priority()

    cash_flows = calculate_cash_flows(
        priority=priority,
        portfolio_value=portfolio_value,
    )

    report = evaluate_cash_position(
        current_cash_weight=current_cash_weight,
        cash_flows=cash_flows,
        portfolio_value=portfolio_value,
        minimum_cash_buffer=DEFAULT_MINIMUM_CASH_BUFFER,
    )

    save_cash_flow_report(cash_flows)
    save_cash_report(report)

    print_cash_report(cash_flows, report)


if __name__ == "__main__":
    main()