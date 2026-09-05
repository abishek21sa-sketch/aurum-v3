from copy import deepcopy

from src.ai.live_market_context_engine import (
    build_live_market_context,
)

from src.ai.autonomous_regime_reconfiguration_engine import (
    build_regime_configuration,
)

from src.ai.execution_friction_engine import (
    estimate_execution_friction,
    classify_execution_environment,
)

from src.ai.realtime_adaptation_engine import (
    determine_adaptive_response,
)


SIMULATION_PATH = [
    {
        "day": 1,
        "market_volatility": 0.032,
        "next_regime_probability": 67,
        "market_regime": "normal",
        "risk_signal": "neutral",
    },

    {
        "day": 2,
        "market_volatility": 0.041,
        "next_regime_probability": 61,
        "market_regime": "normal",
        "risk_signal": "risk_off",
    },

    {
        "day": 3,
        "market_volatility": 0.055,
        "next_regime_probability": 54,
        "market_regime": "stress",
        "risk_signal": "risk_off",
    },

    {
        "day": 4,
        "market_volatility": 0.071,
        "next_regime_probability": 47,
        "market_regime": "stress",
        "risk_signal": "risk_off",
    },

    {
        "day": 5,
        "market_volatility": 0.089,
        "next_regime_probability": 39,
        "market_regime": "shock",
        "risk_signal": "risk_off",
    },
]


def simulate_future_state(state: dict):
    transition_size = -5

    friction = estimate_execution_friction(
        transition_size_pct=transition_size,
        market_volatility=state["market_volatility"],
    )

    execution_environment = classify_execution_environment(
        friction["execution_risk_score"]
    )

    adaptation = determine_adaptive_response(
        market_volatility=state["market_volatility"],
        execution_environment=execution_environment,
        next_regime_probability=state["next_regime_probability"],
    )

    config = build_regime_configuration(
        market_regime=state["market_regime"],
        risk_signal=state["risk_signal"],
        execution_environment=execution_environment,
        next_regime_probability=state["next_regime_probability"],
    )

    return {
        "execution_environment": execution_environment,
        "adaptation": adaptation,
        "configuration": config,
        "friction": friction,
    }


def build_digital_twin_report():
    current_context = build_live_market_context()

    lines = []

    lines.append("=" * 90)
    lines.append("AURUM INSTITUTIONAL DIGITAL TWIN ENGINE")
    lines.append("=" * 90)

    lines.append("")
    lines.append("CURRENT INSTITUTIONAL BASELINE")
    lines.append("-" * 70)

    lines.append(
        f"Current Regime: "
        f"{current_context.get('market_regime')}"
    )

    lines.append(
        f"Current Volatility: "
        f"{float(current_context.get('market_volatility')):.4f}"
    )

    lines.append(
        f"Next Regime Probability: "
        f"{float(current_context.get('next_regime_probability')):.2f}%"
    )

    for step in SIMULATION_PATH:
        future_state = simulate_future_state(
            deepcopy(step)
        )

        lines.append("")
        lines.append("=" * 70)

        lines.append(
            f"PROJECTED INSTITUTIONAL STATE "
            f"(DAY {step['day']})"
        )

        lines.append("=" * 70)

        lines.append(
            f"Projected Regime: "
            f"{step['market_regime'].upper()}"
        )

        lines.append(
            f"Projected Volatility: "
            f"{step['market_volatility']:.4f}"
        )

        lines.append(
            f"Projected Regime Probability: "
            f"{step['next_regime_probability']:.2f}%"
        )

        lines.append("")
        lines.append("EXECUTION STATE")
        lines.append("-" * 50)

        lines.append(
            f"Execution Environment: "
            f"{future_state['execution_environment'].upper()}"
        )

        lines.append(
            f"Execution Risk Score: "
            f"{future_state['friction']['execution_risk_score']:.4f}"
        )

        lines.append("")
        lines.append("ADAPTIVE RESPONSE")
        lines.append("-" * 50)

        lines.append(
            f"Transition Speed: "
            f"{future_state['adaptation']['transition_speed']}"
        )

        lines.append(
            f"Execution Pause: "
            f"{future_state['adaptation']['execution_pause']}"
        )

        lines.append(
            f"Hedge Acceleration: "
            f"{future_state['adaptation']['hedge_acceleration']}"
        )

        lines.append("")
        lines.append("AUTONOMOUS CONFIGURATION")
        lines.append("-" * 50)

        for key, value in future_state[
            "configuration"
        ].items():
            lines.append(
                f"{key}: {value}"
            )

    lines.append("")
    lines.append("DIGITAL TWIN INTERPRETATION")
    lines.append("-" * 70)

    lines.append(
        "The institutional digital twin simulates future "
        "governance, execution, and adaptation states under "
        "progressively deteriorating market conditions."
    )

    lines.append(
        "This allows AURUM to anticipate institutional stress "
        "responses before execution conditions fully deteriorate."
    )

    return "\n".join(lines)


if __name__ == "__main__":
    print(
        build_digital_twin_report()
    )