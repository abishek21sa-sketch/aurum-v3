# src/execution/transaction_cost_engine.py

import json
from pathlib import Path
from typing import Dict, Any

import pandas as pd


EXECUTION_DIR = Path("results/execution")
FILTERED_TRADES_PATH = EXECUTION_DIR / "filtered_trades.csv"
COST_REPORT_PATH = EXECUTION_DIR / "transaction_cost_report.csv"
COST_SUMMARY_PATH = EXECUTION_DIR / "transaction_cost_summary.json"

DEFAULT_PORTFOLIO_VALUE = 1_000_000.0

DEFAULT_COST_MODEL = {
    "commission_bps": 0.50,
    "spread_bps": {
        "SPY": 1.0,
        "QQQ": 1.2,
        "TLT": 1.5,
        "GLD": 1.5,
        "BTC-USD": 8.0,
        "ETH-USD": 10.0,
        "VIX": 5.0,
        "CASH": 0.0,
        "DEFAULT": 2.0,
    },
    "slippage_bps": {
        "SPY": 1.0,
        "QQQ": 1.2,
        "TLT": 1.5,
        "GLD": 1.5,
        "BTC-USD": 10.0,
        "ETH-USD": 12.0,
        "VIX": 8.0,
        "CASH": 0.0,
        "DEFAULT": 2.0,
    },
    "market_impact_multiplier_bps": 4.0,
}


def ensure_execution_dir() -> None:
    EXECUTION_DIR.mkdir(parents=True, exist_ok=True)


def load_filtered_trades() -> pd.DataFrame:
    if not FILTERED_TRADES_PATH.exists():
        raise FileNotFoundError(
            f"Missing filtered trades file: {FILTERED_TRADES_PATH}. "
            "Run python -m src.execution.turnover_control_engine first."
        )

    trades = pd.read_csv(FILTERED_TRADES_PATH)

    required_columns = {
        "asset",
        "current_weight",
        "target_weight",
        "trade_weight",
        "absolute_trade_weight",
        "action",
        "execution_action",
        "filtered_trade_weight",
        "filtered_absolute_trade_weight",
    }

    missing = required_columns - set(trades.columns)
    if missing:
        raise ValueError(f"Filtered trades missing columns: {missing}")

    return trades


def get_asset_cost_bps(asset: str, cost_component: Dict[str, float]) -> float:
    return float(cost_component.get(asset, cost_component.get("DEFAULT", 0.0)))


def estimate_transaction_costs(
    filtered_trades: pd.DataFrame,
    portfolio_value: float = DEFAULT_PORTFOLIO_VALUE,
    cost_model: Dict[str, Any] = DEFAULT_COST_MODEL,
) -> pd.DataFrame:
    if portfolio_value <= 0:
        raise ValueError("Portfolio value must be positive.")

    rows = []

    for _, row in filtered_trades.iterrows():
        asset = row["asset"]
        execution_action = row["execution_action"]
        trade_weight = float(row["filtered_trade_weight"])
        absolute_trade_weight = abs(trade_weight)
        trade_notional = absolute_trade_weight * portfolio_value

        if execution_action in {"SKIP", "HOLD"} or absolute_trade_weight == 0:
            commission_bps = 0.0
            spread_bps = 0.0
            slippage_bps = 0.0
            market_impact_bps = 0.0
        else:
            commission_bps = float(cost_model["commission_bps"])
            spread_bps = get_asset_cost_bps(asset, cost_model["spread_bps"])
            slippage_bps = get_asset_cost_bps(asset, cost_model["slippage_bps"])
            market_impact_bps = (
                absolute_trade_weight * float(cost_model["market_impact_multiplier_bps"])
            )

        total_cost_bps = (
            commission_bps
            + spread_bps
            + slippage_bps
            + market_impact_bps
        )

        estimated_cost_dollars = trade_notional * total_cost_bps / 10_000
        estimated_cost_weight = estimated_cost_dollars / portfolio_value

        rows.append(
            {
                "asset": asset,
                "execution_action": execution_action,
                "trade_weight": trade_weight,
                "absolute_trade_weight": absolute_trade_weight,
                "trade_notional": trade_notional,
                "commission_bps": commission_bps,
                "spread_bps": spread_bps,
                "slippage_bps": slippage_bps,
                "market_impact_bps": market_impact_bps,
                "total_cost_bps": total_cost_bps,
                "estimated_cost_dollars": estimated_cost_dollars,
                "estimated_cost_weight": estimated_cost_weight,
            }
        )

    return pd.DataFrame(rows)


def calculate_cost_summary(cost_report: pd.DataFrame) -> Dict[str, Any]:
    executable = cost_report[
        ~cost_report["execution_action"].isin(["SKIP", "HOLD"])
    ]

    total_trade_notional = cost_report["trade_notional"].sum()
    total_cost_dollars = cost_report["estimated_cost_dollars"].sum()
    total_cost_weight = cost_report["estimated_cost_weight"].sum()

    avg_cost_bps = (
        executable["total_cost_bps"].mean()
        if not executable.empty
        else 0.0
    )

    most_expensive_asset = None
    if not executable.empty:
        most_expensive_asset = executable.sort_values(
            "estimated_cost_dollars",
            ascending=False,
        ).iloc[0]["asset"]

    return {
        "total_trade_notional": float(total_trade_notional),
        "total_estimated_cost_dollars": float(total_cost_dollars),
        "total_estimated_cost_weight": float(total_cost_weight),
        "total_estimated_cost_bps_of_portfolio": float(total_cost_weight * 10_000),
        "average_cost_bps_per_executable_trade": float(avg_cost_bps),
        "number_of_executable_trades": int(len(executable)),
        "most_expensive_asset": most_expensive_asset,
    }


def save_cost_report(cost_report: pd.DataFrame) -> None:
    ensure_execution_dir()
    cost_report.to_csv(COST_REPORT_PATH, index=False)


def save_cost_summary(summary: Dict[str, Any]) -> None:
    ensure_execution_dir()

    with COST_SUMMARY_PATH.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=4)


def print_cost_report(cost_report: pd.DataFrame, summary: Dict[str, Any]) -> None:
    print("=" * 80)
    print("AURUM TRANSACTION COST ENGINE")
    print("=" * 80)

    print("\nTRANSACTION COST REPORT")
    print("-" * 80)

    display = cost_report.copy()

    display["trade_weight"] = display["trade_weight"].map(lambda x: f"{x:+.2%}")
    display["absolute_trade_weight"] = display["absolute_trade_weight"].map(lambda x: f"{x:.2%}")
    display["trade_notional"] = display["trade_notional"].map(lambda x: f"${x:,.2f}")
    display["estimated_cost_dollars"] = display["estimated_cost_dollars"].map(lambda x: f"${x:,.2f}")
    display["estimated_cost_weight"] = display["estimated_cost_weight"].map(lambda x: f"{x:.4%}")

    print(display.to_string(index=False))

    print("\nTRANSACTION COST SUMMARY")
    print("-" * 80)
    print(f"Total Trade Notional: ${summary['total_trade_notional']:,.2f}")
    print(f"Total Estimated Cost: ${summary['total_estimated_cost_dollars']:,.2f}")
    print(
        "Cost as Portfolio Weight: "
        f"{summary['total_estimated_cost_weight']:.4%}"
    )
    print(
        "Cost in Portfolio bps: "
        f"{summary['total_estimated_cost_bps_of_portfolio']:.2f} bps"
    )
    print(
        "Avg Cost per Executable Trade: "
        f"{summary['average_cost_bps_per_executable_trade']:.2f} bps"
    )
    print(f"Executable Trades: {summary['number_of_executable_trades']}")
    print(f"Most Expensive Asset: {summary['most_expensive_asset']}")

    print("\nOUTPUTS")
    print("-" * 80)
    print(f"Cost Report: {COST_REPORT_PATH}")
    print(f"Cost Summary: {COST_SUMMARY_PATH}")

    print("\nAURUM TRANSACTION COST ENGINE COMPLETE")


def main() -> None:
    ensure_execution_dir()

    filtered_trades = load_filtered_trades()

    cost_report = estimate_transaction_costs(
        filtered_trades=filtered_trades,
        portfolio_value=DEFAULT_PORTFOLIO_VALUE,
        cost_model=DEFAULT_COST_MODEL,
    )

    summary = calculate_cost_summary(cost_report)

    save_cost_report(cost_report)
    save_cost_summary(summary)

    print_cost_report(cost_report, summary)


if __name__ == "__main__":
    main()