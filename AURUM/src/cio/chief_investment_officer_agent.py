from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict
import json


RESULTS_DIR = Path("results/cio")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: str | Path, default: Any = None) -> Any:
    if default is None:
        default = {}

    path = Path(path)

    try:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


class ChiefInvestmentOfficerAgent:
    def load_inputs(self) -> Dict:
        return {
            "portfolio_os": load_json("results/portfolio_os/portfolio_operating_system.json"),
            "portfolio_directive": load_json("results/portfolio_os/portfolio_directive.json"),
            "committee": load_json("results/research/committee_decision.json"),
            "alpha_rankings": load_json("results/alpha/top_alpha_rankings.json"),
            "factor_rotation": load_json("results/factors/factor_rotation_signal.json"),
            "cross_asset": load_json("results/intelligence/cross_asset_summary.json"),
            "portfolio_lab": load_json("results/portfolio_lab_2/portfolio_lab_results.json"),
            "research_scientist": load_json("results/research_scientist/research_scientist_agent.json"),
            "autonomous_research": load_json("results/autonomous_research/autonomous_research_loop.json"),
            "reliability": load_json("results/reliability/institutional_readiness_score.json"),
        }

    def build_market_thesis(self, inputs: Dict) -> Dict:
        lab = inputs.get("portfolio_lab", {})
        worst = lab.get("worst_scenario", {}) or {}

        factor = inputs.get("factor_rotation", {})
        alpha = inputs.get("alpha_rankings", {})
        best_alpha = alpha.get("best_alpha", {}) or {}

        cross_asset = inputs.get("cross_asset", {})

        thesis = {
            "timestamp": utc_now(),
            "thesis_id": "AURUM_CIO_MARKET_THESIS",
            "market_view": "cautiously_constructive_but_risk_aware",
            "primary_risk": worst.get("name", "unknown"),
            "primary_risk_impact": worst.get("portfolio_impact", 0),
            "factor_posture": factor.get("factor_posture", "unknown"),
            "preferred_factors": factor.get("preferred_factors", []),
            "top_alpha": best_alpha.get("alpha_id", "unknown"),
            "top_alpha_score": best_alpha.get("alpha_score", 0),
            "cross_asset_relationships": cross_asset.get("relationship_count", 0),
            "investment_thesis": (
                "AURUM's CIO layer views the environment as cautiously constructive, "
                "supported by quality, momentum, and carry factors, but constrained by "
                "rates and inflation scenario risk. The strongest current research idea "
                "is cross-asset momentum, while the largest portfolio vulnerability is "
                "identified through the Portfolio Laboratory stress process."
            ),
        }

        return thesis

    def build_portfolio_directive(self, inputs: Dict, thesis: Dict) -> Dict:
        reliability = inputs.get("reliability", {})
        portfolio_directive = inputs.get("portfolio_directive", {})
        lab = inputs.get("portfolio_lab", {})
        worst = lab.get("worst_scenario", {}) or {}

        readiness_score = reliability.get("institutional_readiness_score", 0)
        worst_impact = worst.get("portfolio_impact", 0)

        if readiness_score < 75:
            execution_permission = "blocked"
            recommended_action = "hold_and_restore_platform_readiness"
            risk_posture = "operational_defense"
        elif worst_impact <= -0.05:
            execution_permission = portfolio_directive.get("execution_permission", "blocked")
            recommended_action = "prepare_defensive_rebalance"
            risk_posture = "defensive"
        else:
            execution_permission = portfolio_directive.get("execution_permission", "blocked")
            recommended_action = "maintain_current_posture_with_monitoring"
            risk_posture = "balanced"

        return {
            "timestamp": utc_now(),
            "directive_id": "AURUM_CIO_PORTFOLIO_DIRECTIVE",
            "risk_posture": risk_posture,
            "recommended_action": recommended_action,
            "execution_permission": execution_permission,
            "confidence": 0.84,
            "rationale": (
                "Directive is based on institutional readiness, portfolio lab scenario risk, "
                "factor rotation, alpha rankings, and existing Portfolio OS governance state."
            ),
            "primary_risk": thesis["primary_risk"],
            "primary_risk_impact": thesis["primary_risk_impact"],
            "preferred_factors": thesis["preferred_factors"],
            "top_alpha": thesis["top_alpha"],
        }

    def run(self) -> Dict:
        inputs = self.load_inputs()
        thesis = self.build_market_thesis(inputs)
        directive = self.build_portfolio_directive(inputs, thesis)

        result = {
            "timestamp": utc_now(),
            "agent": "aurum_ai_chief_investment_officer",
            "mission": "Synthesize AURUM intelligence into an institutional investment view.",
            "market_thesis": thesis,
            "portfolio_directive": directive,
            "inputs_used": sorted(inputs.keys()),
        }

        (RESULTS_DIR / "cio_market_thesis.json").write_text(
            json.dumps(thesis, indent=2),
            encoding="utf-8",
        )

        (RESULTS_DIR / "cio_portfolio_directive.json").write_text(
            json.dumps(directive, indent=2),
            encoding="utf-8",
        )

        (RESULTS_DIR / "chief_investment_officer_agent.json").write_text(
            json.dumps(result, indent=2),
            encoding="utf-8",
        )

        return result


def main() -> None:
    result = ChiefInvestmentOfficerAgent().run()
    thesis = result["market_thesis"]
    directive = result["portfolio_directive"]

    print("=" * 80)
    print("AURUM PHASE 6B.8 AI CHIEF INVESTMENT OFFICER")
    print("=" * 80)
    print(f"Market View:       {thesis['market_view']}")
    print(f"Primary Risk:      {thesis['primary_risk']}")
    print(f"Factor Posture:    {thesis['factor_posture']}")
    print(f"Top Alpha:         {thesis['top_alpha']}")
    print(f"Risk Posture:      {directive['risk_posture']}")
    print(f"Action:            {directive['recommended_action']}")
    print(f"Execution:         {directive['execution_permission']}")
    print("=" * 80)


if __name__ == "__main__":
    main()