def detect_agent_signals(agent_outputs: dict):
    combined = " ".join(agent_outputs.values()).lower()

    signals = {
        "downside_risk": any(
            x in combined
            for x in [
                "equity_gap_down",
                "downside",
                "stress",
                "tail-risk",
                "correlation breakdown",
            ]
        ),
        "defensive_posture": "defensive" in combined,
        "confidence_concern": any(
            x in combined
            for x in [
                "low confidence",
                "low-moderate confidence",
                "moderate confidence",
            ]
        ),
        "concentration_risk": any(
            x in combined
            for x in [
                "concentration risk",
                "spy exposure",
                "broad equity beta",
            ]
        ),
        "upside_tradeoff": any(
            x in combined
            for x in [
                "underperform during sustained bull-market rallies",
                "sacrifice upside",
                "suppressing long-run upside",
            ]
        ),
    }

    return signals


def build_final_recommendation(signals: dict):
    if signals["downside_risk"] and signals["confidence_concern"]:
        return (
            "Maintain the defensive posture, but actively monitor downside "
            "scenario exposure and review concentrated equity beta risk."
        )

    if signals["concentration_risk"]:
        return (
            "Maintain current allocation discipline while reducing hidden "
            "concentration risk where possible."
        )

    if signals["upside_tradeoff"]:
        return (
            "Preserve defensive controls, but evaluate whether the portfolio "
            "is giving up excessive upside participation."
        )

    return (
        "Maintain current institutional positioning while continuing regular "
        "risk and scenario monitoring."
    )


def build_cross_agent_synthesis(query: str, agent_outputs: dict):
    signals = detect_agent_signals(agent_outputs)
    recommendation = build_final_recommendation(signals)

    lines = []

    lines.append("=" * 90)
    lines.append("AURUM CROSS-AGENT SYNTHESIS ENGINE")
    lines.append("=" * 90)

    lines.append("")
    lines.append(f"Original Query: {query}")

    lines.append("")
    lines.append("AGENT SIGNAL SUMMARY")
    lines.append("-" * 70)

    for signal, active in signals.items():
        status = "ACTIVE" if active else "not detected"
        lines.append(f"{signal}: {status}")

    lines.append("")
    lines.append("FINAL CIO SYNTHESIS")
    lines.append("-" * 70)

    if signals["downside_risk"]:
        lines.append(
            "The agent ensemble identifies downside scenario vulnerability "
            "as a material risk consideration."
        )

    if signals["defensive_posture"]:
        lines.append(
            "The portfolio is currently positioned with a defensive, "
            "risk-aware institutional posture."
        )

    if signals["confidence_concern"]:
        lines.append(
            "Confidence is not uniformly high, so recommendations should be "
            "treated as conditional rather than absolute."
        )

    if signals["concentration_risk"]:
        lines.append(
            "The risk layer flags concentration or broad equity beta exposure "
            "as an important review item."
        )

    if signals["upside_tradeoff"]:
        lines.append(
            "The committee view highlights the tradeoff between downside "
            "protection and upside participation."
        )

    lines.append("")
    lines.append("FINAL ACTION RECOMMENDATION")
    lines.append("-" * 70)
    lines.append(recommendation)

    return "\n".join(lines)