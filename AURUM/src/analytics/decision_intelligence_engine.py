from __future__ import annotations


def classify_level(value: float, low: float, high: float) -> str:
    if value >= high:
        return "high"
    if value >= low:
        return "medium"
    return "low"


def build_decision_snapshot(
    regime: dict,
    monte_carlo: list[dict],
    pipeline_summary: dict,
    portfolio_health: str,
) -> dict:
    regime_label = regime.get("regime", "unknown")
    volatility = float(regime.get("rolling_volatility", 0))
    vix_level = float(regime.get("vix_level", 0))

    mc = {row.get("metric"): row.get("value") for row in monte_carlo}
    probability_loss = float(mc.get("probability_loss", 0))
    p05_return = float(mc.get("p05_terminal_return", 0))

    failed_steps = int(pipeline_summary.get("failed_steps", 0))

    risk_level = classify_level(
        probability_loss,
        low=0.15,
        high=0.30,
    )

    instability_level = classify_level(
        vix_level,
        low=0.10,
        high=0.20,
    )

    alerts = []

    if failed_steps > 0:
        alerts.append("Historical pipeline failures exist. Review failure telemetry.")

    if probability_loss >= 0.15:
        alerts.append("Monte Carlo loss probability is elevated.")

    if p05_return < -0.05:
        alerts.append("Lower-tail simulated return is meaningfully negative.")

    if regime_label in ["crisis", "high_volatility"]:
        alerts.append("Market regime indicates elevated instability.")

    if not alerts:
        alerts.append("No critical alerts detected.")

    if risk_level == "high" or regime_label in ["crisis", "high_volatility"]:
        posture = "Defensive"
        recommendation = "Reduce aggressive exposure, monitor downside risk, and prioritize capital preservation."
    elif risk_level == "medium":
        posture = "Balanced"
        recommendation = "Maintain diversified exposure while monitoring regime transition risk."
    else:
        posture = "Constructive"
        recommendation = "Current risk signals appear manageable; maintain allocation discipline."

    return {
        "regime": regime_label,
        "risk_level": risk_level,
        "instability_level": instability_level,
        "probability_loss": probability_loss,
        "p05_terminal_return": p05_return,
        "pipeline_failed_steps": failed_steps,
        "portfolio_posture": posture,
        "recommendation": recommendation,
        "alerts": alerts,
        "health_excerpt": portfolio_health[:500],
    }
