# src/execution/cost_aware_rebalancer.py

import json
from pathlib import Path
from typing import Dict, Any

import pandas as pd


EXECUTION_DIR = Path("results/execution")

TRANSACTION_COST_REPORT_PATH = EXECUTION_DIR / "transaction_cost_report.csv"
REBALANCE_DECISION_PATH = EXECUTION_DIR / "rebalance_decision.csv"
REBALANCE_SUMMARY_PATH = EXECUTION_DIR / "rebalance_decision_summary.json"

MIN_TRADE_WEIGHT_TO_EXECUTE = 0.02
MAX_COST_BPS_TO_EXECUTE = 10.0
REVIEW_COST_BPS_THRESHOLD = 6.0


def ensure_execution_dir() -> None:
    EXECUTION_DIR.mkdir(parents=True, exist_ok=True)


def load_transaction_cost_report() -> pd.DataFrame:
    if not TRANSACTION_COST_REPORT_PATH.exists():
        raise FileNotFoundError(
            f"Missing transaction cost report: {TRANSACTION_COST_REPORT_PATH}. "
            "Run python -m src.execution.transaction_cost_engine first."
        )

    report = pd.read_csv(TRANSACTION_COST_REPORT_PATH)

    required_columns = {
        "asset",
        "execution_action",
        "trade_weight",
        "absolute_trade_weight",
        "trade_notional",
        "total_cost_bps",
        "estimated_cost_dollars",
        "estimated_cost_weight",
    }

    missing = required_columns - set(report.columns)
    if missing:
        raise ValueError(f"Transaction cost report missing columns: {missing}")

    return report


def assign_rebalance_decision(row: pd.Series) -> str:
    action = row["execution_action"]
    trade_size = float(row["absolute_trade_weight"])
    cost_bps = float(row["total_cost_bps"])

    if action in {"SKIP", "HOLD"} or trade_size == 0:
        return "SKIP"

    if trade_size < MIN_TRADE_WEIGHT_TO_EXECUTE:
        return "SKIP"

    if cost_bps > MAX_COST_BPS_TO_EXECUTE:
        return "SKIP_COST_TOO_HIGH"

    if cost_bps >= REVIEW_COST_BPS_THRESHOLD:
        return "REVIEW"

    return "EXECUTE"


def add_rebalance_decisions(cost_report: pd.DataFrame) -> pd.DataFrame:
    decisions = cost_report.copy()

    decisions["rebalance_decision"] = decisions.apply(
        assign_rebalance_decision,
        axis=1,
    )

    decisions["approved_for_execution"] = decisions["rebalance_decision"].eq("EXECUTE")

    decisions["decision_reason"] = decisions.apply(
        lambda row: explain_decision(row),
        axis=1,
    )

    return decisions


def explain_decision(row: pd.Series) -> str:
    decision = row["rebalance_decision"]
    action = row["execution_action"]
    trade_size = float(row["absolute_trade_weight"])
    cost_bps = float(row["total_cost_bps"])

    if decision == "EXECUTE":
        return "Trade is material and transaction cost is acceptable."

    if decision == "REVIEW":
        return "Trade is material but transaction cost is elevated; manual review recommended."

    if decision == "SKIP_COST_TOO_HIGH":
        return "Transaction cost exceeds maximum allowed threshold."

    if action in {"SKIP", "HOLD"} or trade_size == 0:
        return "No executable trade required."

    if trade_size < MIN_TRADE_WEIGHT_TO_EXECUTE:
        return "Trade is below minimum execution size threshold."

    return "Skipped by cost-aware rebalance policy."


def calculate_rebalance_summary(decisions: pd.DataFrame) -> Dict[str, Any]:
    executable = decisions[decisions["rebalance_decision"] == "EXECUTE"]
    review = decisions[decisions["rebalance_decision"] == "REVIEW"]
    skipped = decisions[decisions["rebalance_decision"].str.startswith("SKIP")]

    approved_notional = executable["trade_notional"].sum()
    approved_cost = executable["estimated_cost_dollars"].sum()
    approved_cost_weight = executable["estimated_cost_weight"].sum()

    total_notional = decisions["trade_notional"].sum()
    total_cost = decisions["estimated_cost_dollars"].sum()

    return {
        "total_assets_reviewed": int(len(decisions)),
        "execute_count": int(len(executable)),
        "review_count": int(len(review)),
        "skip_count": int(len(skipped)),
        "approved_trade_notional": float(approved_notional),
        "approved_estimated_cost_dollars": float(approved_cost),
        "approved_estimated_cost_weight": float(approved_cost_weight),
        "approved_estimated_cost_bps_of_portfolio": float(approved_cost_weight * 10_000),
        "total_candidate_trade_notional": float(total_notional),
        "total_candidate_cost_dollars": float(total_cost),
        "decision_policy": {
            "min_trade_weight_to_execute": MIN_TRADE_WEIGHT_TO_EXECUTE,
            "review_cost_bps_threshold": REVIEW_COST_BPS_THRESHOLD,
            "max_cost_bps_to_execute": MAX_COST_BPS_TO_EXECUTE,
        },
    }


def save_rebalance_decisions(decisions: pd.DataFrame) -> None:
    ensure_execution_dir()
    decisions.to_csv(REBALANCE_DECISION_PATH, index=False)


def save_rebalance_summary(summary: Dict[str, Any]) -> None:
    ensure_execution_dir()

    with REBALANCE_SUMMARY_PATH.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=4)


def print_rebalance_report(decisions: pd.DataFrame, summary: Dict[str, Any]) -> None:
    print("=" * 80)
    print("AURUM COST-AWARE REBALANCER")
    print("=" * 80)

    print("\nREBALANCE DECISIONS")
    print("-" * 80)

    display = decisions.copy()

    display["trade_weight"] = display["trade_weight"].map(lambda x: f"{x:+.2%}")
    display["absolute_trade_weight"] = display["absolute_trade_weight"].map(lambda x: f"{x:.2%}")
    display["trade_notional"] = display["trade_notional"].map(lambda x: f"${x:,.2f}")
    display["estimated_cost_dollars"] = display["estimated_cost_dollars"].map(lambda x: f"${x:,.2f}")
    display["estimated_cost_weight"] = display["estimated_cost_weight"].map(lambda x: f"{x:.4%}")

    print(display.to_string(index=False))

    print("\nREBALANCE SUMMARY")
    print("-" * 80)
    print(f"Assets Reviewed: {summary['total_assets_reviewed']}")
    print(f"Execute: {summary['execute_count']}")
    print(f"Review: {summary['review_count']}")
    print(f"Skip: {summary['skip_count']}")
    print(f"Approved Trade Notional: ${summary['approved_trade_notional']:,.2f}")
    print(f"Approved Estimated Cost: ${summary['approved_estimated_cost_dollars']:,.2f}")
    print(
        "Approved Cost in Portfolio bps: "
        f"{summary['approved_estimated_cost_bps_of_portfolio']:.2f} bps"
    )

    print("\nPOLICY")
    print("-" * 80)
    policy = summary["decision_policy"]
    print(f"Minimum Trade Size: {policy['min_trade_weight_to_execute']:.2%}")
    print(f"Review Cost Threshold: {policy['review_cost_bps_threshold']:.2f} bps")
    print(f"Maximum Cost Threshold: {policy['max_cost_bps_to_execute']:.2f} bps")

    print("\nOUTPUTS")
    print("-" * 80)
    print(f"Rebalance Decision: {REBALANCE_DECISION_PATH}")
    print(f"Rebalance Summary: {REBALANCE_SUMMARY_PATH}")

    print("\nAURUM COST-AWARE REBALANCER COMPLETE")


def main() -> None:
    ensure_execution_dir()

    cost_report = load_transaction_cost_report()

    decisions = add_rebalance_decisions(cost_report)
    summary = calculate_rebalance_summary(decisions)

    save_rebalance_decisions(decisions)
    save_rebalance_summary(summary)

    print_rebalance_report(decisions, summary)


if __name__ == "__main__":
    main()