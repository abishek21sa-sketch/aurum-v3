# src/portfolio/end_to_end_portfolio_pipeline.py

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from src.portfolio.governance_execution_gate import GovernanceExecutionGate
from src.portfolio.portfolio_audit_trail import PortfolioAuditTrail
from src.portfolio.portfolio_decision_orchestrator import PortfolioDecisionOrchestrator
from src.portfolio.portfolio_operating_report import PortfolioOperatingReport
from src.portfolio.portfolio_state_manager import PortfolioStateManager


PIPELINE_DIR = Path("results/portfolio")
PIPELINE_DIR.mkdir(parents=True, exist_ok=True)

PIPELINE_SUMMARY_PATH = PIPELINE_DIR / "end_to_end_portfolio_pipeline_summary.json"


class EndToEndPortfolioPipeline:
    def __init__(self):
        self.audit = PortfolioAuditTrail()
        self.governance_gate = GovernanceExecutionGate()
        self.state_manager = PortfolioStateManager()
        self.report_builder = PortfolioOperatingReport()
        self.orchestrator = PortfolioDecisionOrchestrator()

    def run_module(self, module_name: str) -> Dict[str, Any]:
        started_at = datetime.now(timezone.utc).isoformat()

        result = subprocess.run(
            [sys.executable, "-m", module_name],
            capture_output=True,
            text=True,
        )

        ended_at = datetime.now(timezone.utc).isoformat()

        return {
            "module": module_name,
            "status": "PASS" if result.returncode == 0 else "FAIL",
            "return_code": result.returncode,
            "started_at": started_at,
            "ended_at": ended_at,
            "stdout_tail": result.stdout[-3000:],
            "stderr_tail": result.stderr[-3000:],
        }

    def run(self) -> Dict[str, Any]:
        self.audit.record_event(
            event_type="END_TO_END_PORTFOLIO_PIPELINE_STARTED",
            decision_stage="3H_END_TO_END_PIPELINE",
            payload={"message": "Starting full institutional portfolio pipeline."},
        )

        governance_gate_decision = self.governance_gate.evaluate()

        module_results: List[Dict[str, Any]] = []

        pre_execution_modules = [
            "src.portfolio.portfolio_state_manager",
            "src.portfolio.portfolio_operating_report",
            "src.portfolio.portfolio_decision_orchestrator",
        ]

        for module in pre_execution_modules:
            module_results.append(self.run_module(module))

        execution_modules = [
            "src.execution.portfolio_state_engine",
            "src.execution.trade_generation_engine",
            "src.execution.turnover_control_engine",
            "src.execution.transaction_cost_engine",
            "src.execution.cost_aware_rebalancer",
            "src.execution.rebalance_scheduler",
            "src.execution.execution_priority_engine",
            "src.execution.cash_management_engine",
            "src.execution.paper_trading_engine",
        ]

        if governance_gate_decision.get("allow_execution"):
            execution_status = "EXECUTION_RAN"
            for module in execution_modules:
                module_results.append(self.run_module(module))
        else:
            execution_status = "EXECUTION_SKIPPED_BY_GOVERNANCE_GATE"

        portfolio_state = self.state_manager.build_state()
        operating_report = self.report_builder.build_report()
        orchestration = self.orchestrator.run()

        all_modules_passed = all(item["status"] == "PASS" for item in module_results)

        summary = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "pipeline_type": "AURUM_END_TO_END_INSTITUTIONAL_PORTFOLIO_PIPELINE",
            "governance_gate": governance_gate_decision,
            "execution_status": execution_status,
            "module_results": module_results,
            "all_modules_passed": all_modules_passed,
            "portfolio_state_summary": portfolio_state.get("state_summary", {}),
            "operating_report_sections": list(operating_report.keys()),
            "orchestration_status": orchestration.get("institutional_status", {}),
            "final_interpretation": (
                "Pipeline completed with execution allowed."
                if governance_gate_decision.get("allow_execution")
                else "Pipeline completed, but execution was blocked by governance."
            ),
        }

        PIPELINE_SUMMARY_PATH.write_text(
            json.dumps(summary, indent=2, default=str),
            encoding="utf-8",
        )

        self.audit.record_event(
            event_type="END_TO_END_PORTFOLIO_PIPELINE_COMPLETED",
            decision_stage="3H_END_TO_END_PIPELINE",
            payload={
                "summary_path": str(PIPELINE_SUMMARY_PATH),
                "execution_status": execution_status,
                "all_modules_passed": all_modules_passed,
            },
            status="COMPLETED",
        )

        return summary


def main():
    pipeline = EndToEndPortfolioPipeline()
    summary = pipeline.run()

    print("=" * 80)
    print("AURUM END-TO-END PORTFOLIO PIPELINE")
    print("=" * 80)
    print("Execution Status:", summary["execution_status"])
    print("All Modules Passed:", summary["all_modules_passed"])
    print("Final Interpretation:", summary["final_interpretation"])
    print("Summary Saved:", PIPELINE_SUMMARY_PATH)


if __name__ == "__main__":
    main()