from pathlib import Path
import json
from datetime import datetime


GOVERNANCE_DIR = Path("results/governance")

COMPLIANCE_PATH = GOVERNANCE_DIR / "compliance_summary.json"
CONCENTRATION_PATH = GOVERNANCE_DIR / "concentration_summary.json"
LIQUIDITY_PATH = GOVERNANCE_DIR / "liquidity_summary.json"
DRAWDOWN_PATH = GOVERNANCE_DIR / "drawdown_governance_summary.json"
COMMITTEE_PATH = GOVERNANCE_DIR / "investment_committee_decision.json"

OUTPUT_PATH = GOVERNANCE_DIR / "governance_escalations.json"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def add_escalation(escalations: list, level: str, source: str, reason: str, action: str) -> None:
    escalations.append(
        {
            "timestamp": datetime.now().isoformat(),
            "escalation_level": level,
            "source": source,
            "reason": reason,
            "required_action": action,
        }
    )


def run_governance_escalation_engine() -> dict:
    compliance = load_json(COMPLIANCE_PATH)
    concentration = load_json(CONCENTRATION_PATH)
    liquidity = load_json(LIQUIDITY_PATH)
    drawdown = load_json(DRAWDOWN_PATH)
    committee = load_json(COMMITTEE_PATH)

    escalations = []

    if compliance.get("compliance_status") == "NON_COMPLIANT_CRITICAL":
        add_escalation(
            escalations,
            "CRITICAL",
            "portfolio_compliance_engine",
            "Critical compliance violation detected.",
            "Block execution and require investment committee review.",
        )

    elif compliance.get("compliance_status") == "NON_COMPLIANT":
        add_escalation(
            escalations,
            "LEVEL_3",
            "portfolio_compliance_engine",
            "Portfolio compliance violation detected.",
            "Require remediation before execution.",
        )

    if concentration.get("concentration_status") == "HIGH_CONCENTRATION":
        add_escalation(
            escalations,
            "LEVEL_2",
            "concentration_risk_engine",
            "High portfolio concentration detected.",
            "Reduce top holding exposure and improve diversification.",
        )

    elif concentration.get("concentration_status") == "MODERATE_CONCENTRATION":
        add_escalation(
            escalations,
            "LEVEL_1",
            "concentration_risk_engine",
            "Moderate concentration detected.",
            "Monitor concentration risk.",
        )

    if liquidity.get("liquidity_status") == "STRESSED":
        add_escalation(
            escalations,
            "LEVEL_3",
            "liquidity_governance_engine",
            "Liquidity stress detected.",
            "Increase cash buffer and reduce illiquid exposure.",
        )

    elif liquidity.get("liquidity_status") == "CAUTION":
        add_escalation(
            escalations,
            "LEVEL_1",
            "liquidity_governance_engine",
            "Liquidity caution condition detected.",
            "Monitor cash buffer and liquidity profile.",
        )

    drawdown_status = drawdown.get("governance_status")

    if drawdown_status == "EMERGENCY_REVIEW":
        add_escalation(
            escalations,
            "CRITICAL",
            "drawdown_governance_engine",
            "Emergency drawdown threshold breached.",
            "Immediate portfolio review required.",
        )

    elif drawdown_status == "DERISK_REQUIRED":
        add_escalation(
            escalations,
            "LEVEL_3",
            "drawdown_governance_engine",
            "De-risk threshold breached.",
            "Reduce portfolio risk exposure.",
        )

    elif drawdown_status == "HEDGE_REQUIRED":
        add_escalation(
            escalations,
            "LEVEL_2",
            "drawdown_governance_engine",
            "Hedge threshold breached.",
            "Activate or increase hedge overlay.",
        )

    elif drawdown_status == "CAUTION":
        add_escalation(
            escalations,
            "LEVEL_1",
            "drawdown_governance_engine",
            "Drawdown warning threshold breached.",
            "Monitor drawdown risk.",
        )

    if committee.get("committee_decision") == "REJECTED":
        add_escalation(
            escalations,
            "CRITICAL",
            "investment_committee_engine",
            "Investment committee rejected portfolio.",
            "Portfolio cannot proceed to execution.",
        )

    elif committee.get("committee_decision") == "APPROVED_WITH_CONDITIONS":
        add_escalation(
            escalations,
            "LEVEL_2",
            "investment_committee_engine",
            "Portfolio approved with conditions.",
            "Resolve committee conditions before full approval.",
        )

    highest_level = "NONE"

    priority = {
        "NONE": 0,
        "LEVEL_1": 1,
        "LEVEL_2": 2,
        "LEVEL_3": 3,
        "CRITICAL": 4,
    }

    for escalation in escalations:
        level = escalation["escalation_level"]
        if priority[level] > priority[highest_level]:
            highest_level = level

    summary = {
        "generated_at": datetime.now().isoformat(),
        "active_escalations": len(escalations),
        "highest_escalation_level": highest_level,
        "execution_blocked": highest_level == "CRITICAL",
        "escalations": escalations,
    }

    OUTPUT_PATH.write_text(json.dumps(summary, indent=4), encoding="utf-8")

    return summary


def main() -> None:
    print("=" * 80)
    print("AURUM GOVERNANCE ESCALATION ENGINE")
    print("=" * 80)

    summary = run_governance_escalation_engine()

    print("\nESCALATION SUMMARY")
    print("-" * 80)
    print(f"Active escalations: {summary['active_escalations']}")
    print(f"Highest level: {summary['highest_escalation_level']}")
    print(f"Execution blocked: {summary['execution_blocked']}")

    print("\nACTIVE ESCALATIONS")
    print("-" * 80)

    if not summary["escalations"]:
        print("No active governance escalations.")
    else:
        for item in summary["escalations"]:
            print(
                f"[{item['escalation_level']}] "
                f"{item['source']} — {item['reason']}"
            )

    print(f"\nOutput: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()