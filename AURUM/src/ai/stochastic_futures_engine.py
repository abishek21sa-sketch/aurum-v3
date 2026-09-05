from collections import defaultdict

from src.ai.execution_friction_engine import (
    estimate_execution_friction,
    classify_execution_environment,
)

from src.ai.realtime_adaptation_engine import (
    determine_adaptive_response,
)

from src.ai.autonomous_regime_reconfiguration_engine import (
    build_regime_configuration,
)


STOCHASTIC_PATHS = [
    {
        "path_name": "baseline_path",
        "probability": 0.46,
        "market_regime": "normal",
        "market_volatility": 0.038,
        "next_regime_probability": 69,
        "risk_signal": "neutral",
    },

    {
        "path_name": "stress_path",
        "probability": 0.28,
        "market_regime": "stress",
        "market_volatility": 0.061,
        "next_regime_probability": 52,
        "risk_signal": "risk_off",
    },

    {
        "path_name": "crisis_cascade",
        "probability": 0.18,
        "market_regime": "shock",
        "market_volatility": 0.094,
        "next_regime_probability": 34,
        "risk_signal": "risk_off",
    },

    {
        "path_name": "liquidity_freeze",
        "probability": 0.08,
        "market_regime": "shock",
        "market_volatility": 0.135,
        "next_regime_probability": 21,
        "risk_signal": "panic",
    },
]


def simulate_path(path: dict):
    friction = estimate_execution_friction(
        transition_size_pct=-5,
        market_volatility=path["market_volatility"],
    )

    execution_environment = classify_execution_environment(
        friction["execution_risk_score"]
    )

    adaptation = determine_adaptive_response(
        market_volatility=path["market_volatility"],
        execution_environment=execution_environment,
        next_regime_probability=path["next_regime_probability"],
    )

    configuration = build_regime_configuration(
        market_regime=path["market_regime"],
        risk_signal=path["risk_signal"],
        execution_environment=execution_environment,
        next_regime_probability=path["next_regime_probability"],
    )

    return {
        "execution_environment": execution_environment,
        "adaptation": adaptation,
        "configuration": configuration,
        "friction": friction,
    }


def aggregate_systemic_risks():
    risks = {
        "governance_escalation_probability": 0,
        "execution_pause_probability": 0,
        "hedge_acceleration_probability": 0,
        "crisis_cascade_probability": 0,
    }

    for path in STOCHASTIC_PATHS:
        result = simulate_path(path)

        prob = path["probability"]

        if path["market_regime"] in ["stress", "shock"]:
            risks[
                "governance_escalation_probability"
            ] += prob

        if result["adaptation"]["execution_pause"]:
            risks[
                "execution_pause_probability"
            ] += prob

        if result["adaptation"]["hedge_acceleration"]:
            risks[
                "hedge_acceleration_probability"
            ] += prob

        if path["path_name"] == "crisis_cascade":
            risks[
                "crisis_cascade_probability"
            ] += prob

    return risks


def build_stochastic_futures_report():
    systemic_risks = aggregate_systemic_risks()

    lines = []

    lines.append("=" * 90)
    lines.append("AURUM STOCHASTIC FUTURES ENGINE")
    lines.append("=" * 90)

    for path in STOCHASTIC_PATHS:
        result = simulate_path(path)

        lines.append("")
        lines.append("=" * 70)

        lines.append(
            f"STOCHASTIC FUTURE: "
            f"{path['path_name'].upper()}"
        )

        lines.append("=" * 70)

        lines.append(
            f"Probability: "
            f"{path['probability']:.2%}"
        )

        lines.append(
            f"Projected Regime: "
            f"{path['market_regime'].upper()}"
        )

        lines.append(
            f"Projected Volatility: "
            f"{path['market_volatility']:.4f}"
        )

        lines.append(
            f"Execution Environment: "
            f"{result['execution_environment'].upper()}"
        )

        lines.append(
            f"Transition Speed: "
            f"{result['adaptation']['transition_speed']}"
        )

        lines.append(
            f"Execution Pause: "
            f"{result['adaptation']['execution_pause']}"
        )

        lines.append(
            f"Hedge Acceleration: "
            f"{result['adaptation']['hedge_acceleration']}"
        )

        lines.append("")
        lines.append("CONFIGURATION STATE")
        lines.append("-" * 50)

        for key, value in result[
            "configuration"
        ].items():
            lines.append(
                f"{key}: {value}"
            )

    lines.append("")
    lines.append("SYSTEMIC FUTURES RISK SUMMARY")
    lines.append("-" * 70)

    for key, value in systemic_risks.items():
        lines.append(
            f"{key}: {value:.2%}"
        )

    lines.append("")
    lines.append("STOCHASTIC INTERPRETATION")
    lines.append("-" * 70)

    lines.append(
        "The stochastic futures engine models multiple "
        "probabilistic institutional trajectories rather "
        "than relying on a single deterministic forecast."
    )

    lines.append(
        "This allows AURUM to anticipate governance stress, "
        "execution deterioration, and defensive adaptation "
        "under multiple future market environments."
    )

    return "\n".join(lines)


if __name__ == "__main__":
    print(
        build_stochastic_futures_report()
    )