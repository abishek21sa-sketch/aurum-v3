# src/execution/portfolio_state_engine.py

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

import pandas as pd


EXECUTION_DIR = Path("results/execution")
STATE_PATH = EXECUTION_DIR / "current_portfolio_state.json"
HISTORY_PATH = EXECUTION_DIR / "portfolio_history.csv"
SUMMARY_PATH = EXECUTION_DIR / "portfolio_state_summary.json"


DEFAULT_PORTFOLIO_VALUE = 1_000_000.0

DEFAULT_POSITIONS = {
    "SPY": 0.25,
    "QQQ": 0.20,
    "TLT": 0.30,
    "GLD": 0.15,
    "CASH": 0.10,
}


def ensure_execution_dir() -> None:
    EXECUTION_DIR.mkdir(parents=True, exist_ok=True)


def current_timestamp() -> str:
    return datetime.now().isoformat(timespec="seconds")


def create_default_portfolio() -> Dict[str, Any]:
    return {
        "timestamp": current_timestamp(),
        "portfolio_value": DEFAULT_PORTFOLIO_VALUE,
        "positions": DEFAULT_POSITIONS.copy(),
    }


def validate_portfolio_state(state: Dict[str, Any]) -> None:
    required_keys = {"timestamp", "portfolio_value", "positions"}

    missing = required_keys - set(state.keys())
    if missing:
        raise ValueError(f"Portfolio state missing keys: {missing}")

    positions = state["positions"]

    if not isinstance(positions, dict) or not positions:
        raise ValueError("Portfolio positions must be a non-empty dictionary.")

    if "CASH" not in positions:
        raise ValueError("Portfolio must include CASH position.")

    total_weight = sum(float(w) for w in positions.values())

    if abs(total_weight - 1.0) > 0.001:
        raise ValueError(f"Portfolio weights must sum to 1. Current sum: {total_weight:.6f}")

    if state["portfolio_value"] <= 0:
        raise ValueError("Portfolio value must be positive.")


def save_portfolio_state(state: Dict[str, Any]) -> None:
    ensure_execution_dir()
    validate_portfolio_state(state)

    with STATE_PATH.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=4)


def load_portfolio_state() -> Dict[str, Any]:
    ensure_execution_dir()

    if not STATE_PATH.exists():
        state = create_default_portfolio()
        save_portfolio_state(state)
        append_portfolio_history(state)
        save_portfolio_summary(state)
        return state

    with STATE_PATH.open("r", encoding="utf-8") as f:
        state = json.load(f)

    validate_portfolio_state(state)
    return state


def append_portfolio_history(state: Dict[str, Any]) -> None:
    ensure_execution_dir()
    validate_portfolio_state(state)

    row = {
        "timestamp": state["timestamp"],
        "portfolio_value": state["portfolio_value"],
        **state["positions"],
    }

    new_row = pd.DataFrame([row])

    if HISTORY_PATH.exists():
        history = pd.read_csv(HISTORY_PATH)
        history = pd.concat([history, new_row], ignore_index=True)
    else:
        history = new_row

    history.to_csv(HISTORY_PATH, index=False)


def calculate_portfolio_summary(state: Dict[str, Any]) -> Dict[str, Any]:
    validate_portfolio_state(state)

    positions = state["positions"]
    total_weight = sum(positions.values())
    largest_asset = max(positions, key=positions.get)
    largest_weight = positions[largest_asset]

    summary = {
        "timestamp": state["timestamp"],
        "portfolio_value": state["portfolio_value"],
        "number_of_positions": len(positions),
        "largest_position": largest_asset,
        "largest_position_weight": largest_weight,
        "cash_weight": positions.get("CASH", 0.0),
        "total_weight": total_weight,
        "fully_invested": abs(total_weight - 1.0) <= 0.001,
    }

    return summary


def save_portfolio_summary(state: Dict[str, Any]) -> Dict[str, Any]:
    ensure_execution_dir()

    summary = calculate_portfolio_summary(state)

    with SUMMARY_PATH.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=4)

    return summary


def update_portfolio_state(
    positions: Dict[str, float],
    portfolio_value: float = DEFAULT_PORTFOLIO_VALUE,
) -> Dict[str, Any]:
    state = {
        "timestamp": current_timestamp(),
        "portfolio_value": float(portfolio_value),
        "positions": positions,
    }

    save_portfolio_state(state)
    append_portfolio_history(state)
    save_portfolio_summary(state)

    return state


def print_portfolio_state(state: Dict[str, Any], summary: Dict[str, Any]) -> None:
    print("=" * 80)
    print("AURUM PORTFOLIO STATE ENGINE")
    print("=" * 80)

    print(f"\nTimestamp: {state['timestamp']}")
    print(f"Portfolio Value: ${state['portfolio_value']:,.2f}")

    print("\nCURRENT POSITIONS")
    print("-" * 80)

    for asset, weight in state["positions"].items():
        print(f"{asset:<10} {weight:>8.2%}")

    print("\nPORTFOLIO SUMMARY")
    print("-" * 80)
    print(f"Number of Positions: {summary['number_of_positions']}")
    print(
        f"Largest Position: {summary['largest_position']} "
        f"({summary['largest_position_weight']:.2%})"
    )
    print(f"Cash Allocation: {summary['cash_weight']:.2%}")
    print(f"Total Weight: {summary['total_weight']:.2%}")
    print(f"Fully Invested: {summary['fully_invested']}")

    print("\nOUTPUTS")
    print("-" * 80)
    print(f"State Saved: {STATE_PATH}")
    print(f"History Updated: {HISTORY_PATH}")
    print(f"Summary Saved: {SUMMARY_PATH}")

    print("\nAURUM PORTFOLIO STATE ENGINE COMPLETE")


def main() -> None:
    state = load_portfolio_state()

    # Refresh timestamp each run so history records execution time
    state["timestamp"] = current_timestamp()

    save_portfolio_state(state)
    append_portfolio_history(state)
    summary = save_portfolio_summary(state)

    print_portfolio_state(state, summary)


if __name__ == "__main__":
    main()