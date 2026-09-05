from src.ai.decision_explanation_agent import (
    build_decision_explanation,
)

from src.ai.scenario_reasoning_agent import (
    build_scenario_reasoning,
)

from src.ai.risk_critic_agent import (
    build_risk_critique,
)


DECISION_KEYWORDS = [
    "allocation",
    "decision",
    "optimize",
    "optimization",
    "portfolio",
    "investment committee",
]

SCENARIO_KEYWORDS = [
    "scenario",
    "crash",
    "shock",
    "stress",
    "volatility",
    "rates",
    "rally",
    "worst",
    "downside",
]

RISK_KEYWORDS = [
    "risk",
    "weakness",
    "fragility",
    "critic",
    "failure",
    "defensive",
    "tail risk",
]


def classify_query(query: str):
    query_lower = query.lower()

    decision_score = sum(
        keyword in query_lower
        for keyword in DECISION_KEYWORDS
    )

    scenario_score = sum(
        keyword in query_lower
        for keyword in SCENARIO_KEYWORDS
    )

    risk_score = sum(
        keyword in query_lower
        for keyword in RISK_KEYWORDS
    )

    scores = {
        "decision": decision_score,
        "scenario": scenario_score,
        "risk": risk_score,
    }

    best_agent = max(scores, key=scores.get)

    if scores[best_agent] == 0:
        return "decision"

    return best_agent


def route_query(query: str):
    agent = classify_query(query)

    if agent == "decision":
        return build_decision_explanation(query)

    if agent == "scenario":
        return build_scenario_reasoning(query)

    if agent == "risk":
        return build_risk_critique(query)

    return build_decision_explanation(query)


if __name__ == "__main__":
    demo_queries = [
        "Why did allocation change?",
        "What happens during an equity crash?",
        "What are the biggest weaknesses in the strategy?",
        "Is the portfolio too defensive?",
        "Explain portfolio optimization logic.",
        "What is the worst live scenario?",
    ]

    print("\n")
    print("=" * 90)
    print("AURUM MULTI-AGENT COPILOT ROUTER V2")
    print("=" * 90)

    for query in demo_queries:
        print("\n" + "#" * 90)
        print(f"USER QUERY: {query}")
        print("#" * 90)

        detected_agent = classify_query(query)

        print(f"\nROUTED TO AGENT: {detected_agent.upper()}")
        print("-" * 90)

        response = route_query(query)

        print(response)