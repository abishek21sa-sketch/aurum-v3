from collections import OrderedDict

from src.ai.live_market_context_engine import (
    build_live_market_context,
)

from src.ai.stochastic_futures_engine import (
    aggregate_systemic_risks,
)


ADVERSARIAL_AGENTS = OrderedDict({
    "cio": {
        "priority": "balanced_growth",
    },

    "risk_committee": {
        "priority": "capital_preservation",
    },

    "execution_desk": {
        "priority": "liquidity_stability",
    },

    "macro_strategist": {
        "priority": "regime_positioning",
    },

    "volatility_desk": {
        "priority": "tail_hedging",
    },
})


def build_agent_argument(
    agent_name: str,
    systemic_risks: dict,
):
    governance_risk = systemic_risks[
        "governance_escalation_probability"
    ]

    hedge_risk = systemic_risks[
        "hedge_acceleration_probability"
    ]

    crisis_risk = systemic_risks[
        "crisis_cascade_probability"
    ]

    if agent_name == "cio":
        return (
            "Reduce portfolio beta gradually while "
            "avoiding unnecessary over-hedging."
        )

    if agent_name == "risk_committee":
        if governance_risk > 0.50:
            return (
                "Governance escalation risk is elevated. "
                "Transition pacing should be tightened."
            )

        return (
            "Maintain defensive institutional posture."
        )

    if agent_name == "execution_desk":
        if crisis_risk > 0.15:
            return (
                "Liquidity conditions may deteriorate. "
                "Execution sizing should remain controlled."
            )

        return (
            "Execution conditions remain orderly."
        )

    if agent_name == "macro_strategist":
        if governance_risk > 0.50:
            return (
                "Stress regime probability is rising. "
                "Defensive positioning should increase."
            )

        return (
            "Macro conditions remain broadly stable."
        )

    if agent_name == "volatility_desk":
        if hedge_risk > 0.50:
            return (
                "Tail-risk hedging should be increased "
                "under rising stress probabilities."
            )

        return (
            "Current volatility structure remains manageable."
        )

    return "No active institutional view."


def evaluate_conflict_level(arguments: dict):
    disagreement_score = 0

    disagreement_keywords = [
        "tightened",
        "deteriorate",
        "increase",
        "hedging",
    ]

    for text in arguments.values():
        for keyword in disagreement_keywords:
            if keyword in text.lower():
                disagreement_score += 1

    if disagreement_score <= 2:
        return "LOW"

    if disagreement_score <= 5:
        return "MODERATE"

    return "HIGH"


def build_adversarial_simulation_report():
    context = build_live_market_context()

    systemic_risks = aggregate_systemic_risks()

    arguments = {}

    for agent_name in ADVERSARIAL_AGENTS:
        arguments[agent_name] = (
            build_agent_argument(
                agent_name,
                systemic_risks,
            )
        )

    conflict_level = evaluate_conflict_level(
        arguments
    )

    lines = []

    lines.append("=" * 90)
    lines.append(
        "AURUM ADVERSARIAL MARKET SIMULATION ENGINE"
    )
    lines.append("=" * 90)

    lines.append("")
    lines.append("LIVE INSTITUTIONAL CONTEXT")
    lines.append("-" * 70)

    lines.append(
        f"Market Regime: "
        f"{context.get('market_regime')}"
    )

    lines.append(
        f"Market Volatility: "
        f"{float(context.get('market_volatility')):.4f}"
    )

    lines.append(
        f"Governance Escalation Probability: "
        f"{systemic_risks['governance_escalation_probability']:.2%}"
    )

    lines.append(
        f"Crisis Cascade Probability: "
        f"{systemic_risks['crisis_cascade_probability']:.2%}"
    )

    lines.append("")
    lines.append("ADVERSARIAL INSTITUTIONAL DEBATE")
    lines.append("-" * 70)

    for agent_name, argument in arguments.items():
        lines.append("")
        lines.append(
            f"{agent_name.upper()}"
        )

        lines.append(
            f"Priority: "
            f"{ADVERSARIAL_AGENTS[agent_name]['priority']}"
        )

        lines.append(
            f"Position: {argument}"
        )

    lines.append("")
    lines.append("INSTITUTIONAL DISAGREEMENT ANALYSIS")
    lines.append("-" * 70)

    lines.append(
        f"Conflict Level: {conflict_level}"
    )

    if conflict_level == "LOW":
        lines.append(
            "Institutional alignment remains relatively stable."
        )

    elif conflict_level == "MODERATE":
        lines.append(
            "Institutional disagreement is increasing "
            "across governance and execution layers."
        )

    else:
        lines.append(
            "Severe institutional disagreement detected. "
            "Escalated governance intervention may be required."
        )

    lines.append("")
    lines.append("ADVERSARIAL INTERPRETATION")
    lines.append("-" * 70)

    lines.append(
        "The adversarial simulation engine models "
        "institutional conflict dynamics across "
        "multiple portfolio governance participants."
    )

    lines.append(
        "This allows AURUM to stress-test decision "
        "coherence under competing institutional objectives."
    )

    return "\n".join(lines)


if __name__ == "__main__":
    print(
        build_adversarial_simulation_report()
    )