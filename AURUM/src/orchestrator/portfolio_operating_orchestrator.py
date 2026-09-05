# src/orchestrator/portfolio_operating_orchestrator.py

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


OUTPUT_DIR = Path("results/orchestrator")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ORCHESTRATOR_OUTPUT = OUTPUT_DIR / "orchestrator_run.json"


PIPELINE = [
    "src.digital_twin.live_digital_twin_state_engine",
    "src.digital_twin.realtime_risk_projection_engine",
    "src.portfolio.realtime_portfolio_decision_engine",
    "src.optimization.realtime_portfolio_reoptimizer",
    "src.execution.execution_order_generator",
    "src.execution.trade_ticket_engine",
    "src.execution.portfolio_execution_simulator",
    "src.portfolio.position_management_engine",
    "src.portfolio.portfolio_lifecycle_manager",
    "src.governance.execution_audit_engine",
    "src.governance.execution_governance_engine",
    "src.governance.execution_governance_escalation",
    "src.governance.institutional_audit_report",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )


def run_module(module_name: str) -> Dict[str, Any]:

    start_time = now_utc()

    try:
        result = subprocess.run(
            [sys.executable, "-m", module_name],
            capture_output=True,
            text=True,
            timeout=300,
        )

        return {
            "module": module_name,
            "status": "PASS" if result.returncode == 0 else "FAIL",
            "returncode": result.returncode,
            "started_at": start_time,
            "finished_at": now_utc(),
            "stdout_tail": result.stdout[-1000:],
            "stderr_tail": result.stderr[-1000:],
        }

    except subprocess.TimeoutExpired:

        return {
            "module": module_name,
            "status": "TIMEOUT",
            "returncode": -1,
            "started_at": start_time,
            "finished_at": now_utc(),
            "stdout_tail": "",
            "stderr_tail": "Module execution timeout",
        }

    except Exception as exc:

        return {
            "module": module_name,
            "status": "FAIL",
            "returncode": -1,
            "started_at": start_time,
            "finished_at": now_utc(),
            "stdout_tail": "",
            "stderr_tail": str(exc),
        }


def run_portfolio_operating_orchestrator() -> Dict[str, Any]:

    print("=" * 80)
    print("AURUM PORTFOLIO OPERATING ORCHESTRATOR")
    print("=" * 80)

    module_results: List[Dict[str, Any]] = []

    for module_name in PIPELINE:

        print(f"Running: {module_name}")

        result = run_module(module_name)

        module_results.append(result)

        status = result["status"]

        print(f"  [{status}] {module_name}")

    total_steps = len(module_results)

    pass_count = sum(
        1
        for r in module_results
        if r["status"] == "PASS"
    )

    fail_count = sum(
        1
        for r in module_results
        if r["status"] == "FAIL"
    )

    timeout_count = sum(
        1
        for r in module_results
        if r["status"] == "TIMEOUT"
    )

    report = {
        "event_type": "portfolio_operating_orchestrator",
        "timestamp": now_utc(),
        "portfolio_id": "AURUM_LIVE_PORTFOLIO",
        "phase": "4E.1",
        "pipeline": PIPELINE,
        "total_steps": total_steps,
        "steps_passed": pass_count,
        "steps_failed": fail_count,
        "steps_timed_out": timeout_count,
        "success_rate": round(
            pass_count / total_steps,
            4,
        )
        if total_steps > 0
        else 0.0,
        "status": (
            "PASS"
            if pass_count == total_steps
            else "PARTIAL_FAILURE"
        ),
        "module_results": module_results,
    }

    save_json(
        ORCHESTRATOR_OUTPUT,
        report,
    )

    return report


def print_summary(report: Dict[str, Any]) -> None:

    print("-" * 80)

    print(f"Status:         {report['status']}")
    print(f"Steps Passed:   {report['steps_passed']}")
    print(f"Steps Failed:   {report['steps_failed']}")
    print(f"Timed Out:      {report['steps_timed_out']}")
    print(f"Success Rate:   {report['success_rate']:.2%}")

    print("-" * 80)

    for result in report["module_results"]:

        print(
            f"{result['status']:8} | "
            f"{result['module']}"
        )

    print("-" * 80)
    print(f"Saved: {ORCHESTRATOR_OUTPUT}")


def main() -> None:

    report = run_portfolio_operating_orchestrator()

    print_summary(report)


if __name__ == "__main__":
    main()