from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List
import json

from src.universe.asset_universe import AssetUniverse
from src.intelligence.cross_asset_engine import CrossAssetIntelligenceEngine
from src.factors.factor_engine import InstitutionalFactorEngine
from src.alpha.alpha_factory import AlphaFactory
from src.research_scientist.research_scientist_agent import ResearchScientistAgent
from src.autonomous_research.autonomous_research_loop import AutonomousResearchLoop
from src.portfolio_lab_2.portfolio_lab_engine import PortfolioLabEngine
from src.cio.chief_investment_officer_agent import ChiefInvestmentOfficerAgent
from src.alpha_ranking.alpha_scorecard import InstitutionalAlphaScorecard
from src.alpha_ranking.strategy_ranker import StrategyRanker


RESULTS_DIR = Path("results/research_firm")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AIResearchFirmMode:
    def run(self) -> Dict:
        stages: List[Dict] = []

        universe_summary = AssetUniverse().save()
        stages.append(self.stage("multi_asset_universe", "complete", universe_summary))

        cross_asset_summary = CrossAssetIntelligenceEngine().run()
        stages.append(self.stage("cross_asset_intelligence", "complete", cross_asset_summary))

        factor_result = InstitutionalFactorEngine().run(regime="normal")
        stages.append(self.stage("factor_platform", "complete", factor_result["rotation"]))

        alpha_result = AlphaFactory().run()
        stages.append(self.stage("alpha_factory", "complete", alpha_result["rankings"]))

        scientist_result = ResearchScientistAgent().run()
        stages.append(self.stage("research_scientist", "complete", scientist_result))

        research_loop = AutonomousResearchLoop().run()
        stages.append(self.stage("autonomous_research_loop", "complete", research_loop["learning_summary"]))

        portfolio_lab = PortfolioLabEngine().run()
        stages.append(self.stage("portfolio_lab_2", "complete", portfolio_lab))

        cio_result = ChiefInvestmentOfficerAgent().run()
        stages.append(self.stage("ai_cio", "complete", cio_result["portfolio_directive"]))

        alpha_scorecard = InstitutionalAlphaScorecard().build_scorecard()
        stages.append(self.stage("institutional_alpha_scorecard", "complete", alpha_scorecard))

        research_rankings = StrategyRanker().build_rankings()
        stages.append(self.stage("institutional_research_rankings", "complete", research_rankings))

        firm_state = {
            "timestamp": utc_now(),
            "mode": "AURUM_AI_RESEARCH_FIRM_MODE",
            "status": "complete",
            "stage_count": len(stages),
            "stages": stages,
            "executive_summary": self.executive_summary(
                universe_summary=universe_summary,
                alpha_result=alpha_result,
                scientist_result=scientist_result,
                portfolio_lab=portfolio_lab,
                cio_result=cio_result,
                rankings=research_rankings,
            ),
        }

        (RESULTS_DIR / "ai_research_firm_mode.json").write_text(
            json.dumps(firm_state, indent=2),
            encoding="utf-8",
        )

        (RESULTS_DIR / "daily_research_firm_state.json").write_text(
            json.dumps(firm_state, indent=2),
            encoding="utf-8",
        )

        return firm_state

    def stage(self, name: str, status: str, output: Dict) -> Dict:
        return {
            "stage": name,
            "status": status,
            "timestamp": utc_now(),
            "output_summary": self.compact_summary(output),
        }

    def compact_summary(self, payload: Dict) -> Dict:
        keys = [
            "asset_count",
            "relationship_count",
            "factor_posture",
            "alpha_count",
            "hypothesis_count",
            "experiment_count",
            "scenario_count",
            "risk_posture",
            "recommended_action",
            "entity_count",
            "institutional_readiness_score",
        ]

        summary = {}

        for key in keys:
            if key in payload:
                summary[key] = payload[key]

        if "best_alpha" in payload and payload["best_alpha"]:
            summary["best_alpha"] = payload["best_alpha"].get("alpha_id")

        if "worst_scenario" in payload and payload["worst_scenario"]:
            summary["worst_scenario"] = payload["worst_scenario"].get("scenario_id")
            summary["worst_impact"] = payload["worst_scenario"].get("portfolio_impact")

        if "top_entity" in payload and payload["top_entity"]:
            summary["top_entity"] = payload["top_entity"].get("entity_id")

        return summary

    def executive_summary(
        self,
        universe_summary: Dict,
        alpha_result: Dict,
        scientist_result: Dict,
        portfolio_lab: Dict,
        cio_result: Dict,
        rankings: Dict,
    ) -> Dict:
        best_alpha = alpha_result["rankings"].get("best_alpha", {}) or {}
        worst_scenario = portfolio_lab.get("worst_scenario", {}) or {}
        directive = cio_result.get("portfolio_directive", {})
        top_entity = rankings.get("top_entity", {}) or {}

        return {
            "timestamp": utc_now(),
            "firm_view": "research_active_risk_governed",
            "asset_universe_size": universe_summary.get("asset_count"),
            "best_alpha": best_alpha.get("alpha_id"),
            "best_alpha_score": best_alpha.get("alpha_score"),
            "hypotheses_generated": scientist_result["research_hypotheses"]["hypothesis_count"],
            "worst_portfolio_scenario": worst_scenario.get("name"),
            "worst_portfolio_impact": worst_scenario.get("portfolio_impact"),
            "cio_recommended_action": directive.get("recommended_action"),
            "cio_risk_posture": directive.get("risk_posture"),
            "top_ranked_research_entity": top_entity.get("entity_id"),
            "interpretation": (
                "AURUM is operating as an AI Research Firm: it maintains a multi-asset universe, "
                "maps cross-asset relationships, ranks factors and alphas, generates hypotheses, "
                "runs autonomous research loops, stress-tests the portfolio, and synthesizes a CIO directive."
            ),
        }


def main() -> None:
    state = AIResearchFirmMode().run()
    summary = state["executive_summary"]

    print("=" * 80)
    print("AURUM PHASE 6B.10 AI RESEARCH FIRM MODE")
    print("=" * 80)
    print(f"Status:              {state['status']}")
    print(f"Stages:              {state['stage_count']}")
    print(f"Universe Size:       {summary['asset_universe_size']}")
    print(f"Best Alpha:          {summary['best_alpha']}")
    print(f"Hypotheses:          {summary['hypotheses_generated']}")
    print(f"Worst Scenario:      {summary['worst_portfolio_scenario']}")
    print(f"CIO Action:          {summary['cio_recommended_action']}")
    print(f"CIO Risk Posture:    {summary['cio_risk_posture']}")
    print(f"Top Research Entity: {summary['top_ranked_research_entity']}")
    print("-" * 80)
    print(summary["interpretation"])
    print("=" * 80)


if __name__ == "__main__":
    main()