from __future__ import annotations

import json
from typing import Any, Dict

from src.research.ai_agent_base import BaseAIResearchAgent
from src.research.regime_agent import RegimeAgent


class AIRegimeAgent(BaseAIResearchAgent):
    ai_agent_name = "ai_regime_agent"

    def source_agent_output(self) -> Dict[str, Any]:
        return RegimeAgent().run()

    def system_prompt(self) -> str:
        return """
You are an institutional regime strategist for AURUM.

Analyze current regime, expected next regime, regime confidence, transition risk,
stability, and live market state. Identify whether allocation should trust the
current regime or prepare for transition.

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
            "thesis": (
                f"Current regime is {analysis.get('current_regime', 'unknown')} "
                f"with expected next regime {analysis.get('expected_next_regime', 'unknown')}."
            ),
            "evidence": [
                f"Regime confidence is {analysis.get('regime_confidence', 'unknown')}.",
                f"Transition risk is {analysis.get('transition_risk', 'unknown')}.",
                f"Regime stability is {analysis.get('regime_stability', 'unknown')}.",
            ],
            "contradictions": [
                "Fallback response only; no independent LLM reasoning was performed."
            ],
            "risks": [
                "Regime interpretation is based on deterministic scoring."
            ],
            "recommendation": source_output.get(
                "recommendations",
                ["Maintain regime-aligned positioning."],
            )[0],
            "confidence": 0.5,
            "decision_rationale": "Fallback regime thesis generated from deterministic output.",
        }


if __name__ == "__main__":
    agent = AIRegimeAgent()
    result = agent.run()
    print(json.dumps(result, indent=2, default=str))