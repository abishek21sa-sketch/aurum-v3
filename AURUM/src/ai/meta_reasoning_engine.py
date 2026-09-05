def evaluate_evidence_strength(agent_outputs: dict):
    combined = " ".join(agent_outputs.values()).lower()

    evidence_count = combined.count("results\\")

    if evidence_count >= 8:
        return "HIGH", "Multiple supporting AURUM reports were retrieved across agents."

    if evidence_count >= 4:
        return "MODERATE", "Several supporting AURUM reports were retrieved, but coverage is not exhaustive."

    return "LOW", "Limited supporting evidence was retrieved."


def detect_agent_disagreement(agent_outputs: dict):
    combined = " ".join(agent_outputs.values()).lower()

    disagreement_flags = []

    if "defensive" in combined and "upside" in combined:
        disagreement_flags.append(
            "There is tension between defensive positioning and upside participation."
        )

    if "reduce risk" in combined and "maintain" in combined:
        disagreement_flags.append(
            "There is tension between reducing risk and maintaining current allocation discipline."
        )

    if "normal" in combined and "stress" in combined:
        disagreement_flags.append(
            "The system identifies a normal market regime while still flagging stress vulnerability."
        )

    return disagreement_flags


def evaluate_confidence_quality(agent_outputs: dict):
    combined = " ".join(agent_outputs.values()).lower()

    if "low confidence" in combined or "low-moderate confidence" in combined:
        return (
            "LOW-MODERATE",
            "Confidence outputs indicate meaningful uncertainty in current regime or scenario reliability.",
        )

    if "moderate confidence" in combined:
        return (
            "MODERATE",
            "Confidence outputs suggest usable but conditional institutional confidence.",
        )

    if "high confidence" in combined:
        return (
            "HIGH",
            "Confidence outputs suggest strong reliability, though stress assumptions should still be monitored.",
        )

    return (
        "UNSPECIFIED",
        "No explicit confidence signal was detected in the agent outputs.",
    )


def build_meta_reasoning_report(query: str, agent_outputs: dict):
    evidence_level, evidence_reason = evaluate_evidence_strength(agent_outputs)
    confidence_level, confidence_reason = evaluate_confidence_quality(agent_outputs)
    disagreement_flags = detect_agent_disagreement(agent_outputs)

    lines = []

    lines.append("=" * 90)
    lines.append("AURUM META-REASONING ENGINE")
    lines.append("=" * 90)

    lines.append("")
    lines.append(f"Original Query: {query}")

    lines.append("")
    lines.append("EVIDENCE QUALITY")
    lines.append("-" * 70)
    lines.append(f"Evidence Strength: {evidence_level}")
    lines.append(evidence_reason)

    lines.append("")
    lines.append("CONFIDENCE QUALITY")
    lines.append("-" * 70)
    lines.append(f"Confidence Quality: {confidence_level}")
    lines.append(confidence_reason)

    lines.append("")
    lines.append("AGENT DISAGREEMENT CHECK")
    lines.append("-" * 70)

    if disagreement_flags:
        for flag in disagreement_flags:
            lines.append(f"- {flag}")
    else:
        lines.append("No major internal disagreement detected.")

    lines.append("")
    lines.append("META-REASONING CONCLUSION")
    lines.append("-" * 70)

    if evidence_level == "HIGH" and confidence_level in {"HIGH", "MODERATE"}:
        lines.append(
            "The agent ensemble has sufficient support for a usable institutional recommendation."
        )

    elif confidence_level in {"LOW-MODERATE", "LOW"}:
        lines.append(
            "The recommendation should be treated as conditional because uncertainty remains material."
        )

    else:
        lines.append(
            "The agent ensemble provides a useful directional view, but further evidence may be required."
        )

    return "\n".join(lines)