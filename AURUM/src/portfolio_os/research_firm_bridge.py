from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict
import json


RESULTS_DIR = Path("results/portfolio_os")
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


class ResearchFirmPortfolioOSBridge:
    def load_inputs(self) -> Dict:
        return {
            "research_firm": load_json("results/research_firm/ai_research_firm_mode.json"),
            "daily_research_state": load_json("results/research_firm/daily_research_firm_state.json"),
            "cio_directive": load_json("results/cio/cio_portfolio_directive.json"),
            "cio_thesis": load_json("results/cio/cio_market_thesis.json"),
            "research_rankings": load_json("results/alpha_ranking/institutional_research_rankings.json"),
            "alpha_scorecard": load_json("results/alpha_ranking/institutional_alpha_scorecard.json"),
        }

    def build_bridge(self) -> Dict:
        inputs = self.load_inputs()

        research_firm = inputs.get("research_firm", {})
        summary = research_firm.get("executive_summary", {})

        cio_directive = inputs.get("cio_directive", {})
        cio_thesis = inputs.get("cio_thesis", {})

        rankings = inputs.get("research_rankings", {})
        top_entity = rankings.get("top_entity", {}) or {}

        alpha_scorecard = inputs.get("alpha_scorecard", {})
        best_alpha = alpha_scorecard.get("best_alpha", {}) or {}

        execution_guidance = self.execution_guidance(
            cio_directive=cio_directive,
            research_firm=research_firm,
        )

        bridge = {
            "timestamp": utc_now(),
            "bridge": "research_firm_to_portfolio_os",
            "status": "complete" if research_firm.get("status") == "complete" else "degraded",
            "research_firm_status": research_firm.get("status", "unknown"),
            "cio_risk_posture": cio_directive.get("risk_posture", "unknown"),
            "cio_recommended_action": cio_directive.get("recommended_action", "unknown"),
            "cio_execution_permission": cio_directive.get("execution_permission", "unknown"),
            "cio_confidence": cio_directive.get("confidence", 0),
            "market_view": cio_thesis.get("market_view", "unknown"),
            "primary_risk": cio_thesis.get("primary_risk", summary.get("worst_portfolio_scenario", "unknown")),
            "primary_risk_impact": cio_thesis.get("primary_risk_impact", summary.get("worst_portfolio_impact", 0)),
            "top_alpha": best_alpha.get("alpha_id", summary.get("best_alpha", "unknown")),
            "top_alpha_score": best_alpha.get("institutional_score", summary.get("best_alpha_score", 0)),
            "top_research_entity": top_entity.get("entity_id", summary.get("top_ranked_research_entity", "unknown")),
            "portfolio_os_execution_guidance": execution_guidance,
            "portfolio_os_message": self.portfolio_os_message(
                cio_directive=cio_directive,
                primary_risk=cio_thesis.get("primary_risk", summary.get("worst_portfolio_scenario", "unknown")),
                top_alpha=best_alpha.get("alpha_id", summary.get("best_alpha", "unknown")),
            ),
        }

        (RESULTS_DIR / "research_firm_portfolio_os_bridge.json").write_text(
            json.dumps(bridge, indent=2),
            encoding="utf-8",
        )

        return bridge

    def execution_guidance(self, cio_directive: Dict, research_firm: Dict) -> str:
        status = research_firm.get("status", "unknown")
        permission = cio_directive.get("execution_permission", "blocked")
        action = cio_directive.get("recommended_action", "")

        if status != "complete":
            return "block_execution_until_research_firm_complete"

        if permission == "blocked":
            return "do_not_execute_use_for_research_and_governance"

        if "defensive" in action:
            return "prepare_defensive_rebalance_pending_governance"

        return "monitor_and_maintain_current_operating_posture"

    def portfolio_os_message(self, cio_directive: Dict, primary_risk: str, top_alpha: str) -> str:
        return (
            f"Research Firm intelligence recommends {cio_directive.get('recommended_action', 'unknown')} "
            f"with {cio_directive.get('risk_posture', 'unknown')} posture. "
            f"Primary risk is {primary_risk}. "
            f"Top alpha is {top_alpha}. "
            f"Execution permission remains {cio_directive.get('execution_permission', 'unknown')}."
        )


def main() -> None:
    bridge = ResearchFirmPortfolioOSBridge().build_bridge()

    print("=" * 80)
    print("AURUM PHASE 6C.1 RESEARCH FIRM → PORTFOLIO OS BRIDGE")
    print("=" * 80)
    print(f"Status:              {bridge['status']}")
    print(f"Research Firm:       {bridge['research_firm_status']}")
    print(f"CIO Risk Posture:    {bridge['cio_risk_posture']}")
    print(f"CIO Action:          {bridge['cio_recommended_action']}")
    print(f"Execution:           {bridge['cio_execution_permission']}")
    print(f"Top Alpha:           {bridge['top_alpha']}")
    print(f"Primary Risk:        {bridge['primary_risk']}")
    print(f"OS Guidance:         {bridge['portfolio_os_execution_guidance']}")
    print("=" * 80)


if __name__ == "__main__":
    main()