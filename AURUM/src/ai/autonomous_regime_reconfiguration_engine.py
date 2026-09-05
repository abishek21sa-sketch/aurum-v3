from src.ai.live_market_context_engine import (
    build_live_market_context,
)

from src.ai.execution_friction_engine import (
    estimate_execution_friction,
    classify_execution_environment,
)

from src.ai.realtime_adaptation_engine import (
    determine_adaptive_response,
)


def build_regime_configuration(
    market_regime: str,
    risk_signal: str,
    execution_environment: str,
    next_regime_probability: float,
):
    config = {
        "governance_strictness": "normal",
        "transition_aggressiveness": "moderate",
        "execution_tolerance": "normal",
        "hedge_policy": "balanced",
        "agent_weighting_bias": "balanced",
    }

    if market_regime == "stress":
        config["governance_strictness"] = "high"
        config["transition_aggressiveness"] = "defensive"
        config["execution_tolerance"] = "tight"
        config["hedge_policy"] = "elevated"
        config["agent_weighting_bias"] = "risk"

    if market_regime == "shock":
        config["governance_strictness"] = "maximum"
        config["transition_aggressiveness"] = "minimal"
        config["execution_tolerance"] = "restricted"
        config["hedge_policy"] = "maximum defense"
        config["agent_weighting_bias"] = "scenario-risk"

    if (
        market_regime == "normal"
        and risk_signal == "risk_on"
        and next_regime_probability > 75
    ):
        config["transition_aggressiveness"] = "accelerated"
        config["execution_tolerance"] = "flexible"

    if execution_environment == "fragile":
        config["execution_tolerance"] = "tight"

    return config


def build_autonomous_reconfiguration_report():
    context = build_live_market_context()

    market_regime = str(
        context.get("market_regime") or ""
    ).lower()

    risk_signal = str(
        context.get("risk_signal") or ""
    ).lower()

    market_volatility = float(
        context.get("market_volatility") or 0
    )

    next_regime_probability = float(
        context.get("next_regime_probability") or 0
    )

    friction = estimate_execution_friction(
        transition_size_pct=-5,
        market_volatility=market_volatility,
    )

    execution_environment = classify_execution_environment(
        friction["execution_risk_score"]
    )

    adaptation = determine_adaptive_response(
        market_volatility=market_volatility,
        execution_environment=execution_environment,
        next_regime_probability=next_regime_probability,
    )

    config = build_regime_configuration(
        market_regime=market_regime,
        risk_signal=risk_signal,
        execution_environment=execution_environment,
        next_regime_probability=next_regime_probability,
    )

    lines = []

    lines.append("=" * 90)
    lines.append("AURUM AUTONOMOUS REGIME RECONFIGURATION ENGINE")
    lines.append("=" * 90)

    lines.append("")
    lines.append("LIVE REGIME INPUTS")
    lines.append("-" * 70)

    lines.append(f"Market Regime: {market_regime}")
    lines.append(f"Risk Signal: {risk_signal}")
    lines.append(
        f"Execution Environment: {execution_environment.upper()}"
    )
    lines.append(
        f"Next Regime Probability: "
        f"{next_regime_probability:.2f}%"
    )

    lines.append("")
    lines.append("AUTONOMOUS CONFIGURATION")
    lines.append("-" * 70)

    for key, value in config.items():
        lines.append(
            f"{key}: {value}"
        )

    lines.append("")
    lines.append("REAL-TIME EXECUTION RESPONSE")
    lines.append("-" * 70)

    lines.append(
        f"Transition Speed: "
        f"{adaptation['transition_speed']}"
    )

    lines.append(
        f"Execution Pause: "
        f"{adaptation['execution_pause']}"
    )

    lines.append(
        f"Hedge Acceleration: "
        f"{adaptation['hedge_acceleration']}"
    )

    lines.append("")
    lines.append("RECONFIGURATION INTERPRETATION")
    lines.append("-" * 70)

    if market_regime == "normal":
        lines.append(
            "The system remains in standard institutional "
            "operating configuration."
        )

    elif market_regime == "stress":
        lines.append(
            "Governance strictness and defensive posture "
            "have been elevated automatically."
        )

    else:
        lines.append(
            "Shock-state governance protections activated. "
            "Execution tolerance significantly reduced."
        )

    return "\n".join(lines)


if __name__ == "__main__":
    print(
        build_autonomous_reconfiguration_report()
    )