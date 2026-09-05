from __future__ import annotations

import json
from typing import Any, Dict

from src.research.ai_agent_base import BaseAIResearchAgent
from src.research.digital_twin_agent import DigitalTwinAgent


class AIDigitalTwinAgent(BaseAIResearchAgent):
    """
    True AI Digital Twin Agent.

    Uses DigitalTwinAgent as the analytics/tool layer, then asks an LLM
    to reason like a forward-looking scenario strategist.
    """

    ai_agent_name = "ai_digital_twin_agent"

    def source_agent_output(self) -> Dict[str, Any]:
        return DigitalTwinAgent().run()

    def system_prompt(self) -> str:
        return """
You are an institutional digital twin strategist for AURUM.

You are not a rule engine.
You are an AI scenario analyst.

Your job:
- interpret live state, risk projection, stress tests, contagion, Monte Carlo, replay, and regime transition outputs
- identify the most likely future path
- identify the worst plausible case
- compare simulated risk with historical replay risk
- identify contradictions across forward-looking and historical evidence
- recommend whether the portfolio should hold, hedge, reduce risk, or prepare contingency action

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

        assessment = analysis.get("future_risk_assessment", "unknown")
        score = analysis.get("future_risk_score", 0.5)

        return {
            "thesis": f"Digital twin future risk appears {assessment}.",
            "evidence": [
                f"Future risk score is {score}.",
                f"Most likely case: {analysis.get('most_likely_case', 'unknown')}",
                f"Worst case: {analysis.get('worst_case', 'unknown')}",
                f"Survival probability is {analysis.get('survival_probability', 'unknown')}.",
            ],
            "contradictions": [
                "This is a fallback response, so no independent LLM reasoning was performed."
            ],
            "risks": [
                "Scenario interpretation is based on deterministic scoring rather than independent AI analysis."
            ],
            "recommendation": source_output.get(
                "recommendations",
                ["Continue standard digital twin monitoring."],
            )[0],
            "confidence": 0.5,
            "decision_rationale": (
                "Fallback digital twin thesis generated from deterministic DigitalTwinAgent output."
            ),
        }


if __name__ == "__main__":
    agent = AIDigitalTwinAgent()
    result = agent.run()
    print(json.dumps(result, indent=2, default=str))