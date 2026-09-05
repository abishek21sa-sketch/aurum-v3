from src.ai.live_market_context_engine import (
    build_live_market_context,
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

def estimate_execution_friction(
    transition_size_pct: float,
    market_volatility: float,
):
    slippage = (
        abs(transition_size_pct)
        * market_volatility
        * 0.15
    )

    liquidity_stress = (
        abs(transition_size_pct)
        * market_volatility
        * 0.10
    )

    execution_risk = (
        slippage + liquidity_stress
    )

    return {
        "estimated_slippage_pct": round(slippage, 4),
        "estimated_liquidity_stress_pct": round(liquidity_stress, 4),
        "execution_risk_score": round(execution_risk, 4),
    }


def classify_execution_environment(
    execution_risk_score: float,
):
    if execution_risk_score < 0.30:
        return "stable"

    if execution_risk_score < 0.75:
        return "moderate"

    return "fragile"


def build_execution_friction_report():
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

    friction = estimate_execution_friction(
        transition_size_pct=growth_delta,
        market_volatility=market_volatility,
    )

    environment = classify_execution_environment(
        friction["execution_risk_score"]
    )

    lines = []

    lines.append("=" * 90)
    lines.append("AURUM EXECUTION FRICTION ENGINE")
    lines.append("=" * 90)

    lines.append("")
    lines.append("EXECUTION INPUT STATE")
    lines.append("-" * 70)

    lines.append(
        f"Market Volatility: {market_volatility:.4f}"
    )

    lines.append(
        f"Growth Transition Size: {growth_delta:.2f}%"
    )

    lines.append("")
    lines.append("EXECUTION FRICTION ESTIMATES")
    lines.append("-" * 70)

    lines.append(
        f"Estimated Slippage: "
        f"{friction['estimated_slippage_pct']:.4f}%"
    )

    lines.append(
        f"Estimated Liquidity Stress: "
        f"{friction['estimated_liquidity_stress_pct']:.4f}%"
    )

    lines.append(
        f"Execution Risk Score: "
        f"{friction['execution_risk_score']:.4f}"
    )

    lines.append("")
    lines.append("EXECUTION ENVIRONMENT")
    lines.append("-" * 70)

    lines.append(
        f"Execution Environment: {environment.upper()}"
    )

    lines.append("")
    lines.append("EXECUTION INTERPRETATION")
    lines.append("-" * 70)

    if environment == "stable":
        lines.append(
            "Current market conditions support orderly "
            "institutional portfolio transitions."
        )

    elif environment == "moderate":
        lines.append(
            "Execution conditions remain manageable but "
            "transition pacing should be monitored carefully."
        )

    else:
        lines.append(
            "Execution conditions appear fragile. Large "
            "allocation transitions may create elevated "
            "slippage and liquidity disruption."
        )

    return "\n".join(lines)


if __name__ == "__main__":
    print(
        build_execution_friction_report()
    )