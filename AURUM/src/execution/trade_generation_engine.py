# src/execution/trade_generation_engine.py

import json
from pathlib import Path
from typing import Dict, Any

import pandas as pd

from src.execution.portfolio_state_engine import load_portfolio_state


EXECUTION_DIR = Path("results/execution")
TARGET_PORTFOLIO_PATH = EXECUTION_DIR / "target_portfolio.json"
TRADE_RECOMMENDATIONS_PATH = EXECUTION_DIR / "trade_recommendations.csv"


DEFAULT_TARGET_PORTFOLIO = {
    "SPY": 0.20,
    "QQQ": 0.10,
    "TLT": 0.40,
    "GLD": 0.20,
    "CASH": 0.10,
}


def ensure_execution_dir() -> None:
    EXECUTION_DIR.mkdir(parents=True, exist_ok=True)


def validate_weights(weights: Dict[str, float], name: str) -> None:
    if not weights:
        raise ValueError(f"{name} cannot be empty.")

    total_weight = sum(float(w) for w in weights.values())

    if abs(total_weight - 1.0) > 0.001:
        raise ValueError(
            f"{name} weights must sum to 1. Current sum: {total_weight:.6f}"
        )


def save_default_target_portfolio() -> None:
    ensure_execution_dir()

    payload = {
        "source": "default_phase_3d_target",
        "description": "Default execution target portfolio for Chat 3D testing.",
        "target_weights": DEFAULT_TARGET_PORTFOLIO,
    }

    with TARGET_PORTFOLIO_PATH.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=4)


def load_target_portfolio() -> Dict[str, float]:
    ensure_execution_dir()

    if not TARGET_PORTFOLIO_PATH.exists():
        save_default_target_portfolio()

    with TARGET_PORTFOLIO_PATH.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    if "target_weights" in payload:
        target = payload["target_weights"]
    else:
        target = payload

    target = {asset: float(weight) for asset, weight in target.items()}
    validate_weights(target, "Target portfolio")

    return target


def generate_trade_recommendations(
    current_weights: Dict[str, float],
    target_weights: Dict[str, float],
) -> pd.DataFrame:
    validate_weights(current_weights, "Current portfolio")
    validate_weights(target_weights, "Target portfolio")

    all_assets = sorted(set(current_weights) | set(target_weights))

    rows = []

    for asset in all_assets:
        current_weight = float(current_weights.get(asset, 0.0))
        target_weight = float(target_weights.get(asset, 0.0))
        trade_weight = target_weight - current_weight

        if trade_weight > 0:
            action = "BUY"
        elif trade_weight < 0:
            action = "SELL"
        else:
            action = "HOLD"

        rows.append(
            {
                "asset": asset,
                "current_weight": current_weight,
                "target_weight": target_weight,
                "trade_weight": trade_weight,
                "absolute_trade_weight": abs(trade_weight),
                "action": action,
            }
        )

    trades = pd.DataFrame(rows)

    trades = trades.sort_values(
        by="absolute_trade_weight",
        ascending=False,
    ).reset_index(drop=True)

    return trades


def save_trade_recommendations(trades: pd.DataFrame) -> None:
    ensure_execution_dir()
    trades.to_csv(TRADE_RECOMMENDATIONS_PATH, index=False)


def calculate_trade_summary(trades: pd.DataFrame) -> Dict[str, Any]:
    buy_weight = trades.loc[trades["trade_weight"] > 0, "trade_weight"].sum()
    sell_weight = abs(trades.loc[trades["trade_weight"] < 0, "trade_weight"].sum())

    turnover = trades["absolute_trade_weight"].sum() / 2

    return {
        "number_of_assets": int(len(trades)),
        "number_of_buys": int((trades["action"] == "BUY").sum()),
        "number_of_sells": int((trades["action"] == "SELL").sum()),
        "number_of_holds": int((trades["action"] == "HOLD").sum()),
        "total_buy_weight": float(buy_weight),
        "total_sell_weight": float(sell_weight),
        "estimated_turnover": float(turnover),
    }


def print_trade_report(trades: pd.DataFrame, summary: Dict[str, Any]) -> None:
    print("=" * 80)
    print("AURUM TRADE GENERATION ENGINE")
    print("=" * 80)

    print("\nTRADE RECOMMENDATIONS")
    print("-" * 80)

    display = trades.copy()
    display["current_weight"] = display["current_weight"].map(lambda x: f"{x:.2%}")
    display["target_weight"] = display["target_weight"].map(lambda x: f"{x:.2%}")
    display["trade_weight"] = display["trade_weight"].map(lambda x: f"{x:+.2%}")
    display["absolute_trade_weight"] = display["absolute_trade_weight"].map(
        lambda x: f"{x:.2%}"
    )

    print(display.to_string(index=False))

    print("\nTRADE SUMMARY")
    print("-" * 80)
    print(f"Number of Assets: {summary['number_of_assets']}")
    print(f"Buy Trades: {summary['number_of_buys']}")
    print(f"Sell Trades: {summary['number_of_sells']}")
    print(f"Hold Positions: {summary['number_of_holds']}")
    print(f"Total Buy Weight: {summary['total_buy_weight']:.2%}")
    print(f"Total Sell Weight: {summary['total_sell_weight']:.2%}")
    print(f"Estimated Turnover: {summary['estimated_turnover']:.2%}")

    print("\nOUTPUTS")
    print("-" * 80)
    print(f"Target Portfolio: {TARGET_PORTFOLIO_PATH}")
    print(f"Trade Recommendations: {TRADE_RECOMMENDATIONS_PATH}")

    print("\nAURUM TRADE GENERATION ENGINE COMPLETE")


def main() -> None:
    state = load_portfolio_state()
    current_weights = state["positions"]

    target_weights = load_target_portfolio()

    trades = generate_trade_recommendations(
        current_weights=current_weights,
        target_weights=target_weights,
    )

    save_trade_recommendations(trades)
    summary = calculate_trade_summary(trades)

    print_trade_report(trades, summary)


if __name__ == "__main__":
    main()