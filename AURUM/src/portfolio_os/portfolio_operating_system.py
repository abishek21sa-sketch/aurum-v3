from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from src.portfolio_os.daily_portfolio_cycle import DailyPortfolioCycle
from src.portfolio_os.portfolio_director import PortfolioDirector


PORTFOLIO_OS_JSON = Path("results/portfolio_os/portfolio_operating_system.json")
PORTFOLIO_OS_TXT = Path("results/portfolio_os/portfolio_operating_system_report.txt")


class PortfolioOperatingSystem:
    """
    Master AURUM Portfolio Operating System.

    One command runs the institutional daily cycle and produces:
    - operating state
    - portfolio directive
    - governance status
    - learning summary
    - daily PM report
    """

    def __init__(self) -> None:
        PORTFOLIO_OS_JSON.parent.mkdir(parents=True, exist_ok=True)
        self.daily_cycle = DailyPortfolioCycle()
        self.director = PortfolioDirector()

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def run(self) -> Dict[str, Any]:
        cycle = self.daily_cycle.run()
        directive = cycle.get("final_directive") or self.director.generate_directive()

        operating_state = {
            "os_id": f"aurum_portfolio_os_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            "timestamp": self._utc_now(),
            "status": "COMPLETE",
            "system_name": "AURUM Portfolio Operating System",
            "cycle_id": cycle.get("cycle_id"),
            "portfolio_posture": directive.get("portfolio_posture"),
            "portfolio_action": directive.get("portfolio_action"),
            "execution_permission": directive.get("execution_permission"),
            "approval_status": directive.get("approval_status"),
            "confidence": directive.get("confidence"),
            "governance_view": directive.get("governance_view"),
            "risk_officer_view": directive.get("risk_officer_view"),
            "memory_view": directive.get("memory_view"),
            "learning_view": directive.get("learning_view"),
            "recommended_actions": directive.get("recommended_actions", []),
            "cycle": cycle,
        }

        with PORTFOLIO_OS_JSON.open("w", encoding="utf-8") as f:
            json.dump(operating_state, f, indent=2, default=str)

        with PORTFOLIO_OS_TXT.open("w", encoding="utf-8") as f:
            f.write(self._to_text(operating_state))

        return operating_state

    def _to_text(self, state: Dict[str, Any]) -> str:
        lines = []
        lines.append("=" * 80)
        lines.append("AURUM PORTFOLIO OPERATING SYSTEM REPORT")
        lines.append("=" * 80)

        lines.append("")
        lines.append("OPERATING STATE")
        lines.append("-" * 80)
        lines.append(f"OS ID:                 {state.get('os_id')}")
        lines.append(f"Cycle ID:              {state.get('cycle_id')}")
        lines.append(f"Status:                {state.get('status')}")
        lines.append(f"Portfolio Posture:     {state.get('portfolio_posture')}")
        lines.append(f"Portfolio Action:      {state.get('portfolio_action')}")
        lines.append(f"Execution Permission:  {state.get('execution_permission')}")
        lines.append(f"Approval Status:       {state.get('approval_status')}")
        lines.append(f"Confidence:            {state.get('confidence')}")

        lines.append("")
        lines.append("RISK OFFICER VIEW")
        lines.append("-" * 80)
        lines.append(str(state.get("risk_officer_view")))

        lines.append("")
        lines.append("GOVERNANCE VIEW")
        lines.append("-" * 80)
        lines.append(str(state.get("governance_view")))

        lines.append("")
        lines.append("MEMORY VIEW")
        lines.append("-" * 80)
        lines.append(str(state.get("memory_view")))

        lines.append("")
        lines.append("LEARNING VIEW")
        lines.append("-" * 80)
        lines.append(str(state.get("learning_view")))

        lines.append("")
        lines.append("RECOMMENDED ACTIONS")
        lines.append("-" * 80)
        for action in state.get("recommended_actions", []):
            lines.append(f"- {action}")

        cycle = state.get("cycle", {})
        stages = cycle.get("stages", {})

        lines.append("")
        lines.append("CYCLE STAGES")
        lines.append("-" * 80)
        for stage_name, stage_data in stages.items():
            lines.append(f"{stage_name}: {stage_data.get('status')}")

        lines.append("")
        lines.append("=" * 80)

        return "\n".join(lines)


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 6A PORTFOLIO OPERATING SYSTEM")
    print("=" * 80)

    os_engine = PortfolioOperatingSystem()
    state = os_engine.run()

    print(f"OS ID:                 {state['os_id']}")
    print(f"Status:                {state['status']}")
    print(f"Portfolio Posture:     {state['portfolio_posture']}")
    print(f"Portfolio Action:      {state['portfolio_action']}")
    print(f"Execution Permission:  {state['execution_permission']}")
    print(f"Confidence:            {state['confidence']}")
    print(f"Saved JSON:            {PORTFOLIO_OS_JSON}")
    print(f"Saved TXT:             {PORTFOLIO_OS_TXT}")
    print("=" * 80)


if __name__ == "__main__":
    main()