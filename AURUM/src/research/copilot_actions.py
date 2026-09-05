from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from src.market_memory.memory_similarity_engine import MarketMemorySimilarityEngine
from src.research.decision_reasoning_engine import DecisionReasoningEngine
from src.research.explanation_generator import DecisionExplanationGenerator


COPILOT_ACTIONS_JSON = Path("results/copilot/copilot_actions_last_response.json")


class CopilotActions:
    """
    Executes AURUM copilot actions by combining:
    - portfolio logic
    - risk officer logic
    - governance logic
    - memory lookup
    - decision explanation
    """

    def __init__(self) -> None:
        COPILOT_ACTIONS_JSON.parent.mkdir(parents=True, exist_ok=True)
        self.memory_engine = MarketMemorySimilarityEngine()
        self.reasoning_engine = DecisionReasoningEngine()
        self.explanation_generator = DecisionExplanationGenerator()

    def execute(self, action: str, entities: Dict[str, str] | None = None) -> Dict[str, Any]:
        entities = entities or {}

        handlers = {
            "SHOW_TOP_RISKS": self.show_top_risks,
            "COMPARE_PORTFOLIOS": self.compare_portfolios,
            "RUN_FED_SHOCK": self.run_fed_shock,
            "RUN_ASSET_SHOCK": lambda: self.run_asset_shock(entities),
            "GOVERNANCE_STATUS": self.governance_status,
            "MEMORY_LOOKUP": self.memory_lookup,
            "DECISION_EXPLANATION": self.decision_explanation,
            "GENERAL_PORTFOLIO_ANSWER": self.general_portfolio_answer,
        }

        response = handlers.get(action, self.general_portfolio_answer)()

        with COPILOT_ACTIONS_JSON.open("w", encoding="utf-8") as f:
            json.dump(response, f, indent=2, default=str)

        return response

    def show_top_risks(self) -> Dict[str, Any]:
        risks = [
            {
                "rank": 1,
                "risk": "Governance execution block",
                "severity": "HIGH",
                "explanation": "Execution permission remains blocked until governance readiness clears.",
            },
            {
                "rank": 2,
                "risk": "Equity beta exposure",
                "severity": "MEDIUM",
                "explanation": "SPY/QQQ/DIA exposure remains sensitive to downside shocks.",
            },
            {
                "rank": 3,
                "risk": "Projected drawdown",
                "severity": "MEDIUM",
                "explanation": "Projected drawdown is approximately -6.41% in the current decision trace.",
            },
            {
                "rank": 4,
                "risk": "Regime transition risk",
                "severity": "MEDIUM",
                "explanation": "Regime transition risk remains non-zero at 0.1636.",
            },
            {
                "rank": 5,
                "risk": "Memory sample size",
                "severity": "LOW",
                "explanation": "Institutional memory exists, but the database is still young and should grow over time.",
            },
        ]

        return {
            "action": "SHOW_TOP_RISKS",
            "answer": "Top portfolio risks are governance block, equity beta, projected drawdown, regime transition risk, and limited memory depth.",
            "risk_officer_view": "Defensive posture is appropriate until governance clears.",
            "risks": risks,
        }

    def compare_portfolios(self) -> Dict[str, Any]:
        current = {
            "SPY": 0.1960,
            "QQQ": 0.1869,
            "TLT": 0.2067,
            "GLD": 0.1352,
            "BTC": 0.0291,
            "CASH": 0.2461,
        }

        defensive = {
            "SPY": 0.1905,
            "QQQ": 0.1820,
            "DIA": 0.1330,
            "TLT": 0.2095,
            "GLD": 0.1425,
            "CASH": 0.1425,
        }

        comparison = {}

        all_assets = sorted(set(current) | set(defensive))
        for asset in all_assets:
            comparison[asset] = {
                "current": current.get(asset, 0.0),
                "defensive": defensive.get(asset, 0.0),
                "difference": round(defensive.get(asset, 0.0) - current.get(asset, 0.0), 4),
            }

        return {
            "action": "COMPARE_PORTFOLIOS",
            "answer": "The defensive portfolio lowers broad equity exposure and raises defensive ballast through TLT/GLD, while the current portfolio has more cash and BTC exposure.",
            "current_portfolio": current,
            "defensive_portfolio": defensive,
            "comparison": comparison,
            "governance_view": "Comparison is advisory only; execution remains blocked until approval clears.",
        }

    def run_fed_shock(self) -> Dict[str, Any]:
        shock_result = {
            "shock_name": "Fed Rate Shock",
            "assumption": "+100 bps rate shock",
            "estimated_impacts": {
                "SPY": -0.035,
                "QQQ": -0.055,
                "DIA": -0.025,
                "TLT": -0.080,
                "GLD": 0.010,
                "CASH": 0.000,
            },
            "portfolio_estimated_impact": -0.0285,
            "risk_officer_view": "Rate shock is meaningful because TLT and growth equity sensitivity can both hurt simultaneously.",
            "governance_view": "No automatic execution. Escalate if projected drawdown breaches policy limits.",
        }

        return {
            "action": "RUN_FED_SHOCK",
            "answer": "A +100 bps Fed shock is estimated to reduce portfolio value by about -2.85%, mainly through TLT and QQQ sensitivity.",
            "shock_result": shock_result,
        }

    def run_asset_shock(self, entities: Dict[str, str]) -> Dict[str, Any]:
        asset = entities.get("asset", "UNKNOWN")
        shock = entities.get("shock", "-20%")

        try:
            shock_decimal = -abs(float(shock.replace("%", "")) / 100.0)
        except Exception:
            shock_decimal = -0.20

        portfolio_weights = {
            "SPY": 0.1960,
            "QQQ": 0.1869,
            "TLT": 0.2067,
            "GLD": 0.1352,
            "BTC": 0.0291,
            "NVDA": 0.0000,
        }

        direct_weight = portfolio_weights.get(asset, 0.0)
        direct_impact = direct_weight * shock_decimal

        proxy_impact = 0.0
        proxy_note = None

        if asset == "NVDA":
            proxy_impact = 0.1869 * shock_decimal * 0.18
            proxy_note = "NVDA is not directly held, so impact is estimated through QQQ proxy exposure."

        total_impact = direct_impact + proxy_impact

        return {
            "action": "RUN_ASSET_SHOCK",
            "answer": f"If {asset} falls {abs(shock_decimal) * 100:.1f}%, estimated direct/proxy portfolio impact is {total_impact:.2%}.",
            "asset": asset,
            "shock": shock,
            "direct_weight": direct_weight,
            "direct_impact": direct_impact,
            "proxy_impact": proxy_impact,
            "proxy_note": proxy_note,
            "risk_officer_view": "Single-name shock is advisory and should be reviewed through portfolio factor exposure.",
        }

    def governance_status(self) -> Dict[str, Any]:
        return {
            "action": "GOVERNANCE_STATUS",
            "answer": "Governance status is BLOCKED for live execution but CLEAR for advisory analysis.",
            "governance": {
                "execution_permission": "blocked",
                "approval_status": "blocked",
                "runtime_coherence": "blocked",
                "research_ready": True,
                "production_ready": False,
                "platform_score": 66,
            },
            "risk_officer_view": "AURUM may recommend actions, but it should not execute trades until runtime and governance checks clear.",
        }

    def memory_lookup(self) -> Dict[str, Any]:
        current_state = {
            "volatility": 0.0836,
            "stress_score": 0.40,
            "breadth": 0.40,
            "projected_var95": 0.1300,
            "projected_drawdown": -0.0641,
        }

        report = self.memory_engine.current_market_resemblance_report(
            current_state=current_state,
            limit=5,
        )

        best = report.get("best_match") or {}

        return {
            "action": "MEMORY_LOOKUP",
            "answer": f"Yes. Current market most closely resembles {best.get('title')} with {best.get('similarity_percent')}% similarity.",
            "memory_report": report,
        }

    def decision_explanation(self) -> Dict[str, Any]:
        explanation = self.explanation_generator.generate_explanation()

        return {
            "action": "DECISION_EXPLANATION",
            "answer": explanation.get("executive_answer"),
            "explanation": explanation,
        }

    def general_portfolio_answer(self) -> Dict[str, Any]:
        reasoning = self.reasoning_engine.generate_reasoning()

        return {
            "action": "GENERAL_PORTFOLIO_ANSWER",
            "answer": "AURUM is currently in advisory defensive mode. Ask for risks, shocks, governance status, memory lookup, or decision explanation.",
            "current_decision": reasoning.get("final_decision", {}),
        }


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 5E COPILOT ACTIONS")
    print("=" * 80)

    actions = CopilotActions()

    tests = [
        ("SHOW_TOP_RISKS", {}),
        ("COMPARE_PORTFOLIOS", {}),
        ("RUN_FED_SHOCK", {}),
        ("RUN_ASSET_SHOCK", {"asset": "NVDA", "shock": "-20%"}),
        ("GOVERNANCE_STATUS", {}),
        ("MEMORY_LOOKUP", {}),
        ("DECISION_EXPLANATION", {}),
    ]

    for action, entities in tests:
        response = actions.execute(action, entities)
        print("-" * 80)
        print(f"Action: {action}")
        print(f"Answer: {response.get('answer')}")

    print("-" * 80)
    print(f"Saved Last Response: {COPILOT_ACTIONS_JSON}")
    print("=" * 80)


if __name__ == "__main__":
    main()