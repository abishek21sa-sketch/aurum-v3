from __future__ import annotations

import json
from typing import Any, Dict

from src.research.ai_agent_base import BaseAIResearchAgent
from src.research.market_structure_agent import MarketStructureAgent


class AIMarketStructureAgent(BaseAIResearchAgent):
    ai_agent_name = "ai_market_structure_agent"

    def source_agent_output(self) -> Dict[str, Any]:
        return MarketStructureAgent().run()

    def system_prompt(self) -> str:
        return """
You are an institutional market structure analyst for AURUM.

Analyze breadth, volatility, liquidity, dispersion, and cross-asset correlations.
Identify whether the market structure supports risk-taking or warns of fragility.

Return ONLY valid JSON:

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
        return {
            "thesis": f"Market structure appears {analysis.get('market_health', 'unknown')}.",
            "evidence": [
                f"Market structure score is {analysis.get('market_structure_score', 'unknown')}.",
                f"Liquidity score is {analysis.get('liquidity_score', 'unknown')}.",
                f"Correlation regime is {analysis.get('correlation_regime', 'unknown')}.",
            ],
            "contradictions": [
                "Fallback response only; no independent LLM reasoning was performed."
            ],
            "risks": [
                "Market structure interpretation is based on deterministic scoring."
            ],
            "recommendation": source_output.get(
                "recommendations",
                ["Maintain normal market structure monitoring."],
            )[0],
            "confidence": 0.5,
            "decision_rationale": "Fallback market structure thesis generated from deterministic output.",
        }


if __name__ == "__main__":
    agent = AIMarketStructureAgent()
    result = agent.run()
    print(json.dumps(result, indent=2, default=str))