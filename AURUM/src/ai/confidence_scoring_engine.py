from src.ai.scenario_parser import (
    load_scenario_report,
    parse_scenario_results,
    find_worst_scenario,
)

from src.ai.rag_context_engine import (
    retrieve_relevant_context,
)


def score_regime_confidence(text: str):
    text = text.lower()

    score = 0.5

    if "normal" in text:
        score += 0.15

    if "stress" in text:
        score -= 0.10

    if "shock" in text:
        score -= 0.20

    if "transition probabilities" in text:
        score -= 0.05

    return max(0.0, min(score, 1.0))


def score_scenario_resilience(worst_live_impact: float):
    if worst_live_impact <= -3.0:
        return 0.25

    if worst_live_impact <= -2.0:
        return 0.45

    if worst_live_impact <= -1.0:
        return 0.65

    return 0.85


def score_portfolio_stability(text: str):
    text = text.lower()

    score = 0.5

    if "minimum variance" in text:
        score += 0.15

    if "risk parity" in text:
        score += 0.10

    if "cvar" in text:
        score += 0.10

    if "drawdown" in text:
        score += 0.05

    if "volatility spike" in text:
        score -= 0.10

    return max(0.0, min(score, 1.0))


def score_overlay_stability(scenarios: list[dict]):
    penalties = 0

    for s in scenarios:
        if s["overlay_delta_pct"] < 0:
            penalties += abs(s["overlay_delta_pct"])

    score = 1.0 - (penalties / 2.0)

    return max(0.0, min(score, 1.0))


def confidence_label(score: float):
    if score >= 0.80:
        return "HIGH CONFIDENCE"

    if score >= 0.60:
        return "MODERATE CONFIDENCE"

    if score >= 0.40:
        return "LOW-MODERATE CONFIDENCE"

    return "LOW CONFIDENCE"


def build_confidence_report(query: str):
    retrieved = retrieve_relevant_context(query, top_k=6)

    combined_text = " ".join(
        [item["content"] for item in retrieved]
    )

    scenario_report = load_scenario_report()
    scenarios = parse_scenario_results(scenario_report)

    worst_scenario = find_worst_scenario(scenarios)

    regime_conf = score_regime_confidence(combined_text)

    resilience_conf = score_scenario_resilience(
        worst_scenario["live_impact_pct"]
    )

    stability_conf = score_portfolio_stability(
        combined_text
    )

    overlay_conf = score_overlay_stability(
        scenarios
    )

    total_confidence = (
        regime_conf
        + resilience_conf
        + stability_conf
        + overlay_conf
    ) / 4.0

    lines = []

    lines.append("AURUM CONFIDENCE SCORING ENGINE")
    lines.append("=" * 90)
    lines.append(f"Confidence Review Query: {query}")
    lines.append("")

    lines.append("CONFIDENCE COMPONENTS")
    lines.append("-" * 70)

    lines.append(
        f"Regime Confidence: "
        f"{regime_conf:.2f} "
        f"({confidence_label(regime_conf)})"
    )

    lines.append(
        f"Scenario Resilience Confidence: "
        f"{resilience_conf:.2f} "
        f"({confidence_label(resilience_conf)})"
    )

    lines.append(
        f"Portfolio Stability Confidence: "
        f"{stability_conf:.2f} "
        f"({confidence_label(stability_conf)})"
    )

    lines.append(
        f"Overlay Stability Confidence: "
        f"{overlay_conf:.2f} "
        f"({confidence_label(overlay_conf)})"
    )

    lines.append("")
    lines.append("AGGREGATE SYSTEM CONFIDENCE")
    lines.append("-" * 70)

    lines.append(
        f"Total Confidence Score: "
        f"{total_confidence:.2f}"
    )

    lines.append(
        f"Confidence Classification: "
        f"{confidence_label(total_confidence)}"
    )

    lines.append("")
    lines.append("CONFIDENCE INTERPRETATION")
    lines.append("-" * 70)

    if total_confidence >= 0.75:
        lines.append(
            "AURUM currently exhibits strong institutional stability "
            "with relatively controlled downside uncertainty."
        )

    elif total_confidence >= 0.55:
        lines.append(
            "AURUM currently exhibits moderate confidence. The portfolio "
            "appears stable, but stress sensitivity remains important."
        )

    else:
        lines.append(
            "AURUM confidence is deteriorating. Elevated uncertainty, "
            "regime fragility, or stress sensitivity may require "
            "defensive review."
        )

    lines.append("")
    lines.append("DOMINANT UNCERTAINTY DRIVER")
    lines.append("-" * 70)

    if worst_scenario:
        lines.append(
            f"Worst Scenario: {worst_scenario['scenario']} "
            f"({worst_scenario['live_impact_pct']:.2f}%)"
        )

        lines.append(
            f"Worst Sleeve: {worst_scenario['worst_sleeve']}"
        )

    lines.append("")
    lines.append("RETRIEVED SUPPORTING CONTEXT")
    lines.append("-" * 70)

    for i, item in enumerate(retrieved, start=1):
        preview = item["content"][:500].replace("\n", " ")

        lines.append(f"[{i}] {item['path']}")
        lines.append(preview)
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    test_queries = [
        "Evaluate portfolio confidence.",
        "How stable is the current regime?",
        "How reliable is the portfolio positioning?",
        "Evaluate current institutional confidence.",
    ]

    print("\n")
    print("=" * 90)
    print("AURUM CONFIDENCE ENGINE")
    print("=" * 90)

    for query in test_queries:
        print("\n" + "#" * 90)
        print(build_confidence_report(query))