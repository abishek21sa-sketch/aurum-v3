from __future__ import annotations

import json
from typing import Any, Dict

from src.research.ai_agent_base import BaseAIResearchAgent
from src.research.portfolio_agent import PortfolioAgent


class AIPortfolioAgent(BaseAIResearchAgent):
    """
    True AI Portfolio Agent.

    Uses PortfolioAgent as the analytics/tool layer, then asks an LLM
    to reason like an institutional portfolio manager.
    """

    ai_agent_name = "ai_portfolio_agent"

    def source_agent_output(self) -> Dict[str, Any]:
        return PortfolioAgent().run()

    def system_prompt(self) -> str:
        return """
You are an institutional portfolio manager for AURUM.

You are not a rule engine.
You are an AI portfolio analyst.

Your job:
- interpret portfolio state, optimized allocation, governance status, drift, concentration, and execution readiness
- identify the most important portfolio constraint
- identify contradictions between portfolio health, concentration, and governance
- determine whether the portfolio should hold, rebalance, reduce risk, hedge, or remain blocked
- explain your decision like an investment committee memo

Return ONLY valid JSON with this schema:

{
  "thesis": "...",
  "evidence": ["...", "..."],
  "contradictions": ["...", "..."],
  "risks": ["...", "..."],
  "recommendation": "...",
  "confidence": 0.0,
  "decision_rationale": "..."
}
"""

    def fallback_response(self, source_output: Dict[str, Any]) -> Dict[str, Any]:
        analysis = source_output.get("analysis", {})

        assessment = analysis.get("portfolio_assessment", "unknown")
        score = analysis.get("portfolio_score", 0.5)

        return {
            "thesis": f"Portfolio status is {assessment}.",
            "evidence": [
                f"Portfolio score is {score}.",
                f"Concentration risk is {analysis.get('concentration_risk', 'unknown')}.",
                f"Governance approval is {analysis.get('approval_decision', 'unknown')}.",
                f"Compliance status is {analysis.get('compliance_status', 'unknown')}.",
            ],
            "contradictions": [
                "This is a fallback response, so no independent LLM reasoning was performed."
            ],
            "risks": [
                "Portfolio interpretation is based on deterministic scoring rather than independent AI analysis."
            ],
            "recommendation": source_output.get(
                "recommendations",
                ["Keep portfolio under review."],
            )[0],
            "confidence": 0.5,
            "decision_rationale": (
                "Fallback portfolio thesis generated from deterministic PortfolioAgent output."
            ),
        }


if __name__ == "__main__":
    agent = AIPortfolioAgent()
    result = agent.run()
    print(json.dumps(result, indent=2, default=str))