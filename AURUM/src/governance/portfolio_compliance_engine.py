from pathlib import Path
import json
import pandas as pd


GOVERNANCE_DIR = Path("results/governance")

EXPOSURE_REPORT_PATH = GOVERNANCE_DIR / "exposure_limit_report.csv"
EXPOSURE_SUMMARY_PATH = GOVERNANCE_DIR / "exposure_limit_summary.json"

OUTPUT_REPORT_PATH = GOVERNANCE_DIR / "compliance_report.csv"
OUTPUT_SUMMARY_PATH = GOVERNANCE_DIR / "compliance_summary.json"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_exposure_report() -> pd.DataFrame:
    if not EXPOSURE_REPORT_PATH.exists():
        raise FileNotFoundError(
            "Missing exposure_limit_report.csv. Run exposure_limit_monitor first."
        )

    return pd.read_csv(EXPOSURE_REPORT_PATH)


def classify_compliance(report: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    rows = []

    failed = report[report["status"] == "FAIL"]
    warnings = report[
        (report["status"] == "PASS")
        & (report["actual_weight"].astype(float) >= 0.9 * report["actual_weight"].astype(float))
    ]

    for _, row in report.iterrows():
        severity = "NONE"

        if row["status"] == "FAIL":
            if float(row["violation_amount"]) >= 0.10:
                severity = "CRITICAL"
            elif float(row["violation_amount"]) >= 0.05:
                severity = "HIGH"
            else:
                severity = "MEDIUM"

        rows.append(
            {
                "check_type": row["check_type"],
                "asset": row["asset"],
                "asset_class": row["asset_class"],
                "rule": row["rule"],
                "actual_weight": row["actual_weight"],
                "limit": row["limit"],
                "status": row["status"],
                "violation_amount": row["violation_amount"],
                "severity": severity,
            }
        )

    compliance_report = pd.DataFrame(rows)

    critical_count = int((compliance_report["severity"] == "CRITICAL").sum())
    high_count = int((compliance_report["severity"] == "HIGH").sum())
    medium_count = int((compliance_report["severity"] == "MEDIUM").sum())
    fail_count = int((compliance_report["status"] == "FAIL").sum())

    if critical_count > 0:
        compliance_status = "NON_COMPLIANT_CRITICAL"
    elif fail_count > 0:
        compliance_status = "NON_COMPLIANT"
    else:
        compliance_status = "COMPLIANT"

    summary = {
        "total_checks": int(len(compliance_report)),
        "failed_checks": fail_count,
        "critical_violations": critical_count,
        "high_violations": high_count,
        "medium_violations": medium_count,
        "compliance_status": compliance_status,
        "execution_allowed": compliance_status == "COMPLIANT",
    }

    return compliance_report, summary


def run_portfolio_compliance_engine() -> tuple[pd.DataFrame, dict]:
    exposure_report = load_exposure_report()
    compliance_report, summary = classify_compliance(exposure_report)

    compliance_report.to_csv(OUTPUT_REPORT_PATH, index=False)
    OUTPUT_SUMMARY_PATH.write_text(json.dumps(summary, indent=4), encoding="utf-8")

    return compliance_report, summary


def main() -> None:
    print("=" * 80)
    print("AURUM PORTFOLIO COMPLIANCE ENGINE")
    print("=" * 80)

    report, summary = run_portfolio_compliance_engine()

    print("\nCOMPLIANCE SUMMARY")
    print("-" * 80)
    print(f"Total checks: {summary['total_checks']}")
    print(f"Failed checks: {summary['failed_checks']}")
    print(f"Critical violations: {summary['critical_violations']}")
    print(f"High violations: {summary['high_violations']}")
    print(f"Medium violations: {summary['medium_violations']}")
    print(f"Compliance status: {summary['compliance_status']}")
    print(f"Execution allowed: {summary['execution_allowed']}")

    violations = report[report["status"] == "FAIL"]

    print("\nACTIVE VIOLATIONS")
    print("-" * 80)

    if violations.empty:
        print("No active compliance violations.")
    else:
        print(violations.to_string(index=False))

    print(f"\nOutput report: {OUTPUT_REPORT_PATH}")
    print(f"Output summary: {OUTPUT_SUMMARY_PATH}")


if __name__ == "__main__":
    main()