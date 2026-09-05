from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


RESULTS_DIR = Path("results/institutional")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

AUDIT_PATH = RESULTS_DIR / "runtime_integrity_audit.json"
GATE_JSON_PATH = RESULTS_DIR / "runtime_coherence_gate.json"
GATE_TXT_PATH = RESULTS_DIR / "runtime_coherence_gate.txt"


HARD_BLOCK_CHECKS = {
    "freshness",
    "source_quality",
    "regime_decision_consistency",
    "execution_lifecycle",
}

SOFT_BLOCK_CHECKS = {
    "timestamp_order",
    "decision_traceability",
}


def load_audit() -> Dict[str, Any]:
    if not AUDIT_PATH.exists():
        from src.institutional.runtime_integrity_auditor import (
            run_runtime_integrity_audit,
        )

        return run_runtime_integrity_audit()

    with AUDIT_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def classify_findings(findings: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    hard_blocks = []
    soft_blocks = []
    warnings = []
    passes = []

    for finding in findings:
        status = finding.get("status")
        severity = finding.get("severity")
        check = finding.get("check")

        if status == "PASS":
            passes.append(finding)
            continue

        if check in HARD_BLOCK_CHECKS and severity in {"critical", "high"}:
            hard_blocks.append(finding)
        elif check in SOFT_BLOCK_CHECKS and severity in {"critical", "high"}:
            soft_blocks.append(finding)
        else:
            warnings.append(finding)

    return {
        "hard_blocks": hard_blocks,
        "soft_blocks": soft_blocks,
        "warnings": warnings,
        "passes": passes,
    }


def gate_decision(audit: Dict[str, Any]) -> Dict[str, Any]:
    findings = audit.get("findings", [])
    classified = classify_findings(findings)

    hard_blocks = classified["hard_blocks"]
    soft_blocks = classified["soft_blocks"]
    warnings = classified["warnings"]

    allow_decision = len(hard_blocks) == 0
    allow_execution = len(hard_blocks) == 0 and len(soft_blocks) == 0

    if hard_blocks:
        gate_status = "BLOCKED"
        institutional_readiness = "NOT_READY"
    elif soft_blocks:
        gate_status = "REVIEW_REQUIRED"
        institutional_readiness = "CONDITIONALLY_READY"
    elif warnings:
        gate_status = "ALLOW_WITH_WARNINGS"
        institutional_readiness = "READY_WITH_MONITORING"
    else:
        gate_status = "ALLOW"
        institutional_readiness = "READY"

    hard_reasons = [
        {
            "check": f.get("check"),
            "severity": f.get("severity"),
            "message": f.get("message"),
            "evidence": f.get("evidence"),
        }
        for f in hard_blocks
    ]

    soft_reasons = [
        {
            "check": f.get("check"),
            "severity": f.get("severity"),
            "message": f.get("message"),
            "evidence": f.get("evidence"),
        }
        for f in soft_blocks
    ]

    warning_reasons = [
        {
            "check": f.get("check"),
            "severity": f.get("severity"),
            "message": f.get("message"),
            "evidence": f.get("evidence"),
        }
        for f in warnings
    ]

    report = {
        "platform": "AURUM",
        "phase": "Phase 4G",
        "control": "Runtime Coherence Gate",
        "gate_status": gate_status,
        "institutional_readiness": institutional_readiness,
        "allow_new_portfolio_decision": allow_decision,
        "allow_execution_release": allow_execution,
        "hard_block_count": len(hard_blocks),
        "soft_block_count": len(soft_blocks),
        "warning_count": len(warnings),
        "hard_blocks": hard_reasons,
        "soft_blocks": soft_reasons,
        "warnings": warning_reasons,
        "source_audit_readiness": audit.get("readiness_status"),
        "source_audit_critical_failures": audit.get("critical_failures"),
        "source_audit_high_failures": audit.get("high_failures"),
    }

    return report


def save_gate_report(report: Dict[str, Any]) -> None:
    with GATE_JSON_PATH.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    lines = []
    lines.append("=" * 80)
    lines.append("AURUM RUNTIME COHERENCE GATE")
    lines.append("=" * 80)
    lines.append(f"Gate Status: {report['gate_status']}")
    lines.append(f"Institutional Readiness: {report['institutional_readiness']}")
    lines.append(f"Allow New Portfolio Decision: {report['allow_new_portfolio_decision']}")
    lines.append(f"Allow Execution Release: {report['allow_execution_release']}")
    lines.append("")
    lines.append(f"Hard Blocks: {report['hard_block_count']}")
    lines.append(f"Soft Blocks: {report['soft_block_count']}")
    lines.append(f"Warnings: {report['warning_count']}")
    lines.append("")

    if report["hard_blocks"]:
        lines.append("HARD BLOCKS")
        lines.append("-" * 80)
        for item in report["hard_blocks"]:
            lines.append(
                f"[{item['severity'].upper()}] "
                f"{item['check']} | {item['message']}"
            )
        lines.append("")

    if report["soft_blocks"]:
        lines.append("SOFT BLOCKS")
        lines.append("-" * 80)
        for item in report["soft_blocks"]:
            lines.append(
                f"[{item['severity'].upper()}] "
                f"{item['check']} | {item['message']}"
            )
        lines.append("")

    if report["warnings"]:
        lines.append("WARNINGS")
        lines.append("-" * 80)
        for item in report["warnings"]:
            lines.append(
                f"[{item['severity'].upper()}] "
                f"{item['check']} | {item['message']}"
            )
        lines.append("")

    lines.append("INSTITUTIONAL CONTROL INTERPRETATION")
    lines.append("-" * 80)

    if report["gate_status"] == "BLOCKED":
        lines.append(
            "Trading decisions and execution releases are blocked until runtime "
            "freshness, source quality, and stream consistency are restored."
        )
    elif report["gate_status"] == "REVIEW_REQUIRED":
        lines.append(
            "Portfolio decisions may be reviewed, but execution release requires "
            "human/institutional approval due to runtime sequencing concerns."
        )
    elif report["gate_status"] == "ALLOW_WITH_WARNINGS":
        lines.append(
            "System may operate, but warnings should remain visible to the operator."
        )
    else:
        lines.append("System is coherent and cleared for decision and execution release.")

    GATE_TXT_PATH.write_text("\n".join(lines), encoding="utf-8")


def run_runtime_coherence_gate() -> Dict[str, Any]:
    audit = load_audit()
    report = gate_decision(audit)
    save_gate_report(report)
    return report


if __name__ == "__main__":
    result = run_runtime_coherence_gate()

    print("=" * 80)
    print("AURUM RUNTIME COHERENCE GATE")
    print("=" * 80)
    print(f"Gate Status: {result['gate_status']}")
    print(f"Institutional Readiness: {result['institutional_readiness']}")
    print(f"Allow New Portfolio Decision: {result['allow_new_portfolio_decision']}")
    print(f"Allow Execution Release: {result['allow_execution_release']}")
    print(f"Saved: {GATE_JSON_PATH}")
    print(f"Saved: {GATE_TXT_PATH}")