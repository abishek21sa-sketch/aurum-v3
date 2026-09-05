from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from src.research.copilot_router import CopilotRouter
from src.research.copilot_actions import CopilotActions


COPILOT_RESPONSE_JSON = Path("results/copilot/portfolio_copilot_response.json")
COPILOT_TRANSCRIPT_JSONL = Path("results/copilot/portfolio_copilot_transcript.jsonl")


class AutonomousPortfolioCopilot:
    """
    Natural-language interface for AURUM.

    Combines:
    - Portfolio assistant
    - Risk officer
    - Governance copilot
    - Memory lookup
    - Decision explanation
    """

    def __init__(self) -> None:
        COPILOT_RESPONSE_JSON.parent.mkdir(parents=True, exist_ok=True)
        self.router = CopilotRouter()
        self.actions = CopilotActions()

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def ask(self, user_query: str) -> Dict[str, Any]:
        route = self.router.route(user_query)
        response = self.actions.execute(route.action, route.entities)

        copilot_response = {
            "timestamp": self._utc_now(),
            "user_query": user_query,
            "route": {
                "action": route.action,
                "confidence": route.confidence,
                "entities": route.entities,
                "reasoning": route.reasoning,
            },
            "response": response,
            "copilot_identity": {
                "name": "AURUM Autonomous Portfolio Copilot",
                "mode": "portfolio_risk_governance_assistant",
                "execution_mode": "advisory_only",
            },
        }

        with COPILOT_RESPONSE_JSON.open("w", encoding="utf-8") as f:
            json.dump(copilot_response, f, indent=2, default=str)

        with COPILOT_TRANSCRIPT_JSONL.open("a", encoding="utf-8") as f:
            f.write(json.dumps(copilot_response, default=str) + "\n")

        return copilot_response

    def format_answer(self, copilot_response: Dict[str, Any]) -> str:
        route = copilot_response.get("route", {})
        response = copilot_response.get("response", {})

        lines = []
        lines.append("=" * 80)
        lines.append("AURUM AUTONOMOUS PORTFOLIO COPILOT")
        lines.append("=" * 80)
        lines.append("")
        lines.append(f"User Query:       {copilot_response.get('user_query')}")
        lines.append(f"Routed Action:    {route.get('action')}")
        lines.append(f"Route Confidence: {route.get('confidence')}")
        lines.append(f"Execution Mode:   advisory_only")
        lines.append("")
        lines.append("ANSWER")
        lines.append("-" * 80)
        lines.append(str(response.get("answer")))

        if response.get("risk_officer_view"):
            lines.append("")
            lines.append("RISK OFFICER VIEW")
            lines.append("-" * 80)
            lines.append(str(response.get("risk_officer_view")))

        if response.get("governance_view"):
            lines.append("")
            lines.append("GOVERNANCE VIEW")
            lines.append("-" * 80)
            lines.append(str(response.get("governance_view")))

        if route.get("action") == "SHOW_TOP_RISKS":
            lines.append("")
            lines.append("TOP RISKS")
            lines.append("-" * 80)
            for risk in response.get("risks", []):
                lines.append(
                    f"{risk.get('rank')}. {risk.get('risk')} "
                    f"[{risk.get('severity')}] — {risk.get('explanation')}"
                )

        if route.get("action") == "COMPARE_PORTFOLIOS":
            lines.append("")
            lines.append("PORTFOLIO COMPARISON")
            lines.append("-" * 80)

            comparison = response.get("comparison", {})
            for asset, values in comparison.items():
                lines.append(
                    f"{asset}: current={values.get('current')}, "
                    f"defensive={values.get('defensive')}, "
                    f"difference={values.get('difference')}"
                )

        if route.get("action") in {"RUN_FED_SHOCK", "RUN_ASSET_SHOCK"}:
            lines.append("")
            lines.append("SCENARIO DETAILS")
            lines.append("-" * 80)
            details = response.get("shock_result", response)
            for key, value in details.items():
                if key not in {"answer", "action"}:
                    lines.append(f"{key}: {value}")

        if route.get("action") == "GOVERNANCE_STATUS":
            lines.append("")
            lines.append("GOVERNANCE STATUS")
            lines.append("-" * 80)
            for key, value in response.get("governance", {}).items():
                lines.append(f"{key}: {value}")

        if route.get("action") == "MEMORY_LOOKUP":
            memory_report = response.get("memory_report", {})
            best = memory_report.get("best_match", {})
            lines.append("")
            lines.append("INSTITUTIONAL MEMORY")
            lines.append("-" * 80)
            lines.append(f"Closest Memory: {best.get('title')}")
            lines.append(f"Regime:         {best.get('regime')}")
            lines.append(f"Similarity:     {best.get('similarity_percent')}%")

        lines.append("")
        lines.append("=" * 80)

        return "\n".join(lines)


def demo_queries() -> List[str]:
    return [
        "Show top risks.",
        "Compare current portfolio to defensive portfolio.",
        "Run a Fed shock.",
        "What happens if NVDA falls 20%?",
        "Why are we defensive?",
        "Have we seen this before?",
        "What is governance status?",
    ]


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 5E AUTONOMOUS PORTFOLIO COPILOT")
    print("=" * 80)

    copilot = AutonomousPortfolioCopilot()

    for query in demo_queries():
        result = copilot.ask(query)
        print(copilot.format_answer(result))

    print(f"Saved Latest Response: {COPILOT_RESPONSE_JSON}")
    print(f"Saved Transcript:      {COPILOT_TRANSCRIPT_JSONL}")
    print("=" * 80)


if __name__ == "__main__":
    main()