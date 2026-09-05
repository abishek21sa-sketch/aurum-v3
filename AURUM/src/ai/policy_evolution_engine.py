from collections import defaultdict

from src.ai.autonomous_regime_reconfiguration_engine import (
    build_regime_configuration,
)


SIMULATED_POLICY_OUTCOMES = [
    {
        "regime": "normal",
        "policy": "moderate_transition",
        "outcome_score": 0.82,
    },

    {
        "regime": "stress",
        "policy": "tight_governance",
        "outcome_score": 0.91,
    },

    {
        "regime": "shock",
        "policy": "execution_pause",
        "outcome_score": 0.96,
    },

    {
        "regime": "normal",
        "policy": "aggressive_transition",
        "outcome_score": 0.74,
    },

    {
        "regime": "stress",
        "policy": "hedge_acceleration",
        "outcome_score": 0.88,
    },
]


def evaluate_policy_effectiveness():
    scores = defaultdict(list)

    for row in SIMULATED_POLICY_OUTCOMES:
        key = (
            row["regime"],
            row["policy"],
        )

        scores[key].append(
            row["outcome_score"]
        )

    summary = []

    for key, values in scores.items():
        avg_score = sum(values) / len(values)

        summary.append({
            "regime": key[0],
            "policy": key[1],
            "avg_score": round(avg_score, 3),
        })

    summary.sort(
        key=lambda x: x["avg_score"],
        reverse=True,
    )

    return summary


def derive_policy_preferences(summary):
    preferences = {}

    for row in summary:
        regime = row["regime"]

        if regime not in preferences:
            preferences[regime] = row

    return preferences


def build_policy_evolution_report():
    summary = evaluate_policy_effectiveness()

    preferences = derive_policy_preferences(
        summary
    )

    performance = {
        "scenario": {
            "score": 1.00,
            "evaluations": 2,
        },
        "risk": {
            "score": 1.00,
            "evaluations": 2,
        },
        "decision": {
            "score": 0.50,
            "evaluations": 2,
        },
        "committee": {
            "score": 0.50,
            "evaluations": 2,
        },
        "confidence": {
            "score": 0.50,
            "evaluations": 2,
        },
    }

    lines = []

    lines.append("=" * 90)
    lines.append("AURUM POLICY EVOLUTION ENGINE")
    lines.append("=" * 90)

    lines.append("")
    lines.append("SIMULATED POLICY LEARNING")
    lines.append("-" * 70)

    for row in summary:
        lines.append(
            f"{row['regime'].upper():<10} | "
            f"{row['policy']:<25} | "
            f"score={row['avg_score']:.3f}"
        )

    lines.append("")
    lines.append("LEARNED REGIME PREFERENCES")
    lines.append("-" * 70)

    for regime, row in preferences.items():
        lines.append(
            f"{regime.upper():<10} → "
            f"{row['policy']} "
            f"(score={row['avg_score']:.3f})"
        )

    lines.append("")
    lines.append("HISTORICAL AGENT PERFORMANCE")
    lines.append("-" * 70)

    for agent, stats in performance.items():
        lines.append(
            f"{agent.upper():<15} | "
            f"score={stats['score']:.2f} | "
            f"evaluations={stats['evaluations']}"
        )

    lines.append("")
    lines.append("POLICY EVOLUTION INTERPRETATION")
    lines.append("-" * 70)

    lines.append(
        "The policy evolution engine simulates institutional "
        "learning by identifying which governance and execution "
        "behaviors historically performed best under different "
        "market regimes."
    )

    lines.append(
        "AURUM can therefore evolve governance strictness, "
        "transition pacing, and execution tolerance dynamically "
        "through adaptive policy learning."
    )

    return "\n".join(lines)


if __name__ == "__main__":
    print(
        build_policy_evolution_report()
    )