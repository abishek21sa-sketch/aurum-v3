from src.ai.rag_context_engine import retrieve_relevant_context
from src.ai.scenario_parser import (
    load_scenario_report,
    parse_scenario_results,
    find_worst_scenario,
    find_best_scenario,
)


def load_parsed_scenarios():
    report = load_scenario_report()
    return parse_scenario_results(report)


def match_scenario_from_query(query: str, scenarios: list[dict]):
    query_lower = query.lower()

    aliases = {
        "equity_gap_down": ["equity", "stock", "stocks", "gap", "crash", "selloff"],
        "crypto_crash": ["crypto", "bitcoin", "btc", "eth"],
        "rates_shock": ["rates", "interest", "bond", "tlt", "yield"],
        "risk_on_rally": ["rally", "risk on", "upside", "bull"],
        "volatility_spike": ["volatility", "vix", "vol spike", "spike"],
    }

    for scenario in scenarios:
        scenario_name = scenario["scenario"]

        if scenario_name in query_lower:
            return scenario

        for alias in aliases.get(scenario_name, []):
            if alias in query_lower:
                return scenario

    if "worst" in query_lower:
        return find_worst_scenario(scenarios)

    if "best" in query_lower:
        return find_best_scenario(scenarios)

    return find_worst_scenario(scenarios)


def classify_severity(live_impact: float):
    if live_impact <= -2.5:
        return "severe downside scenario"
    if live_impact <= -1.5:
        return "moderate downside scenario"
    if live_impact < 0:
        return "mild downside scenario"
    if live_impact >= 2.0:
        return "strong upside scenario"
    return "positive or neutral scenario"


def explain_overlay(delta: float):
    if delta < 0:
        return (
            f"The live overlay worsens the modeled impact by {delta:.2f} percentage points, "
            "which means current live conditions are increasing stress sensitivity."
        )

    if delta > 0:
        return (
            f"The live overlay improves the modeled impact by {delta:.2f} percentage points, "
            "which means current live conditions are partially cushioning the scenario."
        )

    return "The live overlay has no measurable effect on this scenario."


def build_scenario_reasoning(query: str):
    scenarios = load_parsed_scenarios()
    matched = match_scenario_from_query(query, scenarios)

    retrieved = retrieve_relevant_context(query, top_k=5)

    lines = []

    lines.append("AURUM SCENARIO REASONING AGENT")
    lines.append("=" * 70)
    lines.append(f"Scenario Query: {query}")
    lines.append("")

    if not matched:
        lines.append("No parsed scenario match found.")
        return "\n".join(lines)

    severity = classify_severity(matched["live_impact_pct"])

    lines.append("MATCHED SCENARIO")
    lines.append("-" * 70)
    lines.append(f"Scenario: {matched['scenario']}")
    lines.append(f"Base Impact: {matched['base_impact_pct']:.2f}%")
    lines.append(f"Live Impact: {matched['live_impact_pct']:.2f}%")
    lines.append(f"Overlay Delta: {matched['overlay_delta_pct']:.2f}%")
    lines.append(f"Worst Sleeve: {matched['worst_sleeve']}")
    lines.append(f"Severity: {severity}")

    lines.append("")
    lines.append("SCENARIO INTERPRETATION")
    lines.append("-" * 70)

    if matched["live_impact_pct"] < 0:
        lines.append(
            f"{matched['scenario']} is expected to reduce portfolio value by "
            f"{abs(matched['live_impact_pct']):.2f}% under current live conditions."
        )
    else:
        lines.append(
            f"{matched['scenario']} is expected to improve portfolio value by "
            f"{matched['live_impact_pct']:.2f}% under current live conditions."
        )

    lines.append(explain_overlay(matched["overlay_delta_pct"]))

    lines.append("")
    lines.append("SLEEVE-LEVEL RISK")
    lines.append("-" * 70)

    if matched["worst_sleeve"] == "none_positive_scenario":
        lines.append(
            "No worst sleeve is identified because this is a positive scenario."
        )
    else:
        lines.append(
            f"The weakest sleeve under this scenario is {matched['worst_sleeve']}. "
            "This sleeve should be reviewed for concentration, beta exposure, "
            "or sensitivity to the modeled shock."
        )

    lines.append("")
    lines.append("PORTFOLIO ACTION IMPLICATION")
    lines.append("-" * 70)

    if matched["live_impact_pct"] <= -2.5:
        lines.append(
            "This scenario deserves active monitoring. AURUM should consider whether "
            "hedging, de-risking, or lower exposure to the weakest sleeve is justified."
        )
    elif matched["live_impact_pct"] < 0:
        lines.append(
            "This scenario is adverse but not catastrophic. Current diversification "
            "appears to reduce the shock, but downside sensitivity remains present."
        )
    else:
        lines.append(
            "This scenario is favorable. The portfolio participates in upside while "
            "maintaining its broader defensive structure."
        )

    lines.append("")
    lines.append("RETRIEVED SUPPORTING CONTEXT")
    lines.append("-" * 70)

    for i, item in enumerate(retrieved, start=1):
        preview = item["content"][:600].replace("\n", " ")
        lines.append(f"[{i}] {item['path']}")
        lines.append(preview)
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    test_queries = [
        "What is the worst live scenario?",
        "What happens during an equity crash?",
        "How bad is a volatility spike?",
        "What happens if rates shock the portfolio?",
        "What happens in a risk-on rally?",
    ]

    for query in test_queries:
        print("\n" + "#" * 90)
        print(build_scenario_reasoning(query))