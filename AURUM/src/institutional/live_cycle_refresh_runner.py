from __future__ import annotations

import importlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


RESULTS_DIR = Path("results/institutional")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

REFRESH_JSON = RESULTS_DIR / "live_cycle_refresh_report.json"
REFRESH_TXT = RESULTS_DIR / "live_cycle_refresh_report.txt"


LIVE_CYCLE_STEPS = [
    {
        "step": "market_tick_gateway",
        "module": "src.realtime.market_data_gateway",
        "description": "Produce fresh market ticks.",
        "required": False,
    },
    {
        "step": "feature_stream_processor",
        "module": "src.realtime.feature_stream_processor",
        "description": "Produce fresh market features.",
        "required": False,
    },
    {
        "step": "live_digital_twin_state_engine",
        "module": "src.digital_twin.live_digital_twin_state_engine",
        "description": "Produce fresh digital twin market state.",
        "required": True,
    },
    {
        "step": "realtime_risk_projection_engine",
        "module": "src.digital_twin.realtime_risk_projection_engine",
        "description": "Produce fresh risk projection.",
        "required": True,
    },
    {
        "step": "realtime_decision_orchestrator",
        "module": "src.digital_twin.realtime_decision_orchestrator",
        "description": "Produce fresh optimizer trigger and portfolio decision.",
        "required": True,
    },
    {
        "step": "portfolio_rebalance_simulation_engine",
        "module": "src.simulation.portfolio_rebalance_simulation_engine",
        "description": "Produce fresh rebalance recommendation.",
        "required": False,
    },
    {
        "step": "execution_order_router",
        "module": "src.execution.execution_order_router",
        "description": "Produce fresh execution order.",
        "required": False,
    },
    {
        "step": "trade_ticket_generator",
        "module": "src.execution.trade_ticket_generator",
        "description": "Produce fresh trade ticket.",
        "required": False,
    },
]


def module_exists(module_name: str) -> bool:
    try:
        importlib.import_module(module_name)
        return True
    except Exception:
        return False


def run_module(module_name: str, timeout_seconds: int = 30) -> Dict[str, Any]:
    started = datetime.now(timezone.utc)

    try:
        result = subprocess.run(
            [sys.executable, "-m", module_name],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )

        ended = datetime.now(timezone.utc)

        return {
            "module": module_name,
            "status": "PASS" if result.returncode == 0 else "FAIL",
            "returncode": result.returncode,
            "started_at": started.isoformat(),
            "ended_at": ended.isoformat(),
            "stdout_tail": result.stdout[-3000:],
            "stderr_tail": result.stderr[-3000:],
        }

    except subprocess.TimeoutExpired as exc:
        ended = datetime.now(timezone.utc)

        return {
            "module": module_name,
            "status": "TIMEOUT",
            "returncode": None,
            "started_at": started.isoformat(),
            "ended_at": ended.isoformat(),
            "stdout_tail": str(exc.stdout)[-3000:] if exc.stdout else "",
            "stderr_tail": str(exc.stderr)[-3000:] if exc.stderr else "",
        }

    except Exception as exc:
        ended = datetime.now(timezone.utc)

        return {
            "module": module_name,
            "status": "FAIL",
            "returncode": None,
            "started_at": started.isoformat(),
            "ended_at": ended.isoformat(),
            "stdout_tail": "",
            "stderr_tail": str(exc),
        }


def rerun_integrity_stack() -> Dict[str, Any]:
    from src.institutional.runtime_integrity_auditor import (
        run_runtime_integrity_audit,
    )
    from src.institutional.runtime_coherence_gate import (
        run_runtime_coherence_gate,
    )

    audit = run_runtime_integrity_audit()
    gate = run_runtime_coherence_gate()

    return {
        "audit_readiness": audit.get("readiness_status"),
        "critical_failures": audit.get("critical_failures"),
        "high_failures": audit.get("high_failures"),
        "gate_status": gate.get("gate_status"),
        "allow_new_portfolio_decision": gate.get("allow_new_portfolio_decision"),
        "allow_execution_release": gate.get("allow_execution_release"),
    }


def run_live_cycle_refresh() -> Dict[str, Any]:
    print("=" * 80)
    print("AURUM LIVE CYCLE REFRESH RUNNER")
    print("=" * 80)

    step_results: List[Dict[str, Any]] = []

    for item in LIVE_CYCLE_STEPS:
        step = item["step"]
        module = item["module"]
        required = item["required"]

        print(f"\nRUNNING STEP: {step}")
        print("-" * 80)
        print(f"Module: {module}")

        if not module_exists(module):
            status = "MISSING_REQUIRED" if required else "MISSING_OPTIONAL"
            print(f"[{status}] {module}")

            step_results.append(
                {
                    "step": step,
                    "module": module,
                    "description": item["description"],
                    "required": required,
                    "status": status,
                    "result": None,
                }
            )
            continue

        result = run_module(module)

        print(f"[{result['status']}] {module}")

        if result.get("stdout_tail"):
            print(result["stdout_tail"][-1200:])

        if result.get("stderr_tail"):
            print(result["stderr_tail"][-1200:])

        step_results.append(
            {
                "step": step,
                "module": module,
                "description": item["description"],
                "required": required,
                "status": result["status"],
                "result": result,
            }
        )

    print("\nRERUNNING INTEGRITY STACK")
    print("-" * 80)

    integrity = rerun_integrity_stack()

    print(f"Audit Readiness: {integrity['audit_readiness']}")
    print(f"Gate Status: {integrity['gate_status']}")
    print(f"Allow Decision: {integrity['allow_new_portfolio_decision']}")
    print(f"Allow Execution: {integrity['allow_execution_release']}")

    required_failures = [
        r
        for r in step_results
        if r["required"] and r["status"] not in {"PASS"}
    ]

    report = {
        "platform": "AURUM",
        "phase": "Phase 4G",
        "runner": "Live Cycle Refresh Runner",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "required_step_failures": len(required_failures),
        "steps": step_results,
        "post_refresh_integrity": integrity,
        "overall_status": (
            "PASS"
            if len(required_failures) == 0
            else "PARTIAL"
        ),
        "interpretation": (
            "PASS means required runtime engines executed. "
            "Institutional readiness is still determined by the post-refresh audit and gate."
        ),
    }

    save_report(report)

    return report


def save_report(report: Dict[str, Any]) -> None:
    with REFRESH_JSON.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    lines = []
    lines.append("=" * 80)
    lines.append("AURUM LIVE CYCLE REFRESH REPORT")
    lines.append("=" * 80)
    lines.append(f"Overall Status: {report['overall_status']}")
    lines.append(f"Required Step Failures: {report['required_step_failures']}")
    lines.append("")
    lines.append("STEP RESULTS")
    lines.append("-" * 80)

    for step in report["steps"]:
        lines.append(
            f"[{step['status']}] "
            f"{step['step']} | "
            f"{step['module']} | "
            f"required={step['required']}"
        )

    lines.append("")
    lines.append("POST-REFRESH INTEGRITY")
    lines.append("-" * 80)

    integrity = report["post_refresh_integrity"]

    for key, value in integrity.items():
        lines.append(f"{key}: {value}")

    REFRESH_TXT.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    report = run_live_cycle_refresh()

    print("\nFINAL STATUS")
    print("-" * 80)
    print(f"[{report['overall_status']}] LIVE CYCLE REFRESH COMPLETE")
    print(f"Saved: {REFRESH_JSON}")
    print(f"Saved: {REFRESH_TXT}")