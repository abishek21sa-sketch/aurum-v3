from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


INPUT_DIR = Path("results/regime_intelligence")
OUTPUT_DIR = Path("results/regime_intelligence")

FINAL_ALLOCATION_PATH = INPUT_DIR / "final_regime_allocation.csv"
FINAL_SUMMARY_PATH = INPUT_DIR / "final_regime_allocation_summary.json"
CONFIDENCE_SUMMARY_PATH = INPUT_DIR / "confidence_exposure_summary.json"
HEDGE_OVERLAY_PATH = INPUT_DIR / "dynamic_hedge_overlay.json"
TRANSITION_DECISION_PATH = INPUT_DIR / "transition_decision.json"

OUTPUT_PATH = OUTPUT_DIR / "portfolio_intelligence_report.json"
TEXT_OUTPUT_PATH = OUTPUT_DIR / "portfolio_intelligence_report.txt"


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing required input: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_allocation() -> pd.DataFrame:
    if not FINAL_ALLOCATION_PATH.exists():
        raise FileNotFoundError(f"Missing required input: {FINAL_ALLOCATION_PATH}")
    return pd.read_csv(FINAL_ALLOCATION_PATH)


def classify_allocation_style(risk_weight: float, defensive_weight: float) -> str:
    if defensive_weight >= 0.65:
        return "defensive_capital_preservation"
    if defensive_weight >= 0.50:
        return "balanced_defensive"
    if risk_weight >= 0.70:
        return "growth_risk_on"
    return "balanced_multi_asset"


def build_recommendation_text(report: dict) -> str:
    lines = []

    lines.append("=" * 80)
    lines.append("AURUM PORTFOLIO INTELLIGENCE REPORT")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"Current Detected Regime:     {report['current_detected_regime']}")
    lines.append(f"Effective Allocation Regime: {report['effective_allocation_regime']}")
    lines.append(f"Selected Portfolio:          {report['selected_portfolio_type']}")
    lines.append(f"Allocation Style:            {report['allocation_style']}")
    lines.append(f"Combined Confidence:         {report['combined_confidence_pct']}%")
    lines.append(f"Transition Risk:             {report['transition_risk_label']} ({report['transition_risk_score']})")
    lines.append(f"Hedge Status:                {report['hedge_status']}")
    lines.append("")
    lines.append("RECOMMENDED ALLOCATION")
    lines.append("-" * 80)

    for row in report["recommended_allocation"]:
        lines.append(
            f"{row['asset']:10s} {row['final_weight_pct']:>6.2f}%"
        )

    lines.append("")
    lines.append("INSTITUTIONAL INTERPRETATION")
    lines.append("-" * 80)
    lines.append(report["institutional_interpretation"])

    return "\n".join(lines)


def build_portfolio_intelligence_report() -> tuple[dict, str]:
    allocation = load_allocation()
    final_summary = load_json(FINAL_SUMMARY_PATH)
    confidence = load_json(CONFIDENCE_SUMMARY_PATH)
    hedge = load_json(HEDGE_OVERLAY_PATH)
    transition = load_json(TRANSITION_DECISION_PATH)

    allocation = allocation.sort_values(
        "final_weight",
        ascending=False,
    )

    risk_weight = float(final_summary["final_risk_asset_weight"])
    defensive_weight = float(final_summary["final_defensive_or_cash_weight"])

    allocation_style = classify_allocation_style(
        risk_weight=risk_weight,
        defensive_weight=defensive_weight,
    )

    report = {
        "module": "portfolio_intelligence_report_generator",
        "question_answered": "Given this market regime, what portfolio should AURUM hold?",
        "previous_regime": transition["previous_regime"],
        "current_detected_regime": transition["detected_current_regime"],
        "effective_allocation_regime": transition["effective_allocation_regime"],
        "selected_portfolio_type": confidence["selected_portfolio_type"],
        "allocation_style": allocation_style,
        "transition_risk_label": transition["transition_risk_label"],
        "transition_risk_score": transition["transition_risk_score"],
        "regime_confidence_pct": round(confidence["regime_confidence"] * 100, 2),
        "forecast_confidence_pct": round(confidence["forecast_confidence"] * 100, 2),
        "signal_confidence_pct": round(confidence["signal_confidence"] * 100, 2),
        "combined_confidence_pct": round(confidence["combined_confidence"] * 100, 2),
        "exposure_multiplier": confidence["exposure_multiplier"],
        "hedge_status": hedge["hedge_status"],
        "hedge_overlay_weight_pct": round(hedge["total_overlay_weight"] * 100, 2),
        "volatility_label": hedge["volatility_label"],
        "volatility_signal": hedge["volatility_signal"],
        "crisis_probability_pct": round(hedge["crisis_probability"] * 100, 2),
        "final_risk_asset_weight_pct": round(risk_weight * 100, 2),
        "final_defensive_or_cash_weight_pct": round(defensive_weight * 100, 2),
        "recommended_allocation": allocation[
            ["asset", "final_weight", "final_weight_pct"]
        ].to_dict(orient="records"),
        "institutional_interpretation": (
            f"AURUM detected a {transition['detected_current_regime']} regime and selected "
            f"{transition['effective_allocation_regime']} as the effective allocation regime. "
            f"Transition risk is {transition['transition_risk_label']}, so the allocation does not require "
            f"aggressive staging. Combined confidence is {round(confidence['combined_confidence'] * 100, 2)}%, "
            f"resulting in an exposure multiplier of {confidence['exposure_multiplier']}. "
            f"The hedge overlay is {hedge['hedge_status']} with {round(hedge['total_overlay_weight'] * 100, 2)}% "
            f"allocated toward defensive additions. The final portfolio is therefore a "
            f"{allocation_style} allocation with {round(risk_weight * 100, 2)}% in risk assets and "
            f"{round(defensive_weight * 100, 2)}% in defensive or cash assets."
        ),
    }

    text_report = build_recommendation_text(report)

    return report, text_report


def save_outputs(report: dict, text_report: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(report, indent=4), encoding="utf-8")
    TEXT_OUTPUT_PATH.write_text(text_report, encoding="utf-8")


def main() -> None:
    report, text_report = build_portfolio_intelligence_report()
    save_outputs(report, text_report)

    print(text_report)
    print()
    print(f"Saved JSON report: {OUTPUT_PATH}")
    print(f"Saved text report: {TEXT_OUTPUT_PATH}")


if __name__ == "__main__":
    main()