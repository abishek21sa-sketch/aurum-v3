from src.ai.rag_context_engine import retrieve_relevant_context
from src.ai.scenario_parser import (
    load_scenario_report,
    parse_scenario_results,
    find_worst_scenario,
)


def detect_concentration_risk(text: str):
    risks = []

    if "SPY 0.5" in text or "SPY 5." in text:
        risks.append(
            "SPY exposure appears materially elevated, creating concentration risk "
            "to broad equity beta."
        )

    if "QQQ 5." in text:
        risks.append(
            "QQQ concentration suggests elevated sensitivity to growth and "
            "technology-led drawdowns."
        )

    return risks


def detect_tail_risk(text: str):
    risks = []

    if "CVaR" in text:
        risks.append(
            "Tail-risk sensitivity remains important because extreme market "
            "conditions may exceed variance-based assumptions."
        )

    if "volatility_spike" in text:
        risks.append(
            "Volatility spike scenarios continue to produce negative portfolio "
            "impacts under stress conditions."
        )

    return risks


def detect_regime_fragility(text: str):
    risks = []

    if "shock" in text or "stress" in text:
        risks.append(
            "Regime instability remains a core vulnerability because asset "
            "correlations can rapidly shift during stressed environments."
        )

    if "transition probabilities" in text:
        risks.append(
            "Regime transition estimation risk exists because future market "
            "states may diverge from historical transition behavior."
        )

    return risks


def detect_over_defensive_positioning(text: str):
    risks = []

    if "minimum variance" in text:
        risks.append(
            "The portfolio may be overly defensive and could underperform "
            "during sustained bull-market rallies."
        )

    if "low volatility focus" in text:
        risks.append(
            "Low-volatility optimization may suppress upside convexity "
            "during strong momentum-driven environments."
        )

    return risks


def detect_correlation_breakdown(text: str):
    risks = []

    if "diversification" in text:
        risks.append(
            "Diversification assumptions may weaken during systemic crises "
            "when traditionally uncorrelated assets begin moving together."
        )

    return risks


def build_risk_critique(query: str):
    retrieved = retrieve_relevant_context(query, top_k=6)

    scenario_report = load_scenario_report()
    scenarios = parse_scenario_results(scenario_report)
    worst_scenario = find_worst_scenario(scenarios)

    combined_text = " ".join(
        [item["content"] for item in retrieved]
    )

    risks = []

    risks.extend(detect_concentration_risk(combined_text))
    risks.extend(detect_tail_risk(combined_text))
    risks.extend(detect_regime_fragility(combined_text))
    risks.extend(detect_over_defensive_positioning(combined_text))
    risks.extend(detect_correlation_breakdown(combined_text))

    risks = list(dict.fromkeys(risks))

    lines = []

    lines.append("AURUM RISK CRITIC AGENT")
    lines.append("=" * 70)
    lines.append(f"Risk Review Query: {query}")
    lines.append("")

    lines.append("PRIMARY RISK CONCLUSION")
    lines.append("-" * 70)

    if worst_scenario:
        lines.append(
            f"The current dominant vulnerability is "
            f"{worst_scenario['scenario']} "
            f"with a live impact of "
            f"{worst_scenario['live_impact_pct']:.2f}%."
        )

    lines.append("")
    lines.append("CRITICAL RISK OBSERVATIONS")
    lines.append("-" * 70)

    if risks:
        for i, risk in enumerate(risks, start=1):
            lines.append(f"{i}. {risk}")
    else:
        lines.append(
            "No major structural risk concerns were automatically identified."
        )

    lines.append("")
    lines.append("INSTITUTIONAL RISK INTERPRETATION")
    lines.append("-" * 70)
    lines.append(
        "The portfolio demonstrates strong institutional risk engineering, "
        "but remains exposed to structural market breakdowns, model risk, "
        "and changing cross-asset behavior during severe stress regimes."
    )

    lines.append("")
    lines.append("RISK COMMITTEE QUESTIONS")
    lines.append("-" * 70)

    committee_questions = [
        "Are current diversification assumptions still reliable during systemic stress?",
        "Could regime transitions occur faster than the model anticipates?",
        "Is the portfolio sacrificing too much upside for defensive stability?",
        "Are live overlays increasing hidden fragility?",
        "Would tail hedges remain effective during liquidity crises?",
    ]

    for q in committee_questions:
        lines.append(f"- {q}")

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
        "Critique current portfolio risk.",
        "What are the biggest weaknesses in the strategy?",
        "What could fail during a crisis?",
        "Is the portfolio too defensive?",
    ]

    for query in test_queries:
        print("\n" + "#" * 90)
        print(build_risk_critique(query))