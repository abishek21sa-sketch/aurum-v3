from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from src.research.llm_client import AURUMLLMClient

from src.research.ai_macro_agent import AIMacroAgent
from src.research.ai_market_structure_agent import AIMarketStructureAgent
from src.research.ai_regime_agent import AIRegimeAgent
from src.research.ai_risk_agent import AIRiskAgent
from src.research.ai_portfolio_agent import AIPortfolioAgent
from src.research.ai_digital_twin_agent import AIDigitalTwinAgent


class AIResearchCommittee:
    """
    AURUM AI Research Committee.

    Runs true AI analyst agents and synthesizes them into one
    institutional investment committee decision.
    """

    def __init__(self) -> None:
        self.generated_at = datetime.now(timezone.utc).isoformat()
        self.output_dir = Path("results/research")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.output_path = self.output_dir / "ai_research_committee.json"
        self.llm = AURUMLLMClient()

        self.agents = {
            "macro": AIMacroAgent(),
            "market_structure": AIMarketStructureAgent(),
            "regime": AIRegimeAgent(),
            "risk": AIRiskAgent(),
            "portfolio": AIPortfolioAgent(),
            "digital_twin": AIDigitalTwinAgent(),
        }

    def run_agents(self) -> Dict[str, Any]:
        results: Dict[str, Any] = {}

        for name, agent in self.agents.items():
            try:
                results[name] = {
                    "status": "success",
                    "output": agent.run(),
                }
            except Exception as exc:
                results[name] = {
                    "status": "failed",
                    "error": str(exc),
                    "output": {},
                }

        return results

    def system_prompt(self) -> str:
        return """
You are the AURUM AI Investment Committee.

You receive reports from:
- AI Macro Analyst
- AI Market Structure Analyst
- AI Regime Strategist
- AI Risk Officer
- AI Portfolio Manager
- AI Digital Twin Strategist

Your job:
- compare the analyst reports
- identify consensus
- identify disagreements
- identify the binding constraint
- produce bull case, bear case, base case
- make a final committee recommendation
- decide whether execution is allowed, blocked, hedged, or requires review

Return ONLY valid JSON:

{
  "committee_decision": "...",
  "execution_permission": "allowed | blocked | review_required | hedge_only",
  "base_case": "...",
  "bull_case": "...",
  "bear_case": "...",
  "key_disagreements": ["...", "..."],
  "binding_constraint": "...",
  "risk_controls": ["...", "..."],
  "final_recommendation": "...",
  "committee_confidence": 0.0,
  "decision_rationale": "..."
}
"""

    def fallback_response(self, analyst_outputs: Dict[str, Any]) -> Dict[str, Any]:
        portfolio = self._ai_analysis(analyst_outputs, "portfolio")
        risk = self._ai_analysis(analyst_outputs, "risk")
        twin = self._ai_analysis(analyst_outputs, "digital_twin")

        portfolio_text = json.dumps(portfolio, default=str).upper()

        if "BLOCK" in portfolio_text or "NON_COMPLIANT" in portfolio_text:
            permission = "blocked"
            decision = "Execution blocked pending governance review."
            binding = "Governance and compliance block"
        else:
            permission = "review_required"
            decision = "Committee review required before execution."
            binding = "Unresolved risk committee review"

        return {
            "committee_decision": decision,
            "execution_permission": permission,
            "base_case": "Fallback committee decision based on AI analyst summaries.",
            "bull_case": "Macro and digital twin evidence may support stable continuation.",
            "bear_case": "Risk, concentration, governance, or stress-test evidence may dominate.",
            "key_disagreements": [
                "Fallback response only; no independent LLM committee reasoning was performed."
            ],
            "binding_constraint": binding,
            "risk_controls": [
                "Do not execute while governance is blocked.",
                "Review risk and portfolio AI agent recommendations.",
            ],
            "final_recommendation": decision,
            "committee_confidence": 0.5,
            "decision_rationale": (
                "Fallback committee response generated from available AI analyst outputs."
            ),
            "llm_mode": "fallback",
            "risk_reference": risk.get("thesis", ""),
            "digital_twin_reference": twin.get("thesis", ""),
        }

    def synthesize(self, analyst_outputs: Dict[str, Any]) -> Dict[str, Any]:
        payload = {
            "generated_at": self.generated_at,
            "analyst_outputs": analyst_outputs,
            "required_decision_context": {
                "must_respect_governance_blocks": True,
                "must_surface_disagreements": True,
                "must_not_hide_model_or_data_quality_issues": True,
            },
        }

        return self.llm.generate_json(
            system_prompt=self.system_prompt(),
            user_payload=payload,
            fallback=self.fallback_response(analyst_outputs),
        )

    def run(self) -> Dict[str, Any]:
        analyst_outputs = self.run_agents()
        committee_analysis = self.synthesize(analyst_outputs)

        result = {
            "platform": "AURUM",
            "artifact": "ai_research_committee",
            "generated_at": self.generated_at,
            "analyst_outputs": analyst_outputs,
            "committee_analysis": committee_analysis,
        }

        with self.output_path.open("w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str)

        return result

    @staticmethod
    def _ai_analysis(outputs: Dict[str, Any], name: str) -> Dict[str, Any]:
        payload = outputs.get(name, {})
        output = payload.get("output", {})

        if not isinstance(output, dict):
            return {}

        analysis = output.get("ai_analysis", {})

        if not isinstance(analysis, dict):
            return {}

        return analysis


if __name__ == "__main__":
    committee = AIResearchCommittee()
    result = committee.run()

    print(json.dumps(result["committee_analysis"], indent=2, default=str))
    print()
    print("Saved: results/research/ai_research_committee.json")