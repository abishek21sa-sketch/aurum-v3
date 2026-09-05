# src/execution/paper_trading_engine.py

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

import pandas as pd

from src.execution.portfolio_state_engine import (
    load_portfolio_state,
    update_portfolio_state,
)


EXECUTION_DIR = Path("results/execution")

EXECUTION_PRIORITY_PATH = EXECUTION_DIR / "execution_priority.csv"
CASH_MANAGEMENT_REPORT_PATH = EXECUTION_DIR / "cash_management_report.json"

PAPER_TRADING_LOG_PATH = EXECUTION_DIR / "paper_trading_log.csv"
PAPER_TRADING_SUMMARY_PATH = EXECUTION_DIR / "paper_trading_summary.json"
UPDATED_PORTFOLIO_PATH = EXECUTION_DIR / "post_trade_portfolio_state.json"


DEFAULT_ASSET_PRICES = {
    "SPY": 500.00,
    "QQQ": 430.00,
    "TLT": 90.00,
    "GLD": 220.00,
    "BTC-USD": 65000.00,
    "ETH-USD": 3500.00,
    "VIX": 18.00,
    "CASH": 1.00,
}


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
                "trade_notional",
                "estimated_cost_dollars",
                "execution_rank",
                "execution_bucket",
            ]
        )

    return priority


def load_cash_report() -> Dict[str, Any]:
    if not CASH_MANAGEMENT_REPORT_PATH.exists():
        raise FileNotFoundError(
            f"Missing cash management report: {CASH_MANAGEMENT_REPORT_PATH}. "
            "Run python -m src.execution.cash_management_engine first."
        )

    with CASH_MANAGEMENT_REPORT_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def simulate_fills(priority: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "timestamp",
        "execution_rank",
        "asset",
        "action",
        "execution_bucket",
        "fill_status",
        "fill_price",
        "shares",
        "trade_notional",
        "estimated_cost_dollars",
        "cash_effect",
    ]

    if priority.empty:
        return pd.DataFrame(columns=columns)

    rows = []
    timestamp = datetime.now().isoformat(timespec="seconds")

    for _, row in priority.iterrows():
        asset = row["asset"]
        action = row["execution_action"]
        trade_notional = float(row["trade_notional"])
        estimated_cost = float(row["estimated_cost_dollars"])
        price = DEFAULT_ASSET_PRICES.get(asset, 100.00)

        if action == "BUY":
            shares = trade_notional / price
            cash_effect = -(trade_notional + estimated_cost)
            fill_status = "FILLED"
        elif action == "SELL":
            shares = -trade_notional / price
            cash_effect = trade_notional - estimated_cost
            fill_status = "FILLED"
        else:
            shares = 0.0
            cash_effect = 0.0
            fill_status = "SKIPPED"

        rows.append(
            {
                "timestamp": timestamp,
                "execution_rank": row["execution_rank"],
                "asset": asset,
                "action": action,
                "execution_bucket": row["execution_bucket"],
                "fill_status": fill_status,
                "fill_price": price,
                "shares": shares,
                "trade_notional": trade_notional,
                "estimated_cost_dollars": estimated_cost,
                "cash_effect": cash_effect,
            }
        )

    return pd.DataFrame(rows, columns=columns)


def calculate_post_trade_positions(
    current_positions: Dict[str, float],
    fills: pd.DataFrame,
    portfolio_value: float,
) -> Dict[str, float]:
    updated = current_positions.copy()

    for _, row in fills.iterrows():
        asset = row["asset"]
        action = row["action"]
        trade_weight = float(row["trade_notional"]) / portfolio_value

        if action == "BUY":
            updated[asset] = updated.get(asset, 0.0) + trade_weight
        elif action == "SELL":
            updated[asset] = updated.get(asset, 0.0) - trade_weight

    total_cost = fills["estimated_cost_dollars"].sum()
    cost_weight = total_cost / portfolio_value

    updated["CASH"] = updated.get("CASH", 0.0) - cost_weight

    # Normalize tiny numerical drift only.
    total_weight = sum(updated.values())
    if abs(total_weight - 1.0) > 0.001:
        updated["CASH"] += 1.0 - total_weight

    updated = {asset: round(float(weight), 10) for asset, weight in updated.items()}

    return updated


def save_post_trade_state(
    portfolio_value: float,
    updated_positions: Dict[str, float],
) -> Dict[str, Any]:
    state = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "portfolio_value": portfolio_value,
        "positions": updated_positions,
        "source": "paper_trading_engine",
    }

    with UPDATED_PORTFOLIO_PATH.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=4)

    # Also updates official current state and history.
    update_portfolio_state(
        positions=updated_positions,
        portfolio_value=portfolio_value,
    )

    return state


def calculate_paper_trading_summary(
    fills: pd.DataFrame,
    updated_positions: Dict[str, float],
) -> Dict[str, Any]:
    filled = fills[fills["fill_status"] == "FILLED"]

    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "number_of_orders": int(len(fills)),
        "number_of_filled_orders": int(len(filled)),
        "number_of_skipped_orders": int((fills["fill_status"] == "SKIPPED").sum()),
        "total_trade_notional": float(fills["trade_notional"].sum()),
        "total_transaction_cost": float(fills["estimated_cost_dollars"].sum()),
        "net_cash_effect": float(fills["cash_effect"].sum()),
        "post_trade_cash_weight": float(updated_positions.get("CASH", 0.0)),
        "post_trade_total_weight": float(sum(updated_positions.values())),
        "paper_trading_status": "SUCCESS",
    }


def save_paper_trading_log(fills: pd.DataFrame) -> None:
    ensure_execution_dir()
    fills.to_csv(PAPER_TRADING_LOG_PATH, index=False)


def save_paper_trading_summary(summary: Dict[str, Any]) -> None:
    ensure_execution_dir()

    with PAPER_TRADING_SUMMARY_PATH.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=4)


def print_paper_trading_report(
    fills: pd.DataFrame,
    updated_positions: Dict[str, float],
    summary: Dict[str, Any],
) -> None:
    print("=" * 80)
    print("AURUM PAPER TRADING ENGINE")
    print("=" * 80)

    print("\nPAPER TRADE FILLS")
    print("-" * 80)

    display = fills.copy()
    display["fill_price"] = display["fill_price"].map(lambda x: f"${x:,.2f}")
    display["shares"] = display["shares"].map(lambda x: f"{x:,.4f}")
    display["trade_notional"] = display["trade_notional"].map(lambda x: f"${x:,.2f}")
    display["estimated_cost_dollars"] = display["estimated_cost_dollars"].map(
        lambda x: f"${x:,.2f}"
    )
    display["cash_effect"] = display["cash_effect"].map(lambda x: f"${x:,.2f}")

    print(display.to_string(index=False))

    print("\nUPDATED PORTFOLIO POSITIONS")
    print("-" * 80)
    for asset, weight in updated_positions.items():
        print(f"{asset:<10} {weight:>8.2%}")

    print("\nPAPER TRADING SUMMARY")
    print("-" * 80)
    print(f"Orders: {summary['number_of_orders']}")
    print(f"Filled Orders: {summary['number_of_filled_orders']}")
    print(f"Skipped Orders: {summary['number_of_skipped_orders']}")
    print(f"Total Trade Notional: ${summary['total_trade_notional']:,.2f}")
    print(f"Total Transaction Cost: ${summary['total_transaction_cost']:,.2f}")
    print(f"Net Cash Effect: ${summary['net_cash_effect']:,.2f}")
    print(f"Post-Trade Cash Weight: {summary['post_trade_cash_weight']:.2%}")
    print(f"Post-Trade Total Weight: {summary['post_trade_total_weight']:.2%}")
    print(f"Paper Trading Status: {summary['paper_trading_status']}")

    print("\nOUTPUTS")
    print("-" * 80)
    print(f"Paper Trading Log: {PAPER_TRADING_LOG_PATH}")
    print(f"Paper Trading Summary: {PAPER_TRADING_SUMMARY_PATH}")
    print(f"Post-Trade Portfolio State: {UPDATED_PORTFOLIO_PATH}")

    print("\nAURUM PAPER TRADING ENGINE COMPLETE")


def main() -> None:
    ensure_execution_dir()

    state = load_portfolio_state()
    portfolio_value = float(state["portfolio_value"])
    current_positions = state["positions"]

    priority = load_execution_priority()
    cash_report = load_cash_report()

    if not cash_report.get("cash_buffer_passed", False):
        raise RuntimeError(
            "Cash buffer check failed. Paper trading halted by cash management gate."
        )

    fills = simulate_fills(priority)

    updated_positions = calculate_post_trade_positions(
        current_positions=current_positions,
        fills=fills,
        portfolio_value=portfolio_value,
    )

    save_post_trade_state(
        portfolio_value=portfolio_value,
        updated_positions=updated_positions,
    )

    summary = calculate_paper_trading_summary(
        fills=fills,
        updated_positions=updated_positions,
    )

    save_paper_trading_log(fills)
    save_paper_trading_summary(summary)

    print_paper_trading_report(
        fills=fills,
        updated_positions=updated_positions,
        summary=summary,
    )


if __name__ == "__main__":
    main()