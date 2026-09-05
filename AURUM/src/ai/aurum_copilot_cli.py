from src.ai.query_intelligence_engine import classify_query_intelligence
from src.ai.copilot_router_v3 import build_multi_agent_response
from src.ai.session_memory_engine import (
    initialize_memory,
    add_conversation,
    update_portfolio_stance,
    update_risk_regime,
    update_confidence_level,
    build_memory_summary,
)


WELCOME_BANNER = """
==========================================================================================
AURUM MEMORY-AWARE INSTITUTIONAL AI COPILOT
==========================================================================================

Capabilities:
- Multi-Agent Query Routing
- Portfolio Decision Explanation
- Scenario Stress Reasoning
- Institutional Risk Critique
- Investment Committee Debate
- Confidence Scoring
- Persistent Session Memory

Commands:
- memory
- exit
- quit
- q

==========================================================================================
"""


def infer_state_updates(query: str, response: str):
    response_lower = response.lower()

    if "defensive" in response_lower:
        update_portfolio_stance("Defensive regime-aware allocation")

    if "equity_gap_down" in response_lower or "stress" in response_lower:
        update_risk_regime("Moderate stress sensitivity")

    if "moderate confidence" in response_lower:
        update_confidence_level("MODERATE CONFIDENCE")

    elif "low confidence" in response_lower:
        update_confidence_level("LOW CONFIDENCE")

    elif "high confidence" in response_lower:
        update_confidence_level("HIGH CONFIDENCE")


def summarize_response_for_memory(response: str):
    lines = response.splitlines()

    useful_lines = []

    for line in lines:
        line_clean = line.strip()

        if not line_clean:
            continue

        if any(
            key in line_clean.lower()
            for key in [
                "worst live scenario",
                "dominant vulnerability",
                "confidence classification",
                "committee conclusion",
                "portfolio stance",
                "risk interpretation",
                "scenario:",
                "live impact:",
            ]
        ):
            useful_lines.append(line_clean)

    if useful_lines:
        return " | ".join(useful_lines[:5])

    return response[:500]


def run_copilot():
    initialize_memory()

    print(WELCOME_BANNER)

    while True:
        try:
            query = input("AURUM COPILOT > ").strip()

            if not query:
                continue

            if query.lower() in {"exit", "quit", "q"}:
                print("\nShutting down AURUM Copilot...")
                break

            if query.lower() == "memory":
                print("")
                print(build_memory_summary())
                print("")
                continue

            intelligence = classify_query_intelligence(query)
            selected_agents = intelligence["selected_agents"]

            print("\n" + "=" * 90)
            print("QUERY INTELLIGENCE")
            print("-" * 70)
            print(f"Primary Intent: {intelligence['primary_intent'].upper()}")
            print(f"Selected Agents: {', '.join(a.upper() for a in selected_agents)}")
            print("=" * 90)
            print("")

            response = build_multi_agent_response(query)

            print(response)

            summary = summarize_response_for_memory(response)

            add_conversation(
                query=query,
                detected_agents=selected_agents,
                response_summary=summary,
            )

            infer_state_updates(query, response)

            print("\n" + "=" * 90)
            print("SESSION MEMORY UPDATED")
            print("=" * 90 + "\n")

        except KeyboardInterrupt:
            print("\n\nSession interrupted.")
            break

        except Exception as e:
            print("\nERROR:")
            print(str(e))
            print("\n" + "=" * 90 + "\n")


if __name__ == "__main__":
    run_copilot()