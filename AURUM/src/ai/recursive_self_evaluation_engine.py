from collections import defaultdict

from src.ai.stochastic_futures_engine import (
    aggregate_systemic_risks,
)




SIMULATED_REALIZED_OUTCOMES = [
    {
        "prediction": "governance_escalation",
        "occurred": True,
    },

    {
        "prediction": "hedge_acceleration",
        "occurred": True,
    },

    {
        "prediction": "execution_pause",
        "occurred": False,
    },

    {
        "prediction": "crisis_cascade",
        "occurred": False,
    },
]


def evaluate_prediction_accuracy():
    evaluation = []

    for row in SIMULATED_REALIZED_OUTCOMES:
        prediction = row["prediction"]
        occurred = row["occurred"]

        if occurred:
            score = 1.0
            verdict = "CORRECT"

        else:
            score = 0.0
            verdict = "INCORRECT"

        evaluation.append({
            "prediction": prediction,
            "occurred": occurred,
            "score": score,
            "verdict": verdict,
        })

    return evaluation


def recursive_governance_adjustment(
    evaluations: list,
):
    adjustments = {
        "governance_strictness_bias": 0,
        "hedge_bias": 0,
        "execution_tolerance_bias": 0,
        "scenario_agent_trust": 0,
    }

    for row in evaluations:
        prediction = row["prediction"]
        score = row["score"]

        if prediction == "governance_escalation":
            adjustments[
                "governance_strictness_bias"
            ] += score

        if prediction == "hedge_acceleration":
            adjustments[
                "hedge_bias"
            ] += score

        if prediction == "execution_pause":
            adjustments[
                "execution_tolerance_bias"
            ] -= (1 - score)

        if prediction == "crisis_cascade":
            adjustments[
                "scenario_agent_trust"
            ] -= (1 - score)

    return adjustments


def build_recursive_self_evaluation_report():
    evaluations = evaluate_prediction_accuracy()

    adjustments = recursive_governance_adjustment(
        evaluations
    )

    lines = []

    lines.append("=" * 90)
    lines.append(
        "AURUM RECURSIVE SELF-EVALUATION ENGINE"
    )
    lines.append("=" * 90)

    lines.append("")
    lines.append("PREDICTION VS REALIZED OUTCOME")
    lines.append("-" * 70)

    for row in evaluations:
        lines.append(
            f"{row['prediction']:<30} | "
            f"occurred={row['occurred']} | "
            f"verdict={row['verdict']}"
        )

    lines.append("")
    lines.append("RECURSIVE GOVERNANCE ADJUSTMENTS")
    lines.append("-" * 70)

    for key, value in adjustments.items():
        lines.append(
            f"{key}: {value:.2f}"
        )

    lines.append("")
    lines.append("SELF-EVALUATION INTERPRETATION")
    lines.append("-" * 70)

    lines.append(
        "The recursive evaluation engine compares "
        "institutional forecasts against realized "
        "future outcomes."
    )

    lines.append(
        "AURUM can therefore recalibrate governance "
        "strictness, hedge behavior, execution "
        "tolerance, and agent trust dynamically "
        "through recursive institutional learning."
    )

    return "\n".join(lines)


if __name__ == "__main__":
    print(
        build_recursive_self_evaluation_report()
    )