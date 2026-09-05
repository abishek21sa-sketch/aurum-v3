# src/optimization/allocation_recommendation_engine.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd

from src.optimization.portfolio_constraint_engine import apply_portfolio_constraints
from src.optimization.turnover_control_engine import generate_turnover_report
from src.optimization.volatility_targeting_engine import apply_volatility_target
from src.optimization.live_optimizer_output_loader import get_optimizer_outputs


RESULTS_DIR = Path("results/optimization")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def get_demo_current_portfolio() -> Dict[str, float]:
    return {
        "SPY": 0.20,
        "QQQ": 0.15,
        "TLT": 0.25,
        "GLD": 0.10,
        "BTC-USD": 0.05,
        "CASH": 0.25,
    }


def get_demo_market_conditions() -> Dict:
    return {
        "regime": "normal",
        "forecast_confidence": 0.67,
        "crisis_probability": 0.21,
        "estimated_volatility": 0.16,
        "target_volatility": 0.10,
    }


def choose_optimizer(
    regime: str,
    forecast_confidence: float,
    crisis_probability: float,
) -> Tuple[str, str]:

    if crisis_probability >= 0.70:
        return (
            "cvar",
            "Crisis probability is elevated. CVaR optimization is preferred for tail-risk protection.",
        )

    if forecast_confidence < 0.45:
        return (
            "bayesian_robust",
            "Forecast confidence is low. Bayesian robust allocation is preferred under parameter uncertainty.",
        )

    if regime == "bull":
        return (
            "black_litterman",
            "Bullish regime with usable confidence. Black-Litterman is preferred to express active views.",
        )

    if regime in {"risk_off", "defensive"}:
        return (
            "minimum_variance",
            "Defensive regime detected. Minimum variance is preferred for capital preservation.",
        )

    if regime == "high_volatility":
        return (
            "cvar",
            "High-volatility regime detected. CVaR is preferred to control downside tail losses.",
        )

    return (
        "risk_parity",
        "Normal market regime. Risk parity is preferred for diversified risk-balanced exposure.",
    )


def build_allocation_dataframe(weights: Dict[str, float]) -> pd.DataFrame:
    rows = []

    for asset, weight in weights.items():
        rows.append(
            {
                "asset": asset,
                "recommended_weight": weight,
            }
        )

    return pd.DataFrame(rows).sort_values(
        "recommended_weight",
        ascending=False,
    )


def generate_allocation_recommendation() -> Dict:
    optimizer_outputs = get_optimizer_outputs()
    current_portfolio = get_demo_current_portfolio()
    market = get_demo_market_conditions()

    selected_optimizer, selection_reason = choose_optimizer(
        regime=market["regime"],
        forecast_confidence=market["forecast_confidence"],
        crisis_probability=market["crisis_probability"],
    )

    raw_weights = optimizer_outputs[selected_optimizer]

    constraint_report = apply_portfolio_constraints(raw_weights)
    constrained_weights = constraint_report["constrained_weights"]

    turnover_report, trade_df = generate_turnover_report(
        current_weights=current_portfolio,
        target_weights=constrained_weights,
    )

    vol_report = apply_volatility_target(
        weights=constrained_weights,
        estimated_volatility=market["estimated_volatility"],
        target_volatility=market["target_volatility"],
        min_cash_weight=0.05,
        max_leverage=1.0,
    )

    final_weights = vol_report["volatility_targeted_weights"]

    allocation_df = build_allocation_dataframe(final_weights)

    report = {
        "selected_optimizer": selected_optimizer,
        "selection_reason": selection_reason,
        "market_conditions": market,
        "raw_optimizer_weights": raw_weights,
        "constrained_weights": constrained_weights,
        "final_recommended_weights": final_weights,
        "constraint_summary": {
            "institutional_verdict": constraint_report["institutional_verdict"],
            "breach_count": constraint_report["breach_count"],
            "breaches": constraint_report["breaches"],
        },
        "turnover_summary": turnover_report,
        "volatility_targeting_summary": {
            "target_volatility": vol_report["target_volatility"],
            "estimated_volatility": vol_report["estimated_volatility"],
            "risk_scale": vol_report["risk_scale"],
            "cash_weight": vol_report["cash_weight"],
            "institutional_verdict": vol_report["institutional_verdict"],
        },
        "institutional_decision": {
            "answer": "Given current conditions, the portfolio should use the selected optimizer, pass constraints, control turnover, and scale to the volatility target.",
            "final_verdict": (
                "APPROVED_WITH_RISK_REDUCTION"
                if vol_report["institutional_verdict"] == "DE_RISKED"
                else "APPROVED"
            ),
        },
    }

    return {
        "report": report,
        "allocation_df": allocation_df,
        "trade_df": trade_df,
    }


def save_outputs(payload: Dict) -> None:
    report = payload["report"]
    allocation_df = payload["allocation_df"]
    trade_df = payload["trade_df"]

    allocation_path = RESULTS_DIR / "allocation_recommendation.csv"
    report_path = RESULTS_DIR / "optimizer_report.json"
    trades_path = RESULTS_DIR / "allocation_rebalance_trades.csv"

    allocation_df.to_csv(allocation_path, index=False)
    trade_df.to_csv(trades_path, index=False)

    report_path.write_text(
        json.dumps(report, indent=4),
        encoding="utf-8",
    )

    print(f"Saved allocation recommendation: {allocation_path}")
    print(f"Saved optimizer report: {report_path}")
    print(f"Saved rebalance trades: {trades_path}")


def run_engine() -> Dict:
    payload = generate_allocation_recommendation()
    save_outputs(payload)

    report = payload["report"]
    allocation_df = payload["allocation_df"]

    print("\nAURUM ALLOCATION RECOMMENDATION ENGINE")
    print("=" * 80)

    print(f"Selected Optimizer: {report['selected_optimizer']}")
    print(f"Regime:             {report['market_conditions']['regime']}")
    print(f"Confidence:         {report['market_conditions']['forecast_confidence']:.2f}")
    print(f"Crisis Probability: {report['market_conditions']['crisis_probability']:.2f}")
    print(f"Final Verdict:      {report['institutional_decision']['final_verdict']}")

    print("\nSELECTION REASON")
    print("-" * 80)
    print(report["selection_reason"])

    print("\nFINAL ALLOCATION")
    print("-" * 80)
    for _, row in allocation_df.iterrows():
        print(f"{row['asset']:<10} {row['recommended_weight']:>8.2%}")

    print("\nRISK CONTROLS")
    print("-" * 80)
    print(f"Constraint Verdict: {report['constraint_summary']['institutional_verdict']}")
    print(f"Constraint Breaches:{report['constraint_summary']['breach_count']}")
    print(f"Turnover:           {report['turnover_summary']['turnover']:.2%}")
    print(f"Turnover Verdict:   {report['turnover_summary']['institutional_verdict']}")
    print(f"Risk Scale:         {report['volatility_targeting_summary']['risk_scale']:.4f}")
    print(f"Cash Weight:        {report['volatility_targeting_summary']['cash_weight']:.2%}")

    return payload


if __name__ == "__main__":
    run_engine()