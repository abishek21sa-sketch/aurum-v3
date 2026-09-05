from src.ai.historical_agent_performance_engine import (
    update_agent_performance,
    build_agent_performance_report,
)


def classify_realized_outcome(
    predicted_state: dict,
    realized_state: dict,
):
    predicted_risk = str(
        predicted_state.get("dominant_risk") or ""
    ).lower()

    realized_event = str(
        realized_state.get("realized_event") or ""
    ).lower()

    realized_regime = str(
        realized_state.get("realized_regime") or ""
    ).lower()

    realized_drawdown = float(
        realized_state.get("realized_drawdown_pct", 0.0)
    )

    outcome = {
        "scenario_success": False,
        "risk_success": False,
        "decision_success": False,
        "confidence_success": False,
        "committee_success": False,
    }

    if "equity_gap_down" in predicted_risk and (
        "equity" in realized_event
        or realized_drawdown <= -2.0
    ):
        outcome["scenario_success"] = True
        outcome["risk_success"] = True

    if realized_drawdown > -3.0:
        outcome["decision_success"] = True
        outcome["committee_success"] = True

    if "normal" in realized_regime and realized_drawdown > -2.0:
        outcome["confidence_success"] = True

    if realized_drawdown <= -3.0:
        outcome["confidence_success"] = False
        outcome["decision_success"] = False

    return outcome


def apply_feedback_to_agents(outcome: dict):
    agent_map = {
        "scenario": outcome["scenario_success"],
        "risk": outcome["risk_success"],
        "decision": outcome["decision_success"],
        "confidence": outcome["confidence_success"],
        "committee": outcome["committee_success"],
    }

    for agent, success in agent_map.items():
        update_agent_performance(
            agent=agent,
            successful=success,
        )

    return agent_map


def build_feedback_learning_report(
    predicted_state: dict,
    realized_state: dict,
):
    outcome = classify_realized_outcome(
        predicted_state,
        realized_state,
    )

    agent_updates = apply_feedback_to_agents(
        outcome,
    )

    lines = []

    lines.append("=" * 90)
    lines.append("AURUM AUTONOMOUS FEEDBACK LEARNING ENGINE")
    lines.append("=" * 90)

    lines.append("")
    lines.append("PREDICTED STATE")
    lines.append("-" * 70)

    for key, value in predicted_state.items():
        lines.append(f"{key}: {value}")

    lines.append("")
    lines.append("REALIZED STATE")
    lines.append("-" * 70)

    for key, value in realized_state.items():
        lines.append(f"{key}: {value}")

    lines.append("")
    lines.append("AGENT FEEDBACK UPDATES")
    lines.append("-" * 70)

    for agent, success in agent_updates.items():
        status = "REWARDED" if success else "PENALIZED"
        lines.append(f"{agent.upper():15s} -> {status}")

    lines.append("")
    lines.append(build_agent_performance_report())

    return "\n".join(lines)


if __name__ == "__main__":
    predicted_state = {
        "dominant_risk": "equity_gap_down",
        "portfolio_stance": "defensive regime-aware allocation",
        "confidence_level": "LOW-MODERATE CONFIDENCE",
    }

    realized_state = {
        "realized_event": "equity drawdown",
        "realized_regime": "stress",
        "realized_drawdown_pct": -2.6,
    }

    print(
        build_feedback_learning_report(
            predicted_state=predicted_state,
            realized_state=realized_state,
        )
    )