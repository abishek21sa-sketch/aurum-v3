from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


RESULTS_DIR = Path("results/institutional")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

REPORT_JSON = RESULTS_DIR / "institutional_decision_cycle_report.json"
REPORT_TXT = RESULTS_DIR / "institutional_decision_cycle_report.txt"


DECISION_CYCLE = [
    {
        "step": "live_digital_twin_state",
        "module": "src.digital_twin.live_digital_twin_state_engine",
        "required": True,
    },
    {
        "step": "realtime_risk_projection",
        "module": "src.digital_twin.realtime_risk_projection_engine",
        "required": True,
    },
    {
        "step": "realtime_portfolio_decision",
        "module": "src.portfolio.realtime_portfolio_decision_engine",
        "required": True,
    },
    {
        "step": "execution_order_generation",
        "module": "src.execution.execution_order_generator",
        "required": True,
    },
    {
        "step": "trade_ticket_generation",
        "module": "src.execution.trade_ticket_engine",
        "required": True,
    },
    {
        "step": "execution_governance",
        "module": "src.governance.execution_governance_engine",
        "required": True,
    },
]


def run_module(module: str, timeout_seconds: int = 45) -> Dict[str, Any]:
    start = datetime.now(timezone.utc)

    try:
        result = subprocess.run(
            [sys.executable, "-m", module],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )

        end = datetime.now(timezone.utc)

        return {
            "module": module,
            "status": "PASS" if result.returncode == 0 else "FAIL",
            "returncode": result.returncode,
            "started_at": start.isoformat(),
            "ended_at": end.isoformat(),
            "stdout_tail": result.stdout[-4000:],
            "stderr_tail": result.stderr[-4000:],
        }

    except subprocess.TimeoutExpired as exc:
        end = datetime.now(timezone.utc)

        return {
            "module": module,
            "status": "TIMEOUT",
            "returncode": None,
            "started_at": start.isoformat(),
            "ended_at": end.isoformat(),
            "stdout_tail": str(exc.stdout)[-4000:] if exc.stdout else "",
            "stderr_tail": str(exc.stderr)[-4000:] if exc.stderr else "",
        }

    except Exception as exc:
        end = datetime.now(timezone.utc)

        return {
            "module": module,
            "status": "FAIL",
            "returncode": None,
            "started_at": start.isoformat(),
            "ended_at": end.isoformat(),
            "stdout_tail": "",
            "stderr_tail": str(exc),
        }


def run_post_cycle_controls() -> Dict[str, Any]:
    from src.institutional.runtime_integrity_auditor import (
        run_runtime_integrity_audit,
    )
    from src.institutional.runtime_coherence_gate import (
        run_runtime_coherence_gate,
    )

    audit = run_runtime_integrity_audit()
    gate = run_runtime_coherence_gate()

    return {
        "runtime_integrity": {
            "readiness_status": audit.get("readiness_status"),
            "critical_failures": audit.get("critical_failures"),
            "high_failures": audit.get("high_failures"),
            "finding_count": audit.get("finding_count"),
        },
        "runtime_coherence_gate": {
            "gate_status": gate.get("gate_status"),
            "institutional_readiness": gate.get("institutional_readiness"),
            "allow_new_portfolio_decision": gate.get("allow_new_portfolio_decision"),
            "allow_execution_release": gate.get("allow_execution_release"),
            "hard_block_count": gate.get("hard_block_count"),
            "soft_block_count": gate.get("soft_block_count"),
        },
    }


def run_institutional_decision_cycle() -> Dict[str, Any]:
    print("=" * 80)
    print("AURUM INSTITUTIONAL DECISION CYCLE ORCHESTRATOR")
    print("=" * 80)

    step_results: List[Dict[str, Any]] = []

    for item in DECISION_CYCLE:
        print("\n" + item["step"].upper())
        print("-" * 80)
        print(f"Module: {item['module']}")

        result = run_module(item["module"])

        print(f"[{result['status']}] {item['module']}")

        if result["stdout_tail"]:
            print(result["stdout_tail"][-1500:])

        if result["stderr_tail"]:
            print(result["stderr_tail"][-1500:])

        step_results.append(
            {
                "step": item["step"],
                "module": item["module"],
                "required": item["required"],
                "status": result["status"],
                "result": result,
            }
        )

    required_failures = [
        step
        for step in step_results
        if step["required"] and step["status"] != "PASS"
    ]

    print("\nPOST-CYCLE INSTITUTIONAL CONTROLS")
    print("-" * 80)

    controls = run_post_cycle_controls()

    gate = controls["runtime_coherence_gate"]
    integrity = controls["runtime_integrity"]

    print(f"Runtime Integrity: {integrity['readiness_status']}")
    print(f"Gate Status: {gate['gate_status']}")
    print(f"Allow Decision: {gate['allow_new_portfolio_decision']}")
    print(f"Allow Execution: {gate['allow_execution_release']}")

    if required_failures:
        cycle_status = "FAILED"
    elif gate["allow_execution_release"]:
        cycle_status = "EXECUTION_READY"
    elif gate["allow_new_portfolio_decision"]:
        cycle_status = "DECISION_READY_EXECUTION_BLOCKED"
    else:
        cycle_status = "BLOCKED_BY_CONTROLS"

    report = {
        "platform": "AURUM",
        "phase": "Phase 4G",
        "orchestrator": "Institutional Decision Cycle Orchestrator",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "cycle_status": cycle_status,
        "required_step_failures": len(required_failures),
        "steps": step_results,
        "post_cycle_controls": controls,
        "interpretation": (
            "This orchestrator runs the real AURUM decision chain and then applies "
            "institutional runtime integrity and coherence controls."
        ),
    }

    save_report(report)
    return report


def save_report(report: Dict[str, Any]) -> None:
    with REPORT_JSON.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    lines = []
    lines.append("=" * 80)
    lines.append("AURUM INSTITUTIONAL DECISION CYCLE REPORT")
    lines.append("=" * 80)
    lines.append(f"Cycle Status: {report['cycle_status']}")
    lines.append(f"Required Step Failures: {report['required_step_failures']}")
    lines.append("")

    lines.append("STEP RESULTS")
    lines.append("-" * 80)

    for step in report["steps"]:
        lines.append(
            f"[{step['status']}] {step['step']} | "
            f"{step['module']} | required={step['required']}"
        )

    lines.append("")
    lines.append("POST-CYCLE CONTROLS")
    lines.append("-" * 80)

    integrity = report["post_cycle_controls"]["runtime_integrity"]
    gate = report["post_cycle_controls"]["runtime_coherence_gate"]

    lines.append(f"Runtime Integrity: {integrity['readiness_status']}")
    lines.append(f"Critical Failures: {integrity['critical_failures']}")
    lines.append(f"High Failures: {integrity['high_failures']}")
    lines.append(f"Gate Status: {gate['gate_status']}")
    lines.append(f"Institutional Readiness: {gate['institutional_readiness']}")
    lines.append(f"Allow New Portfolio Decision: {gate['allow_new_portfolio_decision']}")
    lines.append(f"Allow Execution Release: {gate['allow_execution_release']}")
    lines.append(f"Hard Blocks: {gate['hard_block_count']}")
    lines.append(f"Soft Blocks: {gate['soft_block_count']}")

    REPORT_TXT.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    report = run_institutional_decision_cycle()

    print("\nFINAL STATUS")
    print("-" * 80)
    print(f"[{report['cycle_status']}] INSTITUTIONAL DECISION CYCLE COMPLETE")
    print(f"Saved: {REPORT_JSON}")
    print(f"Saved: {REPORT_TXT}")