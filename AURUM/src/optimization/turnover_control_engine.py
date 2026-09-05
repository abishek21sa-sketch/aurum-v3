# src/optimization/turnover_control_engine.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

import pandas as pd


RESULTS_DIR = Path("results/optimization")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    total = sum(max(v, 0.0) for v in weights.values())

    if total <= 0:
        return {}

    return {
        asset: max(weight, 0.0) / total
        for asset, weight in weights.items()
    }


def calculate_turnover(
    current_weights: Dict[str, float],
    target_weights: Dict[str, float],
) -> float:

    assets = set(current_weights.keys()) | set(target_weights.keys())

    total_change = sum(
        abs(
            target_weights.get(asset, 0.0)
            - current_weights.get(asset, 0.0)
        )
        for asset in assets
    )

    return 0.5 * total_change


def build_trade_list(
    current_weights: Dict[str, float],
    target_weights: Dict[str, float],
) -> pd.DataFrame:

    assets = sorted(
        set(current_weights.keys()) | set(target_weights.keys())
    )

    trades = []

    for asset in assets:

        current = current_weights.get(asset, 0.0)
        target = target_weights.get(asset, 0.0)

        delta = target - current

        if abs(delta) < 1e-6:
            action = "HOLD"
        elif delta > 0:
            action = "BUY"
        else:
            action = "SELL"

        trades.append(
            {
                "asset": asset,
                "current_weight": current,
                "target_weight": target,
                "weight_change": delta,
                "action": action,
            }
        )

    return pd.DataFrame(trades)


def estimate_transaction_cost(
    turnover: float,
    cost_per_turnover: float = 0.001,
) -> float:
    """
    Default:
    10 bps round-trip estimate
    """

    return turnover * cost_per_turnover


def generate_turnover_report(
    current_weights: Dict[str, float],
    target_weights: Dict[str, float],
) -> Dict:

    current_weights = normalize_weights(current_weights)
    target_weights = normalize_weights(target_weights)

    turnover = calculate_turnover(
        current_weights,
        target_weights,
    )

    transaction_cost = estimate_transaction_cost(turnover)

    trade_df = build_trade_list(
        current_weights,
        target_weights,
    )

    report = {
        "turnover": round(turnover, 6),
        "transaction_cost_estimate": round(
            transaction_cost,
            6,
        ),
        "trade_count": int(
            (trade_df["action"] != "HOLD").sum()
        ),
        "institutional_verdict": (
            "LOW"
            if turnover < 0.10
            else "MODERATE"
            if turnover < 0.30
            else "HIGH"
        ),
    }

    return report, trade_df


def save_outputs(
    report: Dict,
    trade_df: pd.DataFrame,
) -> None:

    json_path = RESULTS_DIR / "turnover_report.json"
    csv_path = RESULTS_DIR / "rebalance_trades.csv"

    json_path.write_text(
        json.dumps(report, indent=4),
        encoding="utf-8",
    )

    trade_df.to_csv(
        csv_path,
        index=False,
    )

    print(f"Saved: {json_path}")
    print(f"Saved: {csv_path}")


def run_demo():

    current_weights = {
        "SPY": 0.20,
        "QQQ": 0.15,
        "TLT": 0.25,
        "GLD": 0.10,
        "BTC-USD": 0.05,
        "CASH": 0.25,
    }

    target_weights = {
        "SPY": 0.30,
        "QQQ": 0.30,
        "TLT": 0.08,
        "GLD": 0.05,
        "BTC-USD": 0.06,
        "ETH-USD": 0.04,
        "CASH": 0.17,
    }

    report, trade_df = generate_turnover_report(
        current_weights,
        target_weights,
    )

    save_outputs(report, trade_df)

    print("\nTURNOVER CONTROL ENGINE")
    print("=" * 70)

    for key, value in report.items():
        print(f"{key:<30} {value}")

    print("\nTRADE LIST")
    print("-" * 70)

    print(
        trade_df[
            [
                "asset",
                "action",
                "weight_change",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    run_demo()