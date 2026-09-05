from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from src.research.digital_twin_agent import DigitalTwinAgent
from src.research.macro_agent import MacroAgent
from src.research.market_structure_agent import MarketStructureAgent
from src.research.portfolio_agent import PortfolioAgent
from src.research.regime_agent import RegimeAgent
from src.research.risk_agent import RiskAgent


class ResearchDeskOrchestrator:
    """
    AURUM AI Research Desk Orchestrator.

    Runs all specialist agents and converts their views into one
    institutional research desk recommendation.
    """

    def __init__(self) -> None:
        self.generated_at = datetime.now(timezone.utc).isoformat()
        self.output_dir = Path("results/research")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.agents = {
            "macro": MacroAgent(),
            "market_structure": MarketStructureAgent(),
            "regime": RegimeAgent(),
            "risk": RiskAgent(),
            "portfolio": PortfolioAgent(),
            "digital_twin": DigitalTwinAgent(),
        }

    def run_agents(self) -> Dict[str, Any]:
        agent_outputs: Dict[str, Any] = {}

        for name, agent in self.agents.items():
            try:
                agent_outputs[name] = {
                    "status": "success",
                    "output": agent.run(),
                }
            except Exception as exc:
                agent_outputs[name] = {
                    "status": "failed",
                    "error": str(exc),
                    "output": {},
                }

        return agent_outputs

    def synthesize(self, agent_outputs: Dict[str, Any]) -> Dict[str, Any]:
        macro = self._analysis(agent_outputs, "macro")
        market = self._analysis(agent_outputs, "market_structure")
        regime = self._analysis(agent_outputs, "regime")
        risk = self._analysis(agent_outputs, "risk")
        portfolio = self._analysis(agent_outputs, "portfolio")
        twin = self._analysis(agent_outputs, "digital_twin")

        macro_score = self._safe_float(macro.get("macro_risk_score"), 0.5)
        market_score = self._safe_float(market.get("market_structure_score"), 0.5)
        transition_risk = self._safe_float(regime.get("transition_risk"), 0.5)
        risk_score = self._safe_float(risk.get("overall_risk_score"), 0.5)
        future_risk_score = self._safe_float(twin.get("future_risk_score"), 0.5)

        portfolio_assessment = str(portfolio.get("portfolio_assessment", "watch"))
        governance_penalty = self._safe_float(portfolio.get("governance_penalty"), 0.0)
        concentration_score = self._safe_float(portfolio.get("concentration_score"), 0.5)

        desk_risk_score = round(
            self._clip(
                0.20 * macro_score
                + 0.15 * market_score
                + 0.15 * transition_risk
                + 0.25 * risk_score
                + 0.15 * future_risk_score
                + 0.10 * governance_penalty
            ),
            4,
        )

        overall_market_view = self._overall_market_view(
            macro=macro,
            market=market,
            regime=regime,
            twin=twin,
        )

        highest_priority_risk = self._highest_priority_risk(
            governance_penalty=governance_penalty,
            concentration_score=concentration_score,
            risk_score=risk_score,
            market_score=market_score,
            future_risk_score=future_risk_score,
            transition_risk=transition_risk,
        )

        recommended_posture = self._recommended_posture(
            desk_risk_score=desk_risk_score,
            portfolio_assessment=portfolio_assessment,
            governance_penalty=governance_penalty,
            risk_score=risk_score,
        )

        investment_committee_view = self._investment_committee_view(
            recommended_posture=recommended_posture,
            highest_priority_risk=highest_priority_risk,
            portfolio_assessment=portfolio_assessment,
            risk_assessment=str(risk.get("risk_assessment", "moderate")),
            future_risk_assessment=str(twin.get("future_risk_assessment", "moderate")),
        )

        confidence = self._research_desk_confidence(agent_outputs)

        return {
            "overall_market_view": overall_market_view,
            "investment_committee_view": investment_committee_view,
            "recommended_posture": recommended_posture,
            "highest_priority_risk": highest_priority_risk,
            "desk_risk_score": desk_risk_score,
            "research_desk_confidence": confidence,
            "key_scores": {
                "macro_risk_score": round(macro_score, 4),
                "market_structure_score": round(market_score, 4),
                "regime_transition_risk": round(transition_risk, 4),
                "risk_score": round(risk_score, 4),
                "future_risk_score": round(future_risk_score, 4),
                "governance_penalty": round(governance_penalty, 4),
                "concentration_score": round(concentration_score, 4),
            },
            "agent_headlines": self._agent_headlines(
                macro=macro,
                market=market,
                regime=regime,
                risk=risk,
                portfolio=portfolio,
                twin=twin,
            ),
        }

    def run(self) -> Dict[str, Any]:
        agent_outputs = self.run_agents()
        synthesis = self.synthesize(agent_outputs)

        result = {
            "platform": "AURUM",
            "artifact": "ai_research_desk",
            "generated_at": self.generated_at,
            "research_desk_status": self._desk_status(agent_outputs),
            "agents": agent_outputs,
            "synthesis": synthesis,
        }

        output_path = self.output_dir / "research_desk_orchestration.json"

        with output_path.open("w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str)

        return result

    def _agent_headlines(
        self,
        macro: Dict[str, Any],
        market: Dict[str, Any],
        regime: Dict[str, Any],
        risk: Dict[str, Any],
        portfolio: Dict[str, Any],
        twin: Dict[str, Any],
    ) -> Dict[str, str]:
        return {
            "macro": str(macro.get("macro_outlook", "unknown")),
            "market_structure": str(market.get("market_health", "unknown")),
            "regime": (
                f"{regime.get('current_regime', 'unknown')} "
                f"→ {regime.get('expected_next_regime', 'unknown')}"
            ),
            "risk": str(risk.get("risk_assessment", "unknown")),
            "portfolio": str(portfolio.get("portfolio_assessment", "unknown")),
            "digital_twin": str(twin.get("future_risk_assessment", "unknown")),
        }

    def _overall_market_view(
        self,
        macro: Dict[str, Any],
        market: Dict[str, Any],
        regime: Dict[str, Any],
        twin: Dict[str, Any],
    ) -> str:
        macro_view = str(macro.get("macro_outlook", "unknown"))
        market_health = str(market.get("market_health", "unknown"))
        current_regime = str(regime.get("current_regime", "unknown"))
        future_risk = str(twin.get("future_risk_assessment", "unknown"))

        return (
            f"Macro view is {macro_view}, market structure is {market_health}, "
            f"current regime is {current_regime}, and digital twin future risk is "
            f"{future_risk}."
        )

    def _highest_priority_risk(
        self,
        governance_penalty: float,
        concentration_score: float,
        risk_score: float,
        market_score: float,
        future_risk_score: float,
        transition_risk: float,
    ) -> str:
        candidates = {
            "governance_block": governance_penalty,
            "concentration_risk": concentration_score,
            "portfolio_risk": risk_score,
            "market_structure_risk": market_score,
            "future_scenario_risk": future_risk_score,
            "regime_transition_risk": transition_risk,
        }

        top_name = max(candidates.items(), key=lambda item: item[1])[0]

        labels = {
            "governance_block": "Governance block / execution approval failure",
            "concentration_risk": "High portfolio concentration",
            "portfolio_risk": "Elevated portfolio tail risk",
            "market_structure_risk": "Weak market structure",
            "future_scenario_risk": "Adverse digital twin scenario risk",
            "regime_transition_risk": "Regime transition instability",
        }

        return labels.get(top_name, "Unknown risk")

    def _recommended_posture(
        self,
        desk_risk_score: float,
        portfolio_assessment: str,
        governance_penalty: float,
        risk_score: float,
    ) -> str:
        if governance_penalty >= 0.75 or portfolio_assessment == "blocked":
            return "execution_blocked_governance_review_required"

        if desk_risk_score >= 0.75 or risk_score >= 0.75:
            return "defensive_capital_preservation"

        if desk_risk_score >= 0.60 or risk_score >= 0.60:
            return "cautiously_defensive"

        if desk_risk_score >= 0.40:
            return "neutral_risk_controlled"

        return "constructive_normal_risk"

    def _investment_committee_view(
        self,
        recommended_posture: str,
        highest_priority_risk: str,
        portfolio_assessment: str,
        risk_assessment: str,
        future_risk_assessment: str,
    ) -> str:
        if recommended_posture == "execution_blocked_governance_review_required":
            return (
                "The research desk does not recommend execution. Portfolio status is "
                f"{portfolio_assessment}, with highest priority risk identified as "
                f"{highest_priority_risk}. Governance review is required before action."
            )

        return (
            f"The research desk recommends {recommended_posture}. Current portfolio "
            f"risk is {risk_assessment}, digital twin future risk is "
            f"{future_risk_assessment}, and the highest priority risk is "
            f"{highest_priority_risk}."
        )

    def _research_desk_confidence(self, agent_outputs: Dict[str, Any]) -> float:
        successful_agents = sum(
            1 for payload in agent_outputs.values()
            if payload.get("status") == "success"
        )

        base_confidence = successful_agents / max(1, len(agent_outputs))

        signal_quality_scores: List[float] = []

        for payload in agent_outputs.values():
            output = payload.get("output", {})
            analysis = output.get("analysis", {}) if isinstance(output, dict) else {}

            quality = (
                analysis.get("macro_signal_quality")
                or analysis.get("market_structure_signal_quality")
                or analysis.get("source_quality")
                or analysis.get("risk_signal_quality")
                or analysis.get("portfolio_signal_quality")
                or analysis.get("digital_twin_signal_quality")
            )

            signal_quality_scores.append(self._quality_to_score(str(quality)))

        if signal_quality_scores:
            quality_confidence = sum(signal_quality_scores) / len(signal_quality_scores)
        else:
            quality_confidence = 0.5

        return round(
            self._clip(0.60 * base_confidence + 0.40 * quality_confidence),
            4,
        )

    @staticmethod
    def _quality_to_score(quality: str) -> float:
        lowered = quality.lower()

        if lowered == "high":
            return 1.0

        if lowered == "medium":
            return 0.75

        if lowered == "low":
            return 0.50

        if lowered == "fallback":
            return 0.25

        return 0.50

    def _desk_status(self, agent_outputs: Dict[str, Any]) -> str:
        failures = [
            name for name, payload in agent_outputs.items()
            if payload.get("status") != "success"
        ]

        if not failures:
            return "complete"

        if len(failures) <= 2:
            return "partial"

        return "failed"

    @staticmethod
    def _analysis(
        agent_outputs: Dict[str, Any],
        name: str,
    ) -> Dict[str, Any]:
        payload = agent_outputs.get(name, {})
        output = payload.get("output", {})

        if not isinstance(output, dict):
            return {}

        analysis = output.get("analysis", {})

        if not isinstance(analysis, dict):
            return {}

        return analysis

    @staticmethod
    def _safe_float(value: Any, default: float) -> float:
        try:
            if value is None:
                return default
            return float(value)
        except Exception:
            return default

    @staticmethod
    def _clip(value: float) -> float:
        return max(0.0, min(1.0, float(value)))


if __name__ == "__main__":
    orchestrator = ResearchDeskOrchestrator()
    result = orchestrator.run()

    print(json.dumps(result["synthesis"], indent=2, default=str))
    print()
    print("Saved: results/research/research_desk_orchestration.json")