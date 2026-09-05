from src.ai.decision_explanation_agent import (
    build_decision_explanation,
)

from src.ai.risk_critic_agent import (
    build_risk_critique,
)

from src.ai.scenario_parser import (
    load_scenario_report,
    parse_scenario_results,
    find_worst_scenario,
)


def build_bull_case():
    lines = []

    lines.append("PORTFOLIO MANAGER VIEW")
    lines.append("-" * 70)

    lines.append(
        "The portfolio is intentionally designed to maximize robustness "
        "rather than speculative upside. The allocation framework prioritizes "
        "risk-adjusted consistency, diversification, and drawdown control."
    )

    lines.append(
        "Regime-aware allocation and probabilistic blending reduce the risk "
        "of hard allocation switches during unstable market transitions."
    )

    lines.append(
        "Exposure to defensive assets such as TLT, GLD, and VIX improves "
        "portfolio resilience during adverse environments."
    )

    lines.append(
        "The system still preserves upside participation through controlled "
        "equity exposure and adaptive allocation overlays."
    )

    return "\n".join(lines)


def build_bear_case():
    lines = []

    lines.append("RISK COMMITTEE VIEW")
    lines.append("-" * 70)

    lines.append(
        "The portfolio may be excessively defensive relative to current "
        "market conditions, potentially suppressing long-run upside capture."
    )

    lines.append(
        "Concentration risk remains present through broad equity beta exposure "
        "and possible hidden factor crowding."
    )

    lines.append(
        "Historical covariance and diversification assumptions may fail "
        "during systemic crises when cross-asset correlations converge."
    )

    lines.append(
        "Regime transition models may underestimate the speed and severity "
        "of future market dislocations."
    )

    return "\n".join(lines)


def build_committee_conclusion():
    lines = []

    lines.append("COMMITTEE CONCLUSION")
    lines.append("-" * 70)

    lines.append(
        "AURUM currently demonstrates strong institutional portfolio "
        "construction discipline with advanced risk engineering."
    )

    lines.append(
        "However, the committee acknowledges ongoing vulnerability to "
        "tail-risk contagion, correlation breakdown, and defensive "
        "underperformance during sustained bull markets."
    )

    lines.append(
        "The current allocation should therefore be interpreted as "
        "a robustness-oriented institutional posture rather than "
        "an aggressive return-maximization strategy."
    )

    return "\n".join(lines)


def build_committee_debate(query: str):
    decision_view = build_decision_explanation(query)
    risk_view = build_risk_critique(query)

    scenario_report = load_scenario_report()
    scenarios = parse_scenario_results(scenario_report)
    worst_scenario = find_worst_scenario(scenarios)

    lines = []

    lines.append("AURUM INVESTMENT COMMITTEE DEBATE")
    lines.append("=" * 90)
    lines.append(f"Committee Topic: {query}")
    lines.append("")

    if worst_scenario:
        lines.append("CURRENT DOMINANT RISK")
        lines.append("-" * 70)
        lines.append(
            f"Worst Live Scenario: {worst_scenario['scenario']} "
            f"({worst_scenario['live_impact_pct']:.2f}%)"
        )
        lines.append(
            f"Worst Sleeve: {worst_scenario['worst_sleeve']}"
        )
        lines.append("")

    lines.append(build_bull_case())
    lines.append("")

    lines.append(build_bear_case())
    lines.append("")

    lines.append(build_committee_conclusion())
    lines.append("")

    lines.append("DECISION AGENT SUMMARY")
    lines.append("-" * 70)
    lines.append(
        decision_view[:2500]
    )

    lines.append("")
    lines.append("RISK CRITIC SUMMARY")
    lines.append("-" * 70)
    lines.append(
        risk_view[:2500]
    )

    return "\n".join(lines)


if __name__ == "__main__":
    committee_queries = [
        "Should the portfolio remain defensive?",
        "Should AURUM reduce risk exposure?",
        "Is the allocation strategy too conservative?",
        "How should the investment committee evaluate current positioning?",
    ]

    print("\n")
    print("=" * 90)
    print("AURUM COMMITTEE DEBATE ENGINE")
    print("=" * 90)

    for query in committee_queries:
        print("\n" + "#" * 90)
        print(build_committee_debate(query))