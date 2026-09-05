from src.ai.live_market_context_engine import (
    build_live_market_context,
)

from src.ai.execution_friction_engine import (
    estimate_execution_friction,
    classify_execution_environment,
)

def build_target_state(context: dict):
    current_growth = float(
        context.get("growth_risk_weight") or 0
    )

    current_hedge = float(
        context.get("defensive_hedge_weight") or 0
    )

    target_growth = current_growth
    target_hedge = current_hedge

    if current_growth > 68:
        target_growth -= 5
        target_hedge += 5

    return {
        "current_growth_weight": current_growth,
        "target_growth_weight": round(target_growth, 2),
        "current_hedge_weight": current_hedge,
        "target_hedge_weight": round(target_hedge, 2),
    }


def determine_adaptive_response(
    market_volatility: float,
    execution_environment: str,
    next_regime_probability: float,
):
    response = {
        "transition_speed": "normal",
        "execution_pause": False,
        "hedge_acceleration": False,
        "risk_message": "",
    }

    if market_volatility > 0.05:
        response["transition_speed"] = "slow"

        response["risk_message"] = (
            "Elevated volatility detected. "
            "Transition pacing reduced."
        )

    if execution_environment == "fragile":
        response["execution_pause"] = True

        response["risk_message"] = (
            "Execution environment fragile. "
            "Portfolio migration paused."
        )

    if next_regime_probability < 55:
        response["hedge_acceleration"] = True

        response["risk_message"] = (
            "Regime confidence deteriorating. "
            "Defensive hedging accelerated."
        )

    return response


def build_realtime_adaptation_report():
    context = build_live_market_context()

    target_state = build_target_state(
        context,
    )

    growth_delta = (
        target_state["target_growth_weight"]
        - target_state["current_growth_weight"]
    )

    market_volatility = float(
        context.get("market_volatility") or 0
    )

    next_regime_probability = float(
        context.get("next_regime_probability") or 0
    )

    friction = estimate_execution_friction(
        transition_size_pct=growth_delta,
        market_volatility=market_volatility,
    )

    execution_environment = classify_execution_environment(
        friction["execution_risk_score"]
    )

    response = determine_adaptive_response(
        market_volatility=market_volatility,
        execution_environment=execution_environment,
        next_regime_probability=next_regime_probability,
    )

    lines = []

    lines.append("=" * 90)
    lines.append("AURUM REAL-TIME ADAPTATION ENGINE")
    lines.append("=" * 90)

    lines.append("")
    lines.append("LIVE ADAPTATION INPUTS")
    lines.append("-" * 70)

    lines.append(
        f"Market Volatility: {market_volatility:.4f}"
    )

    lines.append(
        f"Execution Environment: "
        f"{execution_environment.upper()}"
    )

    lines.append(
        f"Next Regime Probability: "
        f"{next_regime_probability:.2f}%"
    )

    lines.append("")
    lines.append("ADAPTIVE EXECUTION RESPONSE")
    lines.append("-" * 70)

    lines.append(
        f"Transition Speed: "
        f"{response['transition_speed'].upper()}"
    )

    lines.append(
        f"Execution Pause: "
        f"{response['execution_pause']}"
    )

    lines.append(
        f"Hedge Acceleration: "
        f"{response['hedge_acceleration']}"
    )

    lines.append("")
    lines.append("ADAPTATION INTERPRETATION")
    lines.append("-" * 70)

    if response["risk_message"]:
        lines.append(response["risk_message"])

    else:
        lines.append(
            "Current institutional conditions support "
            "stable adaptive execution behavior."
        )

    return "\n".join(lines)


if __name__ == "__main__":
    print(build_realtime_adaptation_report())