from src.ai.policy_constraint_engine import (
    evaluate_policy_constraints,
)

from src.ai.cio_oversight_engine import (
    evaluate_governance_conditions,
)

from src.ai.live_market_context_engine import (
    build_live_market_context,
)


def generate_execution_actions(
    synthesis_text: str,
    meta_reasoning_text: str,
):
    governance = evaluate_governance_conditions(
        synthesis_text,
        meta_reasoning_text,
    )

    policy = evaluate_policy_constraints()

    context = build_live_market_context()

    actions = []

    if governance["override_recommended"]:
        return {
            "approved": False,
            "reason":
                "CIO override active due to insufficient confidence.",
            "actions": [],
        }

    if not policy["policy_pass"]:
        return {
            "approved": False,
            "reason":
                "Institutional policy constraints violated.",
            "actions": [],
        }

    growth_weight = float(
        context.get("growth_risk_weight") or 0
    )

    hedge_weight = float(
        context.get("defensive_hedge_weight") or 0
    )

    market_regime = str(
        context.get("market_regime") or ""
    ).lower()

    risk_signal = str(
        context.get("risk_signal") or ""
    ).lower()

    if "concentration risk" in synthesis_text.lower():
        actions.append(
            "Reduce SPY concentration exposure by 2-3%."
        )

    if "downside scenario vulnerability" in synthesis_text.lower():
        actions.append(
            "Increase GLD/VIX hedge allocation modestly."
        )

    if growth_weight > 68:
        actions.append(
            "Trim broad equity beta exposure slightly."
        )

    if hedge_weight < 25:
        actions.append(
            "Review defensive hedge sufficiency."
        )

    if market_regime == "normal" and risk_signal == "neutral":
        actions.append(
            "Maintain regime-aware allocation discipline."
        )

    return {
        "approved": True,
        "reason":
            "Execution actions approved under current "
            "governance and policy conditions.",
        "actions": actions,
    }


def build_execution_action_report(
    query: str,
    synthesis_text: str,
    meta_reasoning_text: str,
):
    result = generate_execution_actions(
        synthesis_text,
        meta_reasoning_text,
    )

    lines = []

    lines.append("=" * 90)
    lines.append("AURUM EXECUTION ACTION ENGINE")
    lines.append("=" * 90)

    lines.append("")
    lines.append(f"Original Query: {query}")

    lines.append("")
    lines.append("EXECUTION GOVERNANCE STATUS")
    lines.append("-" * 70)

    status = "APPROVED" if result["approved"] else "REJECTED"

    lines.append(f"Execution Status: {status}")
    lines.append(f"Reason: {result['reason']}")

    lines.append("")
    lines.append("PROPOSED INSTITUTIONAL ACTIONS")
    lines.append("-" * 70)

    if result["actions"]:
        for idx, action in enumerate(
            result["actions"],
            start=1,
        ):
            lines.append(f"{idx}. {action}")
    else:
        lines.append(
            "No autonomous execution actions approved."
        )

    lines.append("")
    lines.append("EXECUTION INTERPRETATION")
    lines.append("-" * 70)

    if result["approved"]:
        lines.append(
            "The execution layer believes the current "
            "institutional state supports limited governed "
            "portfolio adjustments."
        )
    else:
        lines.append(
            "The execution layer has blocked autonomous "
            "portfolio actions pending governance review."
        )

    return "\n".join(lines)