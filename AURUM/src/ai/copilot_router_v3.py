from collections import defaultdict

from src.ai.decision_explanation_agent import (
    build_decision_explanation,
)

from src.ai.scenario_reasoning_agent import (
    build_scenario_reasoning,
)

from src.ai.risk_critic_agent import (
    build_risk_critique,
)

from src.ai.committee_debate_agent import (
    build_committee_debate,
)

from src.ai.confidence_scoring_engine import (
    build_confidence_report,
)

from src.ai.query_intelligence_engine import (
    classify_query_intelligence,
)

from src.ai.live_market_context_engine import (
    build_live_market_context,
    format_live_market_context,
)

from src.ai.cross_agent_synthesis_engine import (
    build_cross_agent_synthesis,
)

from src.ai.meta_reasoning_engine import (
    build_meta_reasoning_report,
)

from src.ai.dynamic_agent_weighting_engine import (
    compute_dynamic_agent_weights,
    build_agent_weighting_report,
)

from src.ai.cio_oversight_engine import (
    build_cio_oversight_report,
)

from src.ai.execution_action_engine import (
    build_execution_action_report,
)

from src.ai.portfolio_state_transition_engine import (
    build_portfolio_transition_report,
)

from src.ai.autonomous_regime_reconfiguration_engine import (
    build_autonomous_reconfiguration_report,
)

from src.ai.policy_evolution_engine import (
    build_policy_evolution_report,
)

from src.ai.institutional_digital_twin_engine import (
    build_digital_twin_report,
)

from src.ai.stochastic_futures_engine import (
    build_stochastic_futures_report,
)

from src.ai.adversarial_market_simulation_engine import (
    build_adversarial_simulation_report,
)

from src.ai.recursive_self_evaluation_engine import (
    build_recursive_self_evaluation_report,
)

AGENT_KEYWORDS = {
    "decision": [
        "allocation",
        "portfolio",
        "optimize",
        "optimization",
        "investment",
        "weights",
        "positioning",
    ],

    "scenario": [
        "scenario",
        "crash",
        "shock",
        "stress",
        "volatility",
        "drawdown",
        "rally",
        "downside",
        "rates",
        "worst",
    ],

    "risk": [
        "risk",
        "fragility",
        "weakness",
        "critic",
        "tail",
        "failure",
        "hedge",
        "defensive",
    ],

    "committee": [
        "committee",
        "debate",
        "should",
        "reduce risk",
        "increase exposure",
        "argument",
        "disagree",
    ],

    "confidence": [
        "confidence",
        "stable",
        "certainty",
        "reliable",
        "trust",
        "conviction",
        "uncertainty",
    ],
}


AGENT_BUILDERS = {
    "decision": build_decision_explanation,
    "scenario": build_scenario_reasoning,
    "risk": build_risk_critique,
    "committee": build_committee_debate,
    "confidence": build_confidence_report,
}


def score_agents(query: str):
    query_lower = query.lower()

    scores = defaultdict(int)

    for agent, keywords in AGENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in query_lower:
                scores[agent] += 1

    return dict(scores)


def select_agents(scores: dict, threshold: int = 1):
    selected = []

    for agent, score in scores.items():
        if score >= threshold:
            selected.append((agent, score))

    selected.sort(key=lambda x: x[1], reverse=True)

    return selected


def build_multi_agent_response(query: str):
    intelligence = classify_query_intelligence(query)
    selected_agents = [
        agent.strip()
        for agent in intelligence["selected_agents"]
    ]
    if not selected_agents:
        selected_agents = ["decision"]

    agent_weights = compute_dynamic_agent_weights(selected_agents)

    lines = []

    lines.append("=" * 90)
    lines.append("AURUM MULTI-AGENT COPILOT ROUTER V3")
    lines.append("=" * 90)

    lines.append("")
    lines.append(f"USER QUERY: {query}")
    live_context = build_live_market_context()

    lines.append("")
    lines.append(format_live_market_context(live_context))

    lines.append("")
    lines.append("ROUTING DECISION")
    lines.append("-" * 70)

    lines.append("")
    lines.append(build_agent_weighting_report(selected_agents))

    agent_outputs = {}

    for agent in selected_agents:
        score = intelligence["intent_scores"].get(agent, 1.0)
        intent_scores = {
            key.strip(): value
            for key, value in intelligence["intent_scores"].items()
        }
        lines.append(
            f"- {agent.upper()} AGENT "
            f"(intent score: {score:.2f}, dynamic weight: {agent_weights.get(agent, 0):.2f})"
        )

    for agent in selected_agents:
        score = intelligence["intent_scores"].get(agent, 1.0)
        intent_scores = {
            key.strip(): value
            for key, value in intelligence["intent_scores"].items()
        }
        builder = AGENT_BUILDERS[agent]

        lines.append("")
        lines.append("#" * 90)
        lines.append(
            f"{agent.upper()} AGENT RESPONSE"
        )
        lines.append("#" * 90)
        lines.append("")

        try:
            response = builder(query)
            agent_outputs[agent] = response
            lines.append(response)

        except Exception as e:
            lines.append(f"ERROR RUNNING {agent}: {str(e)}")
    
        
    synthesis_report = build_cross_agent_synthesis(
        query=query,
        agent_outputs=agent_outputs,
    )

    meta_report = build_meta_reasoning_report(
        query=query,
        agent_outputs=agent_outputs,
    )

    lines.append("")
    lines.append(synthesis_report)

    lines.append("")
    lines.append(meta_report)

    lines.append("")
    lines.append(
        build_cio_oversight_report(
            query=query,
            synthesis_text=synthesis_report,
            meta_reasoning_text=meta_report,
        )
    )

    execution_report = build_execution_action_report(
        query=query,
        synthesis_text=synthesis_report,
        meta_reasoning_text=meta_report,
    )

    lines.append("")
    lines.append(execution_report)

    transition_report = build_portfolio_transition_report(
        query=query,
        synthesis_text=synthesis_report,
        meta_reasoning_text=meta_report,
    )

    lines.append("")
    lines.append(transition_report)

    lines.append("")
    lines.append(build_autonomous_reconfiguration_report())

    lines.append("")
    lines.append(build_policy_evolution_report())
    
    lines.append("")
    lines.append(build_digital_twin_report())

    lines.append("")
    lines.append(build_stochastic_futures_report())

    lines.append("")
    lines.append(build_adversarial_simulation_report())

    lines.append("")
    lines.append(build_recursive_self_evaluation_report())

    return "\n".join(lines)


if __name__ == "__main__":
    test_queries = [
        "What is the worst live scenario?",
        "Critique the current allocation.",
        "How confident is the current regime?",
        "Should the investment committee reduce risk?",
        "Debate whether AURUM is too defensive.",
        "How fragile is the portfolio during stress?",
    ]

    print("\n")
    print("=" * 90)
    print("AURUM ROUTER V3 DEMO")
    print("=" * 90)

    for query in test_queries:
        print("\n" + build_multi_agent_response(query))
        print("\n" + "=" * 90)