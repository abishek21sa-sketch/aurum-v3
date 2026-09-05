from pathlib import Path
import json
import pandas as pd
from datetime import datetime


GOVERNANCE_DIR = Path("results/governance")

SUMMARY_FILES = {
    "policy": GOVERNANCE_DIR / "policy_constraints.json",
    "exposure": GOVERNANCE_DIR / "exposure_limit_summary.json",
    "compliance": GOVERNANCE_DIR / "compliance_summary.json",
    "concentration": GOVERNANCE_DIR / "concentration_summary.json",
    "liquidity": GOVERNANCE_DIR / "liquidity_summary.json",
    "drawdown": GOVERNANCE_DIR / "drawdown_governance_summary.json",
    "committee": GOVERNANCE_DIR / "investment_committee_decision.json",
    "escalation": GOVERNANCE_DIR / "governance_escalations.json",
    "approval": GOVERNANCE_DIR / "portfolio_approval_decision.json",
}

OUTPUT_REPORT_PATH = GOVERNANCE_DIR / "institutional_governance_report.csv"
OUTPUT_SUMMARY_PATH = GOVERNANCE_DIR / "institutional_governance_summary.json"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def flatten_summary(section: str, data: dict) -> list[dict]:
    rows = []

    for key, value in data.items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            rows.append(
                {
                    "section": section,
                    "metric": key,
                    "value": value,
                }
            )

    return rows


def run_governance_report_generator() -> tuple[pd.DataFrame, dict]:
    loaded = {
        name: load_json(path)
        for name, path in SUMMARY_FILES.items()
    }

    rows = []

    for section, data in loaded.items():
        rows.extend(flatten_summary(section, data))

    report = pd.DataFrame(rows)

    compliance_status = loaded["compliance"].get("compliance_status", "UNKNOWN")
    exposure_status = loaded["exposure"].get("overall_status", "UNKNOWN")
    concentration_status = loaded["concentration"].get(
        "concentration_status",
        "UNKNOWN",
    )
    liquidity_status = loaded["liquidity"].get("liquidity_status", "UNKNOWN")
    drawdown_status = loaded["drawdown"].get("governance_status", "UNKNOWN")
    committee_decision = loaded["committee"].get("committee_decision", "UNKNOWN")
    highest_escalation = loaded["escalation"].get(
        "highest_escalation_level",
        "UNKNOWN",
    )
    approval_decision = loaded["approval"].get("approval_decision", "UNKNOWN")

    institutional_status = "APPROVED"

    if approval_decision == "BLOCKED_FROM_EXECUTION":
        institutional_status = "BLOCKED"

    elif committee_decision == "APPROVED_WITH_CONDITIONS":
        institutional_status = "APPROVED_WITH_CONDITIONS"

    elif highest_escalation in ["LEVEL_2", "LEVEL_3", "CRITICAL"]:
        institutional_status = "REVIEW_REQUIRED"

    summary = {
        "generated_at": datetime.now().isoformat(),
        "institutional_status": institutional_status,
        "exposure_status": exposure_status,
        "compliance_status": compliance_status,
        "concentration_status": concentration_status,
        "liquidity_status": liquidity_status,
        "drawdown_status": drawdown_status,
        "committee_decision": committee_decision,
        "highest_escalation_level": highest_escalation,
        "approval_decision": approval_decision,
        "portfolio_allowed_to_execute": approval_decision == "APPROVED_FOR_EXECUTION",
    }

    report.to_csv(OUTPUT_REPORT_PATH, index=False)
    OUTPUT_SUMMARY_PATH.write_text(
        json.dumps(summary, indent=4),
        encoding="utf-8",
    )

    return report, summary


def main() -> None:
    print("=" * 80)
    print("AURUM INSTITUTIONAL GOVERNANCE REPORT GENERATOR")
    print("=" * 80)

    report, summary = run_governance_report_generator()

    print("\nINSTITUTIONAL GOVERNANCE SUMMARY")
    print("-" * 80)
    print(f"Institutional status: {summary['institutional_status']}")
    print(f"Exposure status: {summary['exposure_status']}")
    print(f"Compliance status: {summary['compliance_status']}")
    print(f"Concentration status: {summary['concentration_status']}")
    print(f"Liquidity status: {summary['liquidity_status']}")
    print(f"Drawdown status: {summary['drawdown_status']}")
    print(f"Committee decision: {summary['committee_decision']}")
    print(f"Highest escalation: {summary['highest_escalation_level']}")
    print(f"Approval decision: {summary['approval_decision']}")
    print(
        "Portfolio allowed to execute: "
        f"{summary['portfolio_allowed_to_execute']}"
    )

    print(f"\nReport rows: {len(report)}")
    print(f"Output report: {OUTPUT_REPORT_PATH}")
    print(f"Output summary: {OUTPUT_SUMMARY_PATH}")


if __name__ == "__main__":
    main()