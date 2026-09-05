from src.ai.live_market_context_engine import build_live_market_context


POLICY_LIMITS = {
    "max_growth_risk_weight": 75.0,
    "max_defensive_hedge_weight": 45.0,
    "max_live_scenario_loss": -3.0,
    "min_next_regime_probability": 60.0,
}


def evaluate_policy_constraints():
    context = build_live_market_context()

    growth_weight = float(context.get("growth_risk_weight") or 0)
    hedge_weight = float(context.get("defensive_hedge_weight") or 0)
    next_prob = float(context.get("next_regime_probability") or 0)

    breaches = []

    if growth_weight > POLICY_LIMITS["max_growth_risk_weight"]:
        breaches.append(
            f"Growth/risk exposure {growth_weight:.2f}% exceeds limit "
            f"{POLICY_LIMITS['max_growth_risk_weight']:.2f}%."
        )

    if hedge_weight > POLICY_LIMITS["max_defensive_hedge_weight"]:
        breaches.append(
            f"Defensive/hedge exposure {hedge_weight:.2f}% exceeds limit "
            f"{POLICY_LIMITS['max_defensive_hedge_weight']:.2f}%."
        )

    if next_prob < POLICY_LIMITS["min_next_regime_probability"]:
        breaches.append(
            f"Next-regime confidence {next_prob:.2f}% is below required "
            f"{POLICY_LIMITS['min_next_regime_probability']:.2f}%."
        )

    return {
        "context": context,
        "breaches": breaches,
        "policy_pass": len(breaches) == 0,
    }


def build_policy_constraint_report():
    result = evaluate_policy_constraints()
    context = result["context"]

    lines = []

    lines.append("=" * 90)
    lines.append("AURUM POLICY CONSTRAINT ENGINE")
    lines.append("=" * 90)

    lines.append("")
    lines.append("POLICY INPUT STATE")
    lines.append("-" * 70)
    lines.append(f"Market Regime: {context.get('market_regime')}")
    lines.append(f"Risk Signal: {context.get('risk_signal')}")
    lines.append(f"Growth / Risk Weight: {context.get('growth_risk_weight')}%")
    lines.append(f"Defensive / Hedge Weight: {context.get('defensive_hedge_weight')}%")
    lines.append(f"Next Regime Probability: {context.get('next_regime_probability')}%")

    lines.append("")
    lines.append("POLICY CHECK RESULT")
    lines.append("-" * 70)

    if result["policy_pass"]:
        lines.append("PASS: No institutional policy breaches detected.")
    else:
        lines.append("FAIL: Institutional policy breaches detected.")
        for breach in result["breaches"]:
            lines.append(f"- {breach}")

    lines.append("")
    lines.append("POLICY INTERPRETATION")
    lines.append("-" * 70)

    if result["policy_pass"]:
        lines.append(
            "Current allocation posture remains within defined institutional "
            "risk policy limits."
        )
    else:
        lines.append(
            "CIO oversight should restrict autonomous allocation changes until "
            "policy breaches are reviewed."
        )

    return "\n".join(lines)


if __name__ == "__main__":
    print(build_policy_constraint_report())