from src.ai.policy_constraint_engine import (
    evaluate_policy_constraints,
    build_policy_constraint_report,
)

def evaluate_governance_conditions(
    synthesis_text: str,
    meta_reasoning_text: str,
):
    synthesis_lower = synthesis_text.lower()
    meta_lower = meta_reasoning_text.lower()

    governance = {
        "requires_additional_validation": False,
        "override_recommended": False,
        "escalate_committee_review": False,
        "approve_recommendation": False,
    }

    if (
        "further evidence may be required" in meta_lower
        or "conditional" in meta_lower
    ):
        governance["requires_additional_validation"] = True

    if (
        "confidence quality: low" in meta_lower
        or "confidence quality: low-moderate" in meta_lower
    ):
        governance["override_recommended"] = True

    if (
        "tension between" in meta_lower
        or "disagreement" in meta_lower
    ):
        governance["escalate_committee_review"] = True

    if (
        "maintain current allocation discipline" in synthesis_lower
        and not governance["override_recommended"]
    ):
        governance["approve_recommendation"] = True

    return governance


def build_cio_decision(governance: dict):
    if governance["override_recommended"]:
        return (
            "CIO OVERRIDE: Current recommendation confidence is insufficient "
            "for autonomous institutional action."
        )

    if governance["requires_additional_validation"]:
        return (
            "CIO REVIEW: Additional evidence and regime validation are "
            "recommended before major allocation adjustments."
        )

    if governance["escalate_committee_review"]:
        return (
            "CIO ESCALATION: Cross-agent disagreement warrants deeper "
            "investment committee review."
        )

    if governance["approve_recommendation"]:
        return (
            "CIO APPROVAL: The recommendation is acceptable under current "
            "institutional risk conditions."
        )

    return (
        "CIO STATUS: Monitoring current institutional conditions without "
        "portfolio override."
    )


def build_cio_oversight_report(
    query: str,
    synthesis_text: str,
    meta_reasoning_text: str,
):
    governance = evaluate_governance_conditions(
        synthesis_text,
        meta_reasoning_text,
    )

    policy_result = evaluate_policy_constraints()

    if not policy_result["policy_pass"]:
        governance["override_recommended"] = True
        governance["approve_recommendation"] = False
        governance["requires_additional_validation"] = True

    cio_decision = build_cio_decision(
        governance,
    )

    lines = []

    lines.append("=" * 90)
    lines.append("AURUM CIO OVERSIGHT ENGINE")
    lines.append("=" * 90)

    lines.append("")
    lines.append(f"Original Query: {query}")

    lines.append("")
    lines.append("INSTITUTIONAL GOVERNANCE REVIEW")
    lines.append("-" * 70)

    for key, value in governance.items():
        status = "ACTIVE" if value else "not triggered"

        lines.append(
            f"{key}: {status}"
        )

    lines.append("")
    lines.append(build_policy_constraint_report())

    lines.append("")
    lines.append("CIO EXECUTIVE DECISION")
    lines.append("-" * 70)

    lines.append(cio_decision)

    lines.append("")
    lines.append("OVERSIGHT INTERPRETATION")
    lines.append("-" * 70)

    if governance["requires_additional_validation"]:
        lines.append(
            "The supervisory layer believes current evidence remains "
            "directionally useful but institutionally incomplete."
        )

    if governance["escalate_committee_review"]:
        lines.append(
            "Cross-agent disagreement indicates unresolved institutional "
            "tradeoffs between robustness and upside participation."
        )

    if governance["override_recommended"]:
        lines.append(
            "The CIO layer is withholding autonomous approval because "
            "confidence reliability is insufficient."
        )

    if governance["approve_recommendation"]:
        lines.append(
            "The recommendation is considered institutionally acceptable "
            "under current live conditions."
        )

    return "\n".join(lines)