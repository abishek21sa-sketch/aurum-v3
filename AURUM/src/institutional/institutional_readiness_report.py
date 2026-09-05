from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


RESULTS_DIR = Path("results/institutional")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

AUDIT_PATH = RESULTS_DIR / "runtime_integrity_audit.json"
GATE_PATH = RESULTS_DIR / "runtime_coherence_gate.json"
RUNTIME_STATE_PATH = RESULTS_DIR / "latest_institutional_runtime_state.json"
CYCLE_PATH = RESULTS_DIR / "institutional_decision_cycle_report.json"
GOVERNANCE_PATH = Path("results/governance/execution_governance_report.json")

OUTPUT_JSON = RESULTS_DIR / "institutional_readiness_report.json"
OUTPUT_TXT = RESULTS_DIR / "institutional_readiness_report.txt"


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def extract_failed_checks(audit: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        finding
        for finding in audit.get("findings", [])
        if finding.get("status") == "FAIL"
    ]


def classify_remaining_issues(failed_checks: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    issues = {
        "production_blockers": [],
        "research_tolerated": [],
        "critical_blockers": [],
    }

    for finding in failed_checks:
        check = finding.get("check")
        severity = finding.get("severity")
        message = finding.get("message", "")

        if severity == "critical":
            issues["critical_blockers"].append(f"{check}: {message}")
            continue

        if check == "source_quality":
            issues["research_tolerated"].append(
                "Market data source is demo/synthetic; acceptable for research, not production."
            )
        elif check == "freshness":
            issues["research_tolerated"].append(
                f"Freshness issue: {message}"
            )
        elif check == "timestamp_order":
            issues["research_tolerated"].append(
                f"Timestamp sequencing issue: {message}"
            )
        else:
            issues["production_blockers"].append(f"{check}: {message}")

    return issues


def calculate_score(
    audit: Dict[str, Any],
    gate: Dict[str, Any],
    governance: Dict[str, Any],
    cycle: Dict[str, Any],
) -> int:
    score = 100

    score -= int(audit.get("critical_failures", 0) or 0) * 25
    score -= int(audit.get("high_failures", 0) or 0) * 4

    if gate.get("gate_status") == "BLOCKED":
        score -= 10

    if governance.get("governance_status") != "CLEAR":
        score -= 15

    if int(cycle.get("required_step_failures", 0) or 0) > 0:
        score -= 25

    return max(score, 0)


def determine_status(
    audit: Dict[str, Any],
    gate: Dict[str, Any],
    governance: Dict[str, Any],
    cycle: Dict[str, Any],
    issues: Dict[str, List[str]],
) -> str:
    critical_failures = int(audit.get("critical_failures", 0) or 0)
    high_failures = int(audit.get("high_failures", 0) or 0)
    required_step_failures = int(cycle.get("required_step_failures", 0) or 0)

    governance_status = governance.get("governance_status", "UNKNOWN")
    gate_status = gate.get("gate_status", "UNKNOWN")
    allow_execution = bool(gate.get("allow_execution_release", False))

    if critical_failures > 0:
        return "NOT_READY"

    if required_step_failures > 0:
        return "NOT_READY"

    if governance_status not in {"CLEAR", "WARNING"}:
        return "NOT_READY"

    if (
        critical_failures == 0
        and high_failures == 0
        and governance_status == "CLEAR"
        and gate_status == "ALLOW"
        and allow_execution
    ):
        return "PRODUCTION_READY"

    if (
        critical_failures == 0
        and governance_status == "CLEAR"
        and required_step_failures == 0
    ):
        return "RESEARCH_READY"

    return "NOT_READY"


def generate_institutional_readiness_report() -> Dict[str, Any]:
    audit = load_json(AUDIT_PATH)
    gate = load_json(GATE_PATH)
    runtime_state = load_json(RUNTIME_STATE_PATH)
    governance = load_json(GOVERNANCE_PATH)
    cycle = load_json(CYCLE_PATH)

    failed_checks = extract_failed_checks(audit)
    issues = classify_remaining_issues(failed_checks)

    score = calculate_score(
        audit=audit,
        gate=gate,
        governance=governance,
        cycle=cycle,
    )

    status = determine_status(
        audit=audit,
        gate=gate,
        governance=governance,
        cycle=cycle,
        issues=issues,
    )

    summary = runtime_state.get("summary", {})

    report = {
        "platform": "AURUM",
        "phase": "Phase 4G",
        "report": "Institutional Readiness Report",
        "overall_status": status,
        "platform_score": score,
        "research_ready": status in {"RESEARCH_READY", "PRODUCTION_READY"},
        "production_ready": status == "PRODUCTION_READY",
        "architecture_status": "PASS"
        if int(cycle.get("required_step_failures", 0) or 0) == 0
        else "FAIL",
        "decision_cycle_status": cycle.get("cycle_status"),
        "runtime_integrity_status": audit.get("readiness_status"),
        "coherence_gate_status": gate.get("gate_status"),
        "governance_status": governance.get("governance_status"),
        "execution_release_allowed": gate.get("allow_execution_release"),
        "current_runtime_summary": summary,
        "critical_failures": audit.get("critical_failures"),
        "high_failures": audit.get("high_failures"),
        "hard_blocks": gate.get("hard_block_count"),
        "soft_blocks": gate.get("soft_block_count"),
        "remaining_issues": issues,
        "interpretation": build_interpretation(status, issues),
    }

    save_report(report)
    return report


def build_interpretation(status: str, issues: Dict[str, List[str]]) -> str:
    if status == "PRODUCTION_READY":
        return (
            "AURUM is cleared for production-style institutional decision and "
            "execution release under the current runtime controls."
        )

    if status == "RESEARCH_READY":
        return (
            "AURUM is institutionally coherent as a research-grade real-time "
            "market laboratory. It is not production-ready because remaining "
            "issues are related to demo/synthetic data, stale non-critical streams, "
            "or timestamp sequencing."
        )

    return (
        "AURUM is not ready. Critical architecture, governance, or runtime-control "
        "issues remain and must be resolved before institutional use."
    )


def save_report(report: Dict[str, Any]) -> None:
    with OUTPUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    lines = []
    lines.append("=" * 80)
    lines.append("AURUM INSTITUTIONAL READINESS REPORT")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"Overall Status: {report['overall_status']}")
    lines.append(f"Platform Score: {report['platform_score']} / 100")
    lines.append("")
    lines.append("READINESS")
    lines.append("-" * 80)
    lines.append(f"Research Ready: {report['research_ready']}")
    lines.append(f"Production Ready: {report['production_ready']}")
    lines.append(f"Architecture Status: {report['architecture_status']}")
    lines.append(f"Decision Cycle Status: {report['decision_cycle_status']}")
    lines.append(f"Runtime Integrity: {report['runtime_integrity_status']}")
    lines.append(f"Coherence Gate: {report['coherence_gate_status']}")
    lines.append(f"Governance Status: {report['governance_status']}")
    lines.append(f"Execution Release Allowed: {report['execution_release_allowed']}")
    lines.append("")
    lines.append("CURRENT RUNTIME STATE")
    lines.append("-" * 80)

    for key, value in report["current_runtime_summary"].items():
        lines.append(f"{key}: {value}")

    lines.append("")
    lines.append("FAILURE COUNTS")
    lines.append("-" * 80)
    lines.append(f"Critical Failures: {report['critical_failures']}")
    lines.append(f"High Failures: {report['high_failures']}")
    lines.append(f"Hard Blocks: {report['hard_blocks']}")
    lines.append(f"Soft Blocks: {report['soft_blocks']}")
    lines.append("")

    lines.append("REMAINING ISSUES")
    lines.append("-" * 80)

    for category, items in report["remaining_issues"].items():
        lines.append(category.upper())
        if not items:
            lines.append("  None")
        else:
            for item in items:
                lines.append(f"  - {item}")

    lines.append("")
    lines.append("INTERPRETATION")
    lines.append("-" * 80)
    lines.append(report["interpretation"])

    OUTPUT_TXT.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    result = generate_institutional_readiness_report()

    print("=" * 80)
    print("AURUM INSTITUTIONAL READINESS REPORT")
    print("=" * 80)
    print(f"Overall Status: {result['overall_status']}")
    print(f"Platform Score: {result['platform_score']} / 100")
    print(f"Research Ready: {result['research_ready']}")
    print(f"Production Ready: {result['production_ready']}")
    print(f"Saved: {OUTPUT_JSON}")
    print(f"Saved: {OUTPUT_TXT}")