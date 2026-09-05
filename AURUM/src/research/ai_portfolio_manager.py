from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


RESULTS_DIR = Path("results/research")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str | Path, data: Dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def save_text(path: str | Path, text: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        f.write(text)


class AIPortfolioManager:
    """
    Phase 5C.

    Takes AI research + AI committee decision and converts it into an
    AI portfolio management plan.

    Important:
    - This creates recommended target weights.
    - It does NOT execute trades.
    - It respects committee execution_permission.
    """

    def __init__(self):
        from src.research.ai_investment_committee import TrueLLMClient

        self.llm = TrueLLMClient()

    def run(self) -> Dict[str, Any]:
        context = self._load_context()

        portfolio_plan = self._generate_portfolio_plan(context)

        output = {
            "generated_at": utc_now(),
            "phase": "5C",
            "component": "AI Portfolio Manager",
            "llm_backend": self.llm.backend,
            "model": self.llm.model,
            "input_sources": list(context.keys()),
            "portfolio_plan": portfolio_plan,
        }

        save_json(RESULTS_DIR / "ai_portfolio_manager_plan.json", output)
        save_json(RESULTS_DIR / "target_ai_portfolio.json", portfolio_plan)
        save_text(
            RESULTS_DIR / "ai_portfolio_manager_explanation.txt",
            self._format_explanation(output),
        )

        return output

    def _load_context(self) -> Dict[str, Any]:
        files = {
            "daily_research_packet": RESULTS_DIR / "ai_daily_research_packet.json",
            "research_committee": RESULTS_DIR / "ai_research_committee.json",
            "research_desk": RESULTS_DIR / "ai_research_desk_orchestrator.json",
            "investment_committee_minutes": RESULTS_DIR / "investment_committee_minutes.json",
            "committee_decision": RESULTS_DIR / "committee_decision.json",
            "live_market_snapshot": Path("results/realtime/live_market_snapshot.json"),
            "portfolio_state": Path("results/portfolio_state/institutional_portfolio_state.json"),
            "portfolio_operating_report": Path("results/portfolio/portfolio_operating_report.json"),
            "governance_report": Path("results/governance/governance_report.json"),
            "approval_gate": Path("results/governance/portfolio_approval_gate.json"),
            "runtime_readiness": Path("results/institutional/institutional_readiness_report.json"),
        }

        context: Dict[str, Any] = {}
        for name, path in files.items():
            if path.exists():
                context[name] = load_json(path)

        if "committee_decision" not in context:
            raise FileNotFoundError(
                "Missing results/research/committee_decision.json. Run Phase 5B first."
            )

        return context

    def _generate_portfolio_plan(self, context: Dict[str, Any]) -> Dict[str, Any]:
        system = """
You are the AURUM AI Portfolio Manager.

You are not a trade executor.
You are an institutional portfolio manager that converts AI research,
investment committee views, governance state, and portfolio state into
a target portfolio plan.

Rules:
1. Separate desired portfolio from executable portfolio.
2. If execution_permission is blocked, produce target weights as PREPARED_ONLY.
3. Do not claim trades were executed.
4. Respect governance and compliance constraints.
5. Use only the provided context.
6. Return strict JSON only.
"""

        user = f"""
AURUM context:
{json.dumps(context, indent=2)[:40000]}

Return JSON with this exact schema:
{{
  "generated_at": "{utc_now()}",
  "manager_view": "risk_on | neutral | defensive | risk_off",
  "execution_permission": "allowed | review_required | blocked",
  "portfolio_mode": "executable | prepared_only | blocked",
  "manager_confidence": 0.0,
  "current_portfolio_assessment": "...",
  "target_weights": {{
    "SPY": 0.0,
    "QQQ": 0.0,
    "DIA": 0.0,
    "TLT": 0.0,
    "GLD": 0.0,
    "BTC": 0.0,
    "ETH": 0.0,
    "VIX": 0.0,
    "CASH": 0.0
  }},
  "weight_change_recommendations": [
    {{
      "asset": "SPY/QQQ/DIA/TLT/GLD/BTC/ETH/VIX/CASH",
      "current_weight": 0.0,
      "target_weight": 0.0,
      "change": 0.0,
      "action": "increase | decrease | hold | hedge | review",
      "execution_status": "executable | prepared_only | blocked",
      "rationale": "..."
    }}
  ],
  "risk_budget": {{
    "equity_bucket": 0.0,
    "rates_bucket": 0.0,
    "commodity_bucket": 0.0,
    "crypto_bucket": 0.0,
    "cash_bucket": 0.0,
    "hedge_bucket": 0.0
  }},
  "expected_portfolio_behavior": {{
    "expected_return_direction": "higher | similar | lower | unknown",
    "expected_volatility_direction": "higher | similar | lower | unknown",
    "expected_drawdown_direction": "higher | similar | lower | unknown",
    "liquidity_profile": "strong | acceptable | weak | unknown"
  }},
  "primary_risks": ["..."],
  "required_governance_actions": ["..."],
  "execution_plan_if_cleared": ["..."],
  "do_not_execute_reason": "...",
  "executive_summary": "..."
}}
"""

        return self.llm.complete_json(system, user)

    def _format_explanation(self, output: Dict[str, Any]) -> str:
        plan = output["portfolio_plan"]

        lines = []
        lines.append("=" * 80)
        lines.append("AURUM PHASE 5C AI PORTFOLIO MANAGER")
        lines.append("=" * 80)
        lines.append(f"Generated At: {output.get('generated_at')}")
        lines.append(f"LLM Backend: {output.get('llm_backend')}")
        lines.append(f"Model: {output.get('model')}")
        lines.append("")
        lines.append("PORTFOLIO MANAGER DECISION")
        lines.append("-" * 80)
        lines.append(f"Manager View: {plan.get('manager_view')}")
        lines.append(f"Execution Permission: {plan.get('execution_permission')}")
        lines.append(f"Portfolio Mode: {plan.get('portfolio_mode')}")
        lines.append(f"Confidence: {plan.get('manager_confidence')}")
        lines.append("")
        lines.append("Executive Summary:")
        lines.append(plan.get("executive_summary", ""))
        lines.append("")
        lines.append("Current Portfolio Assessment:")
        lines.append(plan.get("current_portfolio_assessment", ""))
        lines.append("")
        lines.append("Target Weights:")
        for asset, weight in plan.get("target_weights", {}).items():
            lines.append(f"- {asset}: {weight}")
        lines.append("")
        lines.append("Weight Change Recommendations:")
        for rec in plan.get("weight_change_recommendations", []):
            lines.append(
                f"- {rec.get('asset')}: {rec.get('action')} | "
                f"current={rec.get('current_weight')} | "
                f"target={rec.get('target_weight')} | "
                f"change={rec.get('change')} | "
                f"status={rec.get('execution_status')} | "
                f"{rec.get('rationale')}"
            )
        lines.append("")
        lines.append("Primary Risks:")
        for risk in plan.get("primary_risks", []):
            lines.append(f"- {risk}")
        lines.append("")
        lines.append("Required Governance Actions:")
        for action in plan.get("required_governance_actions", []):
            lines.append(f"- {action}")
        lines.append("")
        lines.append("Execution Plan If Cleared:")
        for action in plan.get("execution_plan_if_cleared", []):
            lines.append(f"- {action}")
        lines.append("")
        lines.append("Do Not Execute Reason:")
        lines.append(plan.get("do_not_execute_reason", ""))

        return "\n".join(lines)


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 5C AI PORTFOLIO MANAGER")
    print("=" * 80)

    manager = AIPortfolioManager()
    output = manager.run()
    plan = output["portfolio_plan"]

    print(f"Backend: {output.get('llm_backend')}")
    print(f"Model:   {output.get('model')}")
    print("-" * 80)
    print(f"Manager View:         {plan.get('manager_view')}")
    print(f"Execution Permission: {plan.get('execution_permission')}")
    print(f"Portfolio Mode:       {plan.get('portfolio_mode')}")
    print(f"Confidence:           {plan.get('manager_confidence')}")
    print("-" * 80)
    print(plan.get("executive_summary"))
    print("-" * 80)
    print("Saved:")
    print("results/research/ai_portfolio_manager_plan.json")
    print("results/research/target_ai_portfolio.json")
    print("results/research/ai_portfolio_manager_explanation.txt")


if __name__ == "__main__":
    main()