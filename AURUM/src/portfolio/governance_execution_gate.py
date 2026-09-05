# src/portfolio/governance_execution_gate.py

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from src.portfolio.portfolio_audit_trail import PortfolioAuditTrail


OUTPUT_DIR = Path("results/portfolio")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DECISION_PATH = OUTPUT_DIR / "governance_execution_decision.json"


class GovernanceExecutionGate:
    def __init__(self):
        self.audit = PortfolioAuditTrail()

    def load_json(self, path: str) -> Dict[str, Any]:
        p = Path(path)
        if not p.exists():
            return {}
        return json.loads(p.read_text(encoding="utf-8"))

    def evaluate(self) -> Dict[str, Any]:
        governance = self.load_json("results/governance/portfolio_approval_decision.json")

        approved = bool(governance.get("approved", False))
        approval_decision = governance.get("approval_decision", "UNKNOWN")
        committee_decision = governance.get("committee_decision", "UNKNOWN")
        compliance_status = governance.get("compliance_status", "UNKNOWN")
        blocked_by_escalation = bool(governance.get("execution_blocked_by_escalation_engine", False))

        allow_execution = (
            approved
            and approval_decision not in {"BLOCKED_FROM_EXECUTION", "REJECTED"}
            and committee_decision != "REJECTED"
            and not blocked_by_escalation
        )

        decision = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "gate_type": "GOVERNANCE_AWARE_EXECUTION_GATE",
            "allow_execution": allow_execution,
            "execution_status": "EXECUTION_ALLOWED" if allow_execution else "EXECUTION_BLOCKED",
            "approval_decision": approval_decision,
            "approved": approved,
            "committee_decision": committee_decision,
            "compliance_status": compliance_status,
            "blocked_by_escalation_engine": blocked_by_escalation,
            "reasons": governance.get("reasons", []),
            "interpretation": (
                "Governance approved the portfolio; execution may proceed."
                if allow_execution
                else "Governance did not approve the portfolio; execution must not proceed."
            ),
        }

        DECISION_PATH.write_text(json.dumps(decision, indent=2), encoding="utf-8")

        self.audit.record_event(
            event_type="GOVERNANCE_EXECUTION_GATE_EVALUATED",
            decision_stage="3H_GOVERNANCE_EXECUTION_GATE",
            payload=decision,
            status=decision["execution_status"],
        )

        return decision


def main():
    gate = GovernanceExecutionGate()
    decision = gate.evaluate()

    print("=" * 80)
    print("AURUM GOVERNANCE EXECUTION GATE")
    print("=" * 80)
    print(json.dumps(decision, indent=2))


if __name__ == "__main__":
    main()