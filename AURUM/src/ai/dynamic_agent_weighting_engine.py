from src.ai.live_market_context_engine import build_live_market_context

from src.ai.historical_agent_performance_engine import (
    load_agent_history,
)

BASE_AGENT_WEIGHTS = {
    "decision": 0.20,
    "scenario": 0.25,
    "risk": 0.25,
    "committee": 0.20,
    "confidence": 0.10,
}


def normalize_weights(weights: dict):
    total = sum(weights.values())

    if total == 0:
        return weights

    return {
        agent: weight / total
        for agent, weight in weights.items()
    }

def apply_historical_reliability_adjustment(weights: dict):
    history = load_agent_history()

    adjusted = {}

    for agent, weight in weights.items():
        stats = history.get(agent, {})
        historical_score = stats.get("historical_score", 0.50)

        reliability_multiplier = 0.75 + historical_score

        adjusted[agent] = weight * reliability_multiplier

    return normalize_weights(adjusted)

def compute_dynamic_agent_weights(selected_agents: list[str]):
    context = build_live_market_context()

    weights = {
        agent: BASE_AGENT_WEIGHTS.get(agent, 0.10)
        for agent in selected_agents
    }

    market_volatility = context.get("market_volatility")

    try:
        market_volatility = float(market_volatility)
    except Exception:
        market_volatility = None

    risk_regime = str(context.get("active_risk_regime") or "").lower()
    confidence_level = str(context.get("active_confidence_level") or "").lower()
    risk_signal = str(context.get("risk_signal") or "").lower()

    if market_volatility is not None and market_volatility >= 0.03:
        if "risk" in weights:
            weights["risk"] += 0.15
        if "scenario" in weights:
            weights["scenario"] += 0.15

    if "stress" in risk_regime:
        if "risk" in weights:
            weights["risk"] += 0.15
        if "scenario" in weights:
            weights["scenario"] += 0.10

    if "low" in confidence_level or "moderate" in confidence_level:
        if "confidence" in weights:
            weights["confidence"] += 0.20
        if "committee" in weights:
            weights["committee"] += 0.10

    if risk_signal in {"defensive", "risk_off"}:
        if "risk" in weights:
            weights["risk"] += 0.10
        if "scenario" in weights:
            weights["scenario"] += 0.10

    weights = normalize_weights(weights)
    weights = apply_historical_reliability_adjustment(weights)

    return weights


def build_agent_weighting_report(selected_agents: list[str]):
    weights = compute_dynamic_agent_weights(selected_agents)

    lines = []

    lines.append("=" * 90)
    lines.append("AURUM DYNAMIC AGENT WEIGHTING ENGINE")
    lines.append("=" * 90)

    lines.append("")
    lines.append("SELECTED AGENT WEIGHTS")
    lines.append("-" * 70)

    for agent, weight in sorted(
        weights.items(),
        key=lambda x: x[1],
        reverse=True,
    ):
        lines.append(f"{agent.upper():15s} -> {weight:.2f}")

    lines.append("")
    lines.append("WEIGHTING INTERPRETATION")
    lines.append("-" * 70)

    top_agent = max(weights, key=weights.get)

    lines.append(
        f"Primary reasoning influence is assigned to "
        f"{top_agent.upper()} based on current live context."
    )

    return "\n".join(lines)


if __name__ == "__main__":
    test_agent_sets = [
        ["decision"],
        ["risk", "decision"],
        ["risk", "scenario", "decision"],
        ["committee", "risk"],
        ["confidence", "scenario"],
    ]

    for agents in test_agent_sets:
        print("")
        print(build_agent_weighting_report(agents))