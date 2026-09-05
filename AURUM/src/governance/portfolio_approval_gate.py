from pathlib import Path
import json
from datetime import datetime


GOVERNANCE_DIR = Path("results/governance")

COMPLIANCE_PATH = GOVERNANCE_DIR / "compliance_summary.json"
COMMITTEE_PATH = GOVERNANCE_DIR / "investment_committee_decision.json"
ESCALATION_PATH = GOVERNANCE_DIR / "governance_escalations.json"

OUTPUT_PATH = GOVERNANCE_DIR / "portfolio_approval_decision.json"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def run_portfolio_approval_gate() -> dict:
    compliance = load_json(COMPLIANCE_PATH)
    committee = load_json(COMMITTEE_PATH)
    escalation = load_json(ESCALATION_PATH)

    reasons = []

    compliance_status = compliance.get("compliance_status", "UNKNOWN")
    committee_decision = committee.get("committee_decision", "UNKNOWN")
    execution_blocked = escalation.get("execution_blocked", True)

    if compliance_status not in ["COMPLIANT"]:
        reasons.append(f"Compliance status is {compliance_status}.")

    if committee_decision == "REJECTED":
        reasons.append("Investment committee rejected the portfolio.")

    if execution_blocked:
        reasons.append("Governance escalation engine blocked execution.")

    approved = (
        compliance_status == "COMPLIANT"
        and committee_decision in ["APPROVED", "APPROVED_WITH_CONDITIONS"]
        and not execution_blocked
    )

    decision = "APPROVED_FOR_EXECUTION" if approved else "BLOCKED_FROM_EXECUTION"

    approval_report = {
        "generated_at": datetime.now().isoformat(),
        "approval_decision": decision,
        "approved": approved,
        "compliance_status": compliance_status,
        "committee_decision": committee_decision,
        "execution_blocked_by_escalation_engine": execution_blocked,
        "reasons": reasons,
    }

    OUTPUT_PATH.write_text(
        json.dumps(approval_report, indent=4),
        encoding="utf-8",
    )

    return approval_report


def main() -> None:
    print("=" * 80)
    print("AURUM PORTFOLIO APPROVAL GATE")
    print("=" * 80)

    report = run_portfolio_approval_gate()

    print("\nAPPROVAL DECISION")
    print("-" * 80)
    print(f"Decision: {report['approval_decision']}")
    print(f"Approved: {report['approved']}")
    print(f"Compliance status: {report['compliance_status']}")
    print(f"Committee decision: {report['committee_decision']}")
    print(
        "Execution blocked by escalation engine: "
        f"{report['execution_blocked_by_escalation_engine']}"
    )

    print("\nREASONS")
    print("-" * 80)

    if not report["reasons"]:
        print("No blocking reasons.")
    else:
        for reason in report["reasons"]:
            print(f"- {reason}")

    print(f"\nOutput: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()