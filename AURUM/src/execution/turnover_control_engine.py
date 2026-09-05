# src/execution/turnover_control_engine.py

from pathlib import Path
from typing import Dict, Any

import pandas as pd


EXECUTION_DIR = Path("results/execution")
TRADE_RECOMMENDATIONS_PATH = EXECUTION_DIR / "trade_recommendations.csv"
FILTERED_TRADES_PATH = EXECUTION_DIR / "filtered_trades.csv"
TURNOVER_SUMMARY_PATH = EXECUTION_DIR / "turnover_control_summary.json"

DEFAULT_TURNOVER_THRESHOLD = 0.02


def ensure_execution_dir() -> None:
    EXECUTION_DIR.mkdir(parents=True, exist_ok=True)


def load_trade_recommendations() -> pd.DataFrame:
    if not TRADE_RECOMMENDATIONS_PATH.exists():
        raise FileNotFoundError(
            f"Missing trade recommendations file: {TRADE_RECOMMENDATIONS_PATH}. "
            "Run python -m src.execution.trade_generation_engine first."
        )

    trades = pd.read_csv(TRADE_RECOMMENDATIONS_PATH)

    required_columns = {
        "asset",
        "current_weight",
        "target_weight",
        "trade_weight",
        "absolute_trade_weight",
        "action",
    }

    missing = required_columns - set(trades.columns)
    if missing:
        raise ValueError(f"Trade recommendations missing columns: {missing}")

    return trades


def apply_turnover_filter(
    trades: pd.DataFrame,
    threshold: float = DEFAULT_TURNOVER_THRESHOLD,
) -> pd.DataFrame:
    if threshold < 0:
        raise ValueError("Turnover threshold must be non-negative.")

    filtered = trades.copy()

    filtered["passes_turnover_filter"] = (
        filtered["absolute_trade_weight"].abs() >= threshold
    )

    filtered["execution_action"] = filtered.apply(
        lambda row: row["action"] if row["passes_turnover_filter"] else "SKIP",
        axis=1,
    )

    filtered["filtered_trade_weight"] = filtered.apply(
        lambda row: row["trade_weight"] if row["passes_turnover_filter"] else 0.0,
        axis=1,
    )

    filtered["filtered_absolute_trade_weight"] = filtered[
        "filtered_trade_weight"
    ].abs()

    return filtered


def calculate_turnover_summary(
    trades: pd.DataFrame,
    filtered: pd.DataFrame,
    threshold: float,
) -> Dict[str, Any]:
    original_turnover = trades["absolute_trade_weight"].sum() / 2
    filtered_turnover = filtered["filtered_absolute_trade_weight"].sum() / 2

    skipped = filtered[~filtered["passes_turnover_filter"]]
    executable = filtered[filtered["passes_turnover_filter"]]

    summary = {
        "turnover_threshold": float(threshold),
        "original_turnover": float(original_turnover),
        "filtered_turnover": float(filtered_turnover),
        "turnover_reduction": float(original_turnover - filtered_turnover),
        "number_of_original_trades": int((trades["action"] != "HOLD").sum()),
        "number_of_executable_trades": int(
            (executable["execution_action"] != "HOLD").sum()
        ),
        "number_of_skipped_trades": int(len(skipped)),
        "skipped_assets": skipped["asset"].tolist(),
    }

    return summary


def save_filtered_trades(filtered: pd.DataFrame) -> None:
    ensure_execution_dir()
    filtered.to_csv(FILTERED_TRADES_PATH, index=False)


def save_turnover_summary(summary: Dict[str, Any]) -> None:
    import json

    ensure_execution_dir()

    with TURNOVER_SUMMARY_PATH.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=4)


def print_turnover_report(
    filtered: pd.DataFrame,
    summary: Dict[str, Any],
) -> None:
    print("=" * 80)
    print("AURUM TURNOVER CONTROL ENGINE")
    print("=" * 80)

    print("\nTURNOVER FILTERED TRADES")
    print("-" * 80)

    display = filtered.copy()

    percent_cols = [
        "current_weight",
        "target_weight",
        "trade_weight",
        "absolute_trade_weight",
        "filtered_trade_weight",
        "filtered_absolute_trade_weight",
    ]

    for col in percent_cols:
        display[col] = display[col].map(lambda x: f"{x:+.2%}" if "trade" in col else f"{x:.2%}")

    print(display.to_string(index=False))

    print("\nTURNOVER SUMMARY")
    print("-" * 80)
    print(f"Threshold: {summary['turnover_threshold']:.2%}")
    print(f"Original Turnover: {summary['original_turnover']:.2%}")
    print(f"Filtered Turnover: {summary['filtered_turnover']:.2%}")
    print(f"Turnover Reduction: {summary['turnover_reduction']:.2%}")
    print(f"Original Trades: {summary['number_of_original_trades']}")
    print(f"Executable Trades: {summary['number_of_executable_trades']}")
    print(f"Skipped Trades: {summary['number_of_skipped_trades']}")
    print(f"Skipped Assets: {summary['skipped_assets']}")

    print("\nOUTPUTS")
    print("-" * 80)
    print(f"Filtered Trades: {FILTERED_TRADES_PATH}")
    print(f"Turnover Summary: {TURNOVER_SUMMARY_PATH}")

    print("\nAURUM TURNOVER CONTROL ENGINE COMPLETE")


def main() -> None:
    ensure_execution_dir()

    trades = load_trade_recommendations()

    filtered = apply_turnover_filter(
        trades=trades,
        threshold=DEFAULT_TURNOVER_THRESHOLD,
    )

    summary = calculate_turnover_summary(
        trades=trades,
        filtered=filtered,
        threshold=DEFAULT_TURNOVER_THRESHOLD,
    )

    save_filtered_trades(filtered)
    save_turnover_summary(summary)
    print_turnover_report(filtered, summary)


if __name__ == "__main__":
    main()