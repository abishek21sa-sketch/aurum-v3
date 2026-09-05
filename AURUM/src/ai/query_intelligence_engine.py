from collections import defaultdict


INTENT_PATTERNS = {
    "decision": {
        "keywords": [
            "allocation",
            "portfolio",
            "weights",
            "optimize",
            "optimization",
            "positioning",
            "rebalance",
            "exposure",
        ],
        "base_weight": 1.0,
    },

    "scenario": {
        "keywords": [
            "scenario",
            "stress",
            "shock",
            "crash",
            "drawdown",
            "volatility",
            "rally",
            "downside",
            "tail",
            "rates",
            "equity",
        ],
        "base_weight": 1.2,
    },

"   risk": {
        "keywords": [
            "risk",
            "fragility",
            "fragile",
            "weakness",
            "critic",
            "critique",
            "failure",
            "hedge",
            "concentration",
            "correlation",
            "defensive",
        ],
        "base_weight": 1.3,
    },

    "committee": {
        "keywords": [
            "committee",
            "debate",
            "should",
            "recommend",
            "reduce risk",
            "increase exposure",
            "approve",
            "disagree",
        ],
        "base_weight": 1.1,
    },

    "confidence": {
        "keywords": [
            "confidence",
            "confident",
            "stable",
            "stability",
            "certainty",
            "conviction",
            "uncertainty",
            "reliable",
            "trust",
            "probability",
            "regime",
        ],
        "base_weight": 1.4,
    },
}


def normalize_query(query: str):
    return query.lower().strip()


def extract_intents(query: str):
    query = normalize_query(query)

    scores = defaultdict(float)

    for intent, config in INTENT_PATTERNS.items():

        base_weight = config["base_weight"]

        for keyword in config["keywords"]:

            if keyword in query:
                scores[intent] += base_weight

                if keyword == query:
                    scores[intent] += 1.0

    return dict(scores)


def classify_query_intelligence(query: str):
    scores = extract_intents(query)

    if not scores:
        return {
            "primary_intent": "decision",
            "intent_scores": {},
            "selected_agents": ["decision"],
        }

    sorted_scores = sorted(
        scores.items(),
        key=lambda x: x[1],
        reverse=True,
    )

    primary_intent = sorted_scores[0][0]

    selected_agents = []

    max_score = sorted_scores[0][1]

    threshold = max_score * 0.35

    for intent, score in sorted_scores:
        if score >= threshold:
            selected_agents.append(intent)

    return {
        "primary_intent": primary_intent,
        "intent_scores": dict(sorted_scores),
        "selected_agents": selected_agents,
    }


def build_intelligence_report(query: str):
    result = classify_query_intelligence(query)

    lines = []

    lines.append("=" * 90)
    lines.append("AURUM QUERY INTELLIGENCE ENGINE")
    lines.append("=" * 90)

    lines.append("")
    lines.append(f"QUERY: {query}")

    lines.append("")
    lines.append("PRIMARY INTENT")
    lines.append("-" * 70)
    lines.append(result["primary_intent"].upper())

    lines.append("")
    lines.append("INTENT SCORES")
    lines.append("-" * 70)

    for intent, score in result["intent_scores"].items():
        lines.append(
            f"{intent.upper():15s} -> {score:.2f}"
        )

    lines.append("")
    lines.append("SELECTED AGENTS")
    lines.append("-" * 70)

    for agent in result["selected_agents"]:
        lines.append(f"- {agent.upper()}")

    return "\n".join(lines)


if __name__ == "__main__":
    test_queries = [
        "How confident is the current regime?",
        "Critique the current allocation.",
        "Should the investment committee reduce risk?",
        "How fragile is the portfolio during stress?",
        "Debate whether AURUM is too defensive.",
        "What is the downside risk during volatility shock?",
        "How reliable is the current allocation strategy?",
    ]

    print("\n")
    print("=" * 90)
    print("AURUM QUERY INTELLIGENCE DEMO")
    print("=" * 90)

    for query in test_queries:
        print("\n")
        print(build_intelligence_report(query))