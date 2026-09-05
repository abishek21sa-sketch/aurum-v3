from __future__ import annotations

import json
from typing import Any, Dict

from src.research.ai_agent_base import BaseAIResearchAgent
from src.research.macro_agent import MacroAgent


class AIMacroAgent(BaseAIResearchAgent):
    """
    True AI Macro Agent.

    Uses MacroAgent as the analytics/tool layer, then asks an LLM
    to reason like an institutional macro strategist.
    """

    ai_agent_name = "ai_macro_agent"

    def source_agent_output(self) -> Dict[str, Any]:
        return MacroAgent().run()

    def system_prompt(self) -> str:
        return """
You are an institutional macro strategist for AURUM.

You are not a rule engine.
You are an AI research analyst.

Your job:
- interpret the macro analytics
- identify what matters
- identify contradictions
- form a thesis
- make a recommendation
- explain your reasoning clearly

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

        outlook = analysis.get("macro_outlook", "unknown")
        score = analysis.get("macro_risk_score", 0.5)

        return {
            "thesis": f"Macro conditions appear {outlook}.",
            "evidence": [
                f"Macro risk score is {score}.",
                f"VIX pressure is {analysis.get('vix_pressure', 'unknown')}.",
                f"Risk asset momentum support is {analysis.get('risk_asset_momentum_support', 'unknown')}.",
            ],
            "contradictions": [
                "This is a fallback response, so no independent LLM reasoning was performed."
            ],
            "risks": [
                "Macro data is based on engineered proxies rather than direct CPI, Fed, and unemployment feeds."
            ],
            "recommendation": source_output.get("recommendations", ["Maintain neutral stance."])[0],
            "confidence": 0.5,
            "decision_rationale": (
                "Fallback macro thesis generated from deterministic MacroAgent output."
            ),
        }


if __name__ == "__main__":
    agent = AIMacroAgent()
    result = agent.run()
    print(json.dumps(result, indent=2, default=str))