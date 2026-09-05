# src/portfolio/portfolio_decision_orchestrator.py

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from src.portfolio.portfolio_audit_trail import PortfolioAuditTrail
from src.portfolio.portfolio_state_manager import PortfolioStateManager
from src.portfolio.portfolio_operating_report import PortfolioOperatingReport


ORCHESTRATION_DIR = Path("results/portfolio")
ORCHESTRATION_DIR.mkdir(parents=True, exist_ok=True)

ORCHESTRATION_PATH = ORCHESTRATION_DIR / "portfolio_decision_orchestration.json"


class PortfolioDecisionOrchestrator:
    def __init__(self):
        self.audit = PortfolioAuditTrail()
        self.state_manager = PortfolioStateManager()
        self.report_builder = PortfolioOperatingReport()

    def load_json(self, path: str) -> Dict[str, Any]:
        p = Path(path)
        if not p.exists():
            return {}
        return json.loads(p.read_text(encoding="utf-8"))

    def run(self) -> Dict[str, Any]:
        self.audit.record_event(
            event_type="PORTFOLIO_ORCHESTRATION_STARTED",
            decision_stage="3H_DECISION_ORCHESTRATOR",
            payload={"message": "Starting institutional portfolio orchestration."},
        )

        regime_allocation = self.load_json(
            "results/regime_intelligence/final_regime_allocation_summary.json"
        )
        optimizer_decision = self.load_json(
            "results/optimization/final_optimizer_decision_report.json"
        )
        governance_decision = self.load_json(
            "results/governance/portfolio_approval_decision.json"
        )
        lifecycle_report = self.load_json(
            "results/execution/lifecycle_report.json"
        )

        portfolio_state = self.state_manager.build_state()
        operating_report = self.report_builder.build_report()

        orchestration = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "orchestration_type": "AURUM_INSTITUTIONAL_PORTFOLIO_DECISION_ORCHESTRATION",
            "inputs": {
                "regime_allocation_loaded": bool(regime_allocation),
                "optimizer_decision_loaded": bool(optimizer_decision),
                "governance_decision_loaded": bool(governance_decision),
                "execution_lifecycle_loaded": bool(lifecycle_report),
            },
            "decision_flow": {
                "regime_intelligence": regime_allocation,
                "optimizer_decision": optimizer_decision,
                "governance_decision": governance_decision,
                "execution_lifecycle": lifecycle_report,
                "portfolio_state": portfolio_state.get("state_summary", {}),
                "operating_report_sections": list(operating_report.keys()),
            },
            "institutional_status": self.evaluate_status(
                regime_allocation=regime_allocation,
                optimizer_decision=optimizer_decision,
                governance_decision=governance_decision,
                lifecycle_report=lifecycle_report,
            ),
        }

        ORCHESTRATION_PATH.write_text(
            json.dumps(orchestration, indent=2, default=str),
            encoding="utf-8",
        )

        self.audit.record_event(
            event_type="PORTFOLIO_ORCHESTRATION_COMPLETED",
            decision_stage="3H_DECISION_ORCHESTRATOR",
            payload={
                "orchestration_path": str(ORCHESTRATION_PATH),
                "institutional_status": orchestration["institutional_status"],
            },
            status="COMPLETED",
        )

        return orchestration

    def evaluate_status(
        self,
        regime_allocation: Dict[str, Any],
        optimizer_decision: Dict[str, Any],
        governance_decision: Dict[str, Any],
        lifecycle_report: Dict[str, Any],
    ) -> Dict[str, Any]:
        required = {
            "regime_allocation": bool(regime_allocation),
            "optimizer_decision": bool(optimizer_decision),
            "governance_decision": bool(governance_decision),
            "execution_lifecycle": bool(lifecycle_report),
        }

        ready = all(required.values())

        return {
            "portfolio_operating_system_ready": ready,
            "readiness_checks": required,
            "interpretation": (
                "AURUM has a connected institutional portfolio decision workflow."
                if ready
                else "AURUM portfolio workflow is partially connected; inspect missing inputs."
            ),
        }


def main():
    orchestrator = PortfolioDecisionOrchestrator()
    result = orchestrator.run()

    print("=" * 80)
    print("AURUM PORTFOLIO DECISION ORCHESTRATOR")
    print("=" * 80)
    print(json.dumps(result["institutional_status"], indent=2))


if __name__ == "__main__":
    main()