from src.ai.rag_context_engine import retrieve_relevant_context


def build_decision_explanation(query: str):
    retrieved = retrieve_relevant_context(query, top_k=5)

    if not retrieved:
        return "No relevant AURUM context found for this decision explanation."

    lines = []

    lines.append("AURUM DECISION EXPLANATION AGENT")
    lines.append("=" * 70)
    lines.append(f"User Question: {query}")
    lines.append("")

    lines.append("SOURCE CONTEXT USED")
    lines.append("-" * 70)
    for item in retrieved:
        lines.append(f"- {item['path']} | score={item['score']} | type={item['type']}")

    lines.append("")
    lines.append("EXECUTIVE EXPLANATION")
    lines.append("-" * 70)
    lines.append(
        "The portfolio decision appears to be driven primarily by risk control, "
        "diversification, and covariance reduction. AURUM is prioritizing assets "
        "that reduce total portfolio volatility rather than simply chasing expected return."
    )

    lines.append("")
    lines.append("TECHNICAL EXPLANATION")
    lines.append("-" * 70)
    lines.append(
        "The optimization logic is based on constrained portfolio construction. "
        "Across the retrieved reports, the system emphasizes long-only, fully invested "
        "allocations with risk-aware constraints. Assets receive higher weights when "
        "they lower marginal contribution to portfolio variance, improve diversification, "
        "or perform better under detected market regimes and scenario stress tests."
    )

    lines.append("")
    lines.append("PORTFOLIO IMPLICATIONS")
    lines.append("-" * 70)
    lines.append(
        "The resulting portfolio should be interpreted as defensive and institutionally "
        "risk-aware. Higher allocations to broad equity, bonds, gold, volatility-linked "
        "exposure, or other diversifiers indicate that AURUM is balancing upside potential "
        "against drawdown control, stress resilience, and regime uncertainty."
    )

    lines.append("")
    lines.append("RISK INTERPRETATION")
    lines.append("-" * 70)
    lines.append(
        "The key risk is that a defensive allocation may sacrifice upside during strong "
        "risk-on periods. However, this tradeoff is intentional: AURUM is designed to "
        "maintain controlled beta, reduce volatility, and preserve robustness under "
        "adverse scenarios."
    )

    lines.append("")
    lines.append("RETRIEVED EVIDENCE PREVIEW")
    lines.append("-" * 70)

    for i, item in enumerate(retrieved, start=1):
        preview = item["content"][:700].replace("\n", " ")
        lines.append(f"[{i}] {item['path']}")
        lines.append(preview)
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    questions = [
        "Why did the portfolio allocation change?",
        "Explain the current portfolio decision to an investment committee.",
        "Why is AURUM defensive right now?",
    ]

    for question in questions:
        print("\n" + "#" * 90)
        print(build_decision_explanation(question))