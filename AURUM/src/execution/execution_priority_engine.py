# src/execution/execution_priority_engine.py

from pathlib import Path
from typing import Dict, Any

import json
import pandas as pd


EXECUTION_DIR = Path("results/execution")

REBALANCE_DECISION_PATH = EXECUTION_DIR / "rebalance_decision.csv"
REBALANCE_SCHEDULE_PATH = EXECUTION_DIR / "rebalance_schedule.json"

EXECUTION_PRIORITY_PATH = EXECUTION_DIR / "execution_priority.csv"
EXECUTION_PRIORITY_SUMMARY_PATH = EXECUTION_DIR / "execution_priority_summary.json"


RISK_REDUCTION_ASSETS = {"BTC-USD", "ETH-USD", "VIX", "QQQ", "SPY"}
DEFENSIVE_ASSETS = {"TLT", "GLD", "CASH"}


def ensure_execution_dir() -> None:
    EXECUTION_DIR.mkdir(parents=True, exist_ok=True)


def load_rebalance_decisions() -> pd.DataFrame:
    if not REBALANCE_DECISION_PATH.exists():
        raise FileNotFoundError(
            f"Missing rebalance decision file: {REBALANCE_DECISION_PATH}. "
            "Run python -m src.execution.cost_aware_rebalancer first."
        )

    decisions = pd.read_csv(REBALANCE_DECISION_PATH)

    required_columns = {
        "asset",
        "execution_action",
        "trade_weight",
        "absolute_trade_weight",
        "trade_notional",
        "total_cost_bps",
        "estimated_cost_dollars",
        "rebalance_decision",
        "approved_for_execution",
    }

    missing = required_columns - set(decisions.columns)
    if missing:
        raise ValueError(f"Rebalance decisions missing columns: {missing}")

    return decisions


def load_rebalance_schedule() -> Dict[str, Any]:
    if not REBALANCE_SCHEDULE_PATH.exists():
        raise FileNotFoundError(
            f"Missing rebalance schedule file: {REBALANCE_SCHEDULE_PATH}. "
            "Run python -m src.execution.rebalance_scheduler first."
        )

    with REBALANCE_SCHEDULE_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def risk_reduction_score(asset: str, action: str) -> float:
    if action == "SELL" and asset in RISK_REDUCTION_ASSETS:
        return 1.0

    if action == "BUY" and asset in DEFENSIVE_ASSETS:
        return 0.8

    if action == "SELL":
        return 0.6

    if action == "BUY":
        return 0.4

    return 0.0


def trade_size_score(abs_trade_weight: float) -> float:
    return min(float(abs_trade_weight) / 0.20, 1.0)


def cost_efficiency_score(total_cost_bps: float) -> float:
    max_reasonable_cost_bps = 10.0
    score = 1.0 - min(float(total_cost_bps) / max_reasonable_cost_bps, 1.0)
    return max(score, 0.0)


def urgency_score(schedule: Dict[str, Any]) -> float:
    decision = schedule.get("decision", {})
    recommendation = decision.get("recommendation", "NO_REBALANCE")
    trigger_reasons = decision.get("trigger_reasons", [])

    score = 0.0

    if recommendation == "REBALANCE_NOW":
        score += 0.5

    if "event_trigger_active" in trigger_reasons:
        score += 0.25

    if "turnover_above_threshold" in trigger_reasons:
        score += 0.15

    if "calendar_schedule_due" in trigger_reasons:
        score += 0.10

    return min(score, 1.0)


def assign_execution_priority(
    decisions: pd.DataFrame,
    schedule: Dict[str, Any],
) -> pd.DataFrame:
    approved = decisions[decisions["approved_for_execution"] == True].copy()

    if approved.empty:
        return approved

    global_urgency = urgency_score(schedule)

    approved["risk_reduction_score"] = approved.apply(
        lambda row: risk_reduction_score(
            asset=row["asset"],
            action=row["execution_action"],
        ),
        axis=1,
    )

    approved["trade_size_score"] = approved["absolute_trade_weight"].apply(
        trade_size_score
    )

    approved["cost_efficiency_score"] = approved["total_cost_bps"].apply(
        cost_efficiency_score
    )

    approved["urgency_score"] = global_urgency

    approved["execution_priority_score"] = (
        0.40 * approved["risk_reduction_score"]
        + 0.25 * approved["trade_size_score"]
        + 0.20 * approved["cost_efficiency_score"]
        + 0.15 * approved["urgency_score"]
    )

    approved = approved.sort_values(
        by="execution_priority_score",
        ascending=False,
    ).reset_index(drop=True)

    approved["execution_rank"] = range(1, len(approved) + 1)

    approved["execution_bucket"] = approved["execution_priority_score"].apply(
        lambda x: "HIGH" if x >= 0.75 else "MEDIUM" if x >= 0.50 else "LOW"
    )

    return approved


def calculate_priority_summary(priority: pd.DataFrame) -> Dict[str, Any]:
    if priority.empty:
        return {
            "number_of_priority_trades": 0,
            "highest_priority_asset": None,
            "highest_priority_action": None,
            "average_priority_score": 0.0,
            "high_priority_count": 0,
            "medium_priority_count": 0,
            "low_priority_count": 0,
        }

    top = priority.iloc[0]

    return {
        "number_of_priority_trades": int(len(priority)),
        "highest_priority_asset": top["asset"],
        "highest_priority_action": top["execution_action"],
        "average_priority_score": float(priority["execution_priority_score"].mean()),
        "high_priority_count": int((priority["execution_bucket"] == "HIGH").sum()),
        "medium_priority_count": int((priority["execution_bucket"] == "MEDIUM").sum()),
        "low_priority_count": int((priority["execution_bucket"] == "LOW").sum()),
    }


def save_execution_priority(priority: pd.DataFrame) -> None:
    ensure_execution_dir()
    priority.to_csv(EXECUTION_PRIORITY_PATH, index=False)


def save_priority_summary(summary: Dict[str, Any]) -> None:
    ensure_execution_dir()

    with EXECUTION_PRIORITY_SUMMARY_PATH.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=4)


def print_priority_report(priority: pd.DataFrame, summary: Dict[str, Any]) -> None:
    print("=" * 80)
    print("AURUM EXECUTION PRIORITY ENGINE")
    print("=" * 80)

    print("\nEXECUTION PRIORITY QUEUE")
    print("-" * 80)

    if priority.empty:
        print("No approved trades available for prioritization.")
    else:
        display = priority.copy()

        display["trade_weight"] = display["trade_weight"].map(lambda x: f"{x:+.2%}")
        display["absolute_trade_weight"] = display["absolute_trade_weight"].map(
            lambda x: f"{x:.2%}"
        )
        display["trade_notional"] = display["trade_notional"].map(
            lambda x: f"${x:,.2f}"
        )
        display["estimated_cost_dollars"] = display["estimated_cost_dollars"].map(
            lambda x: f"${x:,.2f}"
        )

        score_cols = [
            "risk_reduction_score",
            "trade_size_score",
            "cost_efficiency_score",
            "urgency_score",
            "execution_priority_score",
        ]

        for col in score_cols:
            display[col] = display[col].map(lambda x: f"{x:.3f}")

        selected_cols = [
            "execution_rank",
            "asset",
            "execution_action",
            "trade_weight",
            "trade_notional",
            "total_cost_bps",
            "risk_reduction_score",
            "trade_size_score",
            "cost_efficiency_score",
            "urgency_score",
            "execution_priority_score",
            "execution_bucket",
        ]

        print(display[selected_cols].to_string(index=False))

    print("\nPRIORITY SUMMARY")
    print("-" * 80)
    print(f"Priority Trades: {summary['number_of_priority_trades']}")
    print(f"Highest Priority Asset: {summary['highest_priority_asset']}")
    print(f"Highest Priority Action: {summary['highest_priority_action']}")
    print(f"Average Priority Score: {summary['average_priority_score']:.3f}")
    print(f"High Priority Count: {summary['high_priority_count']}")
    print(f"Medium Priority Count: {summary['medium_priority_count']}")
    print(f"Low Priority Count: {summary['low_priority_count']}")

    print("\nOUTPUTS")
    print("-" * 80)
    print(f"Execution Priority: {EXECUTION_PRIORITY_PATH}")
    print(f"Priority Summary: {EXECUTION_PRIORITY_SUMMARY_PATH}")

    print("\nAURUM EXECUTION PRIORITY ENGINE COMPLETE")


def main() -> None:
    ensure_execution_dir()

    decisions = load_rebalance_decisions()
    schedule = load_rebalance_schedule()

    priority = assign_execution_priority(
        decisions=decisions,
        schedule=schedule,
    )

    summary = calculate_priority_summary(priority)

    save_execution_priority(priority)
    save_priority_summary(summary)

    print_priority_report(priority, summary)


if __name__ == "__main__":
    main()