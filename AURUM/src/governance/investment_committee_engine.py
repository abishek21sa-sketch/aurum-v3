from pathlib import Path
import json


GOVERNANCE_DIR = Path("results/governance")

COMPLIANCE_PATH = GOVERNANCE_DIR / "compliance_summary.json"
CONCENTRATION_PATH = GOVERNANCE_DIR / "concentration_summary.json"
LIQUIDITY_PATH = GOVERNANCE_DIR / "liquidity_summary.json"
DRAWDOWN_PATH = GOVERNANCE_DIR / "drawdown_governance_summary.json"

OUTPUT_PATH = GOVERNANCE_DIR / "investment_committee_decision.json"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def run_investment_committee_engine() -> dict:
    compliance = load_json(COMPLIANCE_PATH)
    concentration = load_json(CONCENTRATION_PATH)
    liquidity = load_json(LIQUIDITY_PATH)
    drawdown = load_json(DRAWDOWN_PATH)

    findings = []
    score = 100

    compliance_status = compliance.get("compliance_status", "UNKNOWN")

    if compliance_status == "NON_COMPLIANT_CRITICAL":
        findings.append("Critical compliance violation detected.")
        score -= 50

    elif compliance_status == "NON_COMPLIANT":
        findings.append("Compliance violations detected.")
        score -= 25

    concentration_status = concentration.get(
        "concentration_status",
        "UNKNOWN",
    )

    if concentration_status == "HIGH_CONCENTRATION":
        findings.append("Portfolio concentration risk is elevated.")
        score -= 20

    elif concentration_status == "MODERATE_CONCENTRATION":
        findings.append("Moderate concentration risk detected.")
        score -= 10

    liquidity_status = liquidity.get("liquidity_status", "UNKNOWN")

    if liquidity_status == "STRESSED":
        findings.append("Liquidity stress identified.")
        score -= 20

    elif liquidity_status == "CAUTION":
        findings.append("Liquidity caution flagged.")
        score -= 10

    drawdown_status = drawdown.get("governance_status", "UNKNOWN")

    if drawdown_status == "EMERGENCY_REVIEW":
        findings.append("Emergency drawdown condition.")
        score -= 40

    elif drawdown_status == "DERISK_REQUIRED":
        findings.append("Portfolio requires de-risking.")
        score -= 25

    elif drawdown_status == "HEDGE_REQUIRED":
        findings.append("Portfolio hedge recommended.")
        score -= 15

    elif drawdown_status == "CAUTION":
        findings.append("Drawdown caution condition.")
        score -= 5

    if score >= 80:
        decision = "APPROVED"

    elif score >= 60:
        decision = "APPROVED_WITH_CONDITIONS"

    else:
        decision = "REJECTED"

    committee_report = {
        "committee_score": score,
        "committee_decision": decision,
        "number_of_findings": len(findings),
        "findings": findings,
        "compliance_status": compliance_status,
        "concentration_status": concentration_status,
        "liquidity_status": liquidity_status,
        "drawdown_status": drawdown_status,
    }

    OUTPUT_PATH.write_text(
        json.dumps(committee_report, indent=4),
        encoding="utf-8",
    )

    return committee_report


def main() -> None:
    print("=" * 80)
    print("AURUM INVESTMENT COMMITTEE ENGINE")
    print("=" * 80)

    report = run_investment_committee_engine()

    print("\nCOMMITTEE DECISION")
    print("-" * 80)
    print(f"Committee score: {report['committee_score']}")
    print(f"Decision: {report['committee_decision']}")
    print(f"Findings: {report['number_of_findings']}")

    print("\nKEY FINDINGS")
    print("-" * 80)

    if not report["findings"]:
        print("No governance concerns identified.")
    else:
        for finding in report["findings"]:
            print(f"- {finding}")

    print(f"\nOutput: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()