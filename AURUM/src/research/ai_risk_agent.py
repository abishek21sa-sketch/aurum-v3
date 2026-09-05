from __future__ import annotations

import json
from typing import Any, Dict

from src.research.ai_agent_base import BaseAIResearchAgent
from src.research.risk_agent import RiskAgent


class AIRiskAgent(BaseAIResearchAgent):
    """
    True AI Risk Agent.

    Uses RiskAgent as the analytics/tool layer, then asks an LLM
    to reason like an institutional risk officer.
    """

    ai_agent_name = "ai_risk_agent"

    def source_agent_output(self) -> Dict[str, Any]:
        return RiskAgent().run()

    def system_prompt(self) -> str:
        return """
You are an institutional Chief Risk Officer for AURUM.

You are not a rule engine.
You are an AI risk analyst.

Your job:
- interpret VaR, CVaR, drawdown, stress tests, and contagion results
- identify the most important risk drivers
- identify contradictions between live risk and historical/stress risk
- form a risk thesis
- recommend risk posture
- explain whether risk should be increased, held, reduced, hedged, or blocked

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

        assessment = analysis.get("risk_assessment", "unknown")
        score = analysis.get("overall_risk_score", 0.5)

        return {
            "thesis": f"Portfolio risk appears {assessment}.",
            "evidence": [
                f"Overall risk score is {score}.",
                f"Tail risk score is {analysis.get('tail_risk_score', 'unknown')}.",
                f"Stress score is {analysis.get('stress_score', 'unknown')}.",
                f"Contagion score is {analysis.get('contagion_score', 'unknown')}.",
            ],
            "contradictions": [
                "This is a fallback response, so no independent LLM reasoning was performed."
            ],
            "risks": [
                "Risk interpretation is based on deterministic scoring rather than independent AI analysis."
            ],
            "recommendation": source_output.get(
                "recommendations",
                ["Maintain standard risk controls."],
            )[0],
            "confidence": 0.5,
            "decision_rationale": (
                "Fallback risk thesis generated from deterministic RiskAgent output."
            ),
        }


if __name__ == "__main__":
    agent = AIRiskAgent()
    result = agent.run()
    print(json.dumps(result, indent=2, default=str))