# src/optimization/optimizer_report_generator.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pandas as pd


RESULTS_DIR = Path("results/optimization")


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}

    return json.loads(path.read_text(encoding="utf-8"))


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()

    return pd.read_csv(path)


def build_final_decision_report() -> Dict[str, Any]:
    optimizer_report = load_json(RESULTS_DIR / "optimizer_report.json")
    constraint_report = load_json(RESULTS_DIR / "portfolio_constraints.json")
    turnover_report = load_json(RESULTS_DIR / "turnover_report.json")
    volatility_report = load_json(RESULTS_DIR / "volatility_target_report.json")

    allocation_df = load_csv(RESULTS_DIR / "allocation_recommendation.csv")
    trades_df = load_csv(RESULTS_DIR / "allocation_rebalance_trades.csv")

    selected_optimizer = optimizer_report.get("selected_optimizer", "unknown")
    market_conditions = optimizer_report.get("market_conditions", {})
    final_weights = optimizer_report.get("final_recommended_weights", {})

    top_positions = (
        allocation_df.head(5).to_dict(orient="records")
        if not allocation_df.empty
        else []
    )

    trade_summary = (
        trades_df[trades_df["action"] != "HOLD"].to_dict(orient="records")
        if not trades_df.empty and "action" in trades_df.columns
        else []
    )

    decision_report = {
        "report_type": "AURUM_FINAL_OPTIMIZER_DECISION_REPORT",
        "selected_optimizer": selected_optimizer,
        "market_regime": market_conditions.get("regime", "unknown"),
        "forecast_confidence": market_conditions.get("forecast_confidence"),
        "crisis_probability": market_conditions.get("crisis_probability"),
        "estimated_volatility": market_conditions.get("estimated_volatility"),
        "target_volatility": market_conditions.get("target_volatility"),
        "selection_reason": optimizer_report.get("selection_reason", ""),
        "final_recommended_weights": final_weights,
        "top_positions": top_positions,
        "risk_controls": {
            "constraint_verdict": optimizer_report.get(
                "constraint_summary", {}
            ).get("institutional_verdict"),
            "constraint_breach_count": optimizer_report.get(
                "constraint_summary", {}
            ).get("breach_count"),
            "turnover": optimizer_report.get(
                "turnover_summary", {}
            ).get("turnover"),
            "turnover_verdict": optimizer_report.get(
                "turnover_summary", {}
            ).get("institutional_verdict"),
            "transaction_cost_estimate": optimizer_report.get(
                "turnover_summary", {}
            ).get("transaction_cost_estimate"),
            "risk_scale": optimizer_report.get(
                "volatility_targeting_summary", {}
            ).get("risk_scale"),
            "cash_weight": optimizer_report.get(
                "volatility_targeting_summary", {}
            ).get("cash_weight"),
            "volatility_verdict": optimizer_report.get(
                "volatility_targeting_summary", {}
            ).get("institutional_verdict"),
        },
        "rebalance_trade_summary": trade_summary,
        "institutional_final_decision": generate_final_decision_text(
            optimizer_report
        ),
        "source_files_used": {
            "optimizer_report": bool(optimizer_report),
            "portfolio_constraints": bool(constraint_report),
            "turnover_report": bool(turnover_report),
            "volatility_target_report": bool(volatility_report),
            "allocation_recommendation": not allocation_df.empty,
            "allocation_rebalance_trades": not trades_df.empty,
        },
    }

    return decision_report


def generate_final_decision_text(report: Dict[str, Any]) -> Dict[str, str]:
    selected_optimizer = report.get("selected_optimizer", "unknown")
    market = report.get("market_conditions", {})
    risk = report.get("volatility_targeting_summary", {})
    turnover = report.get("turnover_summary", {})
    constraints = report.get("constraint_summary", {})

    regime = market.get("regime", "unknown")
    confidence = market.get("forecast_confidence", "unknown")
    crisis_probability = market.get("crisis_probability", "unknown")
    cash_weight = risk.get("cash_weight", 0.0)
    risk_scale = risk.get("risk_scale", 1.0)

    decision = (
        f"AURUM recommends using the {selected_optimizer} allocation framework "
        f"under the current {regime} regime."
    )

    risk_comment = (
        f"The portfolio is scaled by a risk factor of {risk_scale}, "
        f"with {cash_weight:.2%} allocated to cash."
        if isinstance(cash_weight, (int, float))
        else "Risk scaling information is unavailable."
    )

    execution_comment = (
        f"Expected turnover is {turnover.get('turnover', 0.0):.2%}, "
        f"classified as {turnover.get('institutional_verdict', 'unknown')}."
        if isinstance(turnover.get("turnover"), (int, float))
        else "Turnover information is unavailable."
    )

    governance_comment = (
        f"Portfolio constraints were classified as "
        f"{constraints.get('institutional_verdict', 'unknown')} "
        f"with {constraints.get('breach_count', 'unknown')} breach(es)."
    )

    final_verdict = report.get(
        "institutional_decision", {}
    ).get("final_verdict", "REVIEW_REQUIRED")

    return {
        "decision": decision,
        "market_context": (
            f"Forecast confidence is {confidence}, and crisis probability is "
            f"{crisis_probability}."
        ),
        "risk_comment": risk_comment,
        "execution_comment": execution_comment,
        "governance_comment": governance_comment,
        "final_verdict": final_verdict,
    }


def save_final_report(report: Dict[str, Any]) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    json_path = RESULTS_DIR / "final_optimizer_decision_report.json"
    csv_path = RESULTS_DIR / "final_optimizer_decision_summary.csv"

    json_path.write_text(
        json.dumps(report, indent=4),
        encoding="utf-8",
    )

    summary_rows = [
        {
            "metric": "selected_optimizer",
            "value": report.get("selected_optimizer"),
        },
        {
            "metric": "market_regime",
            "value": report.get("market_regime"),
        },
        {
            "metric": "forecast_confidence",
            "value": report.get("forecast_confidence"),
        },
        {
            "metric": "crisis_probability",
            "value": report.get("crisis_probability"),
        },
        {
            "metric": "estimated_volatility",
            "value": report.get("estimated_volatility"),
        },
        {
            "metric": "target_volatility",
            "value": report.get("target_volatility"),
        },
        {
            "metric": "cash_weight",
            "value": report.get("risk_controls", {}).get("cash_weight"),
        },
        {
            "metric": "risk_scale",
            "value": report.get("risk_controls", {}).get("risk_scale"),
        },
        {
            "metric": "turnover",
            "value": report.get("risk_controls", {}).get("turnover"),
        },
        {
            "metric": "turnover_verdict",
            "value": report.get("risk_controls", {}).get("turnover_verdict"),
        },
        {
            "metric": "constraint_verdict",
            "value": report.get("risk_controls", {}).get("constraint_verdict"),
        },
        {
            "metric": "final_verdict",
            "value": report.get(
                "institutional_final_decision", {}
            ).get("final_verdict"),
        },
    ]

    pd.DataFrame(summary_rows).to_csv(csv_path, index=False)

    print(f"Saved final optimizer decision report: {json_path}")
    print(f"Saved final optimizer decision summary: {csv_path}")


def run_report_generator() -> Dict[str, Any]:
    report = build_final_decision_report()
    save_final_report(report)

    decision = report["institutional_final_decision"]
    risk = report["risk_controls"]

    print("\nAURUM FINAL OPTIMIZER DECISION REPORT")
    print("=" * 80)

    print(f"Selected Optimizer: {report['selected_optimizer']}")
    print(f"Market Regime:      {report['market_regime']}")
    print(f"Final Verdict:      {decision['final_verdict']}")

    print("\nDECISION")
    print("-" * 80)
    print(decision["decision"])

    print("\nMARKET CONTEXT")
    print("-" * 80)
    print(decision["market_context"])

    print("\nRISK CONTROL SUMMARY")
    print("-" * 80)
    print(f"Cash Weight:        {risk.get('cash_weight'):.2%}")
    print(f"Risk Scale:         {risk.get('risk_scale'):.4f}")
    print(f"Turnover:           {risk.get('turnover'):.2%}")
    print(f"Turnover Verdict:   {risk.get('turnover_verdict')}")
    print(f"Constraint Verdict: {risk.get('constraint_verdict')}")

    print("\nTOP POSITIONS")
    print("-" * 80)
    for row in report["top_positions"]:
        asset = row.get("asset")
        weight = row.get("recommended_weight")
        print(f"{asset:<10} {weight:>8.2%}")

    return report


if __name__ == "__main__":
    run_report_generator()