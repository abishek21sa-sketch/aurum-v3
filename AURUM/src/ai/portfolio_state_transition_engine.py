from src.ai.live_market_context_engine import (
    build_live_market_context,
)

from src.ai.execution_action_engine import (
    generate_execution_actions,
)

from src.ai.execution_friction_engine import (
    build_execution_friction_report,
)

from src.ai.realtime_adaptation_engine import (
    build_realtime_adaptation_report,
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


def build_transition_plan(
    current_weight: float,
    target_weight: float,
):
    delta = round(
        target_weight - current_weight,
        2,
    )

    if delta == 0:
        return []

    steps = []

    daily_step = round(delta / 3, 2)

    running = current_weight

    for day in range(1, 4):
        running += daily_step

        steps.append({
            "day": day,
            "projected_weight": round(running, 2),
            "step_change": daily_step,
        })

    return steps


def build_portfolio_transition_report(
    query: str,
    synthesis_text: str,
    meta_reasoning_text: str,
):
    context = build_live_market_context()

    execution = generate_execution_actions(
        synthesis_text,
        meta_reasoning_text,
    )

    target_state = build_target_state(
        context,
    )

    growth_transition = build_transition_plan(
        target_state["current_growth_weight"],
        target_state["target_growth_weight"],
    )

    hedge_transition = build_transition_plan(
        target_state["current_hedge_weight"],
        target_state["target_hedge_weight"],
    )

    lines = []

    lines.append("=" * 90)
    lines.append("AURUM PORTFOLIO STATE TRANSITION ENGINE")
    lines.append("=" * 90)

    lines.append("")
    lines.append(f"Original Query: {query}")

    lines.append("")
    lines.append("CURRENT VS TARGET STATE")
    lines.append("-" * 70)

    lines.append(
        f"Growth/Risk Weight: "
        f"{target_state['current_growth_weight']:.2f}% "
        f"→ "
        f"{target_state['target_growth_weight']:.2f}%"
    )

    lines.append(
        f"Defensive/Hedge Weight: "
        f"{target_state['current_hedge_weight']:.2f}% "
        f"→ "
        f"{target_state['target_hedge_weight']:.2f}%"
    )

    lines.append("")
    lines.append("EXECUTION TRANSITION PLAN")
    lines.append("-" * 70)

    if not execution["approved"]:
        lines.append(
            "Transition sequencing blocked pending governance approval."
        )

    else:
        lines.append("Growth/Risk Transition Path:")

        for step in growth_transition:
            lines.append(
                f"Day {step['day']}: "
                f"{step['projected_weight']:.2f}% "
                f"(Δ {step['step_change']:+.2f}%)"
            )

        lines.append("")
        lines.append("Defensive/Hedge Transition Path:")

        for step in hedge_transition:
            lines.append(
                f"Day {step['day']}: "
                f"{step['projected_weight']:.2f}% "
                f"(Δ {step['step_change']:+.2f}%)"
            )

    lines.append("")
    lines.append("EXECUTION ACTION LINKAGE")
    lines.append("-" * 70)

    if execution["actions"]:
        for idx, action in enumerate(
            execution["actions"],
            start=1,
        ):
            lines.append(f"{idx}. {action}")

    lines.append("")
    lines.append(build_execution_friction_report())

    lines.append("")
    lines.append(build_realtime_adaptation_report())

    lines.append("")
    lines.append("TRANSITION INTERPRETATION")
    lines.append("-" * 70)

    lines.append(
        "The transition engine converts institutional reasoning into "
        "controlled portfolio migration sequencing rather than abrupt "
        "allocation switching."
    )

    return "\n".join(lines)