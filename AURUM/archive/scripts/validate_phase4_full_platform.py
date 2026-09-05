# scripts/validate_phase4_full_platform.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, List


def banner(title: str) -> None:
    print("=" * 80)
    print(title)
    print("=" * 80)


def section(title: str) -> None:
    print("-" * 80)
    print(title)
    print("-" * 80)


def load_json(path: Path, default: Any = None) -> Any:
    if default is None:
        default = {}

    if not path.exists():
        return default

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def check_file(path: str, label: str, results: List[Dict[str, Any]]) -> None:
    p = Path(path)

    if p.exists():
        print(f"[PASS] {label} | {path}")
        results.append({"check": label, "status": "PASS", "path": path})
    else:
        print(f"[FAIL] {label} | missing {path}")
        results.append({"check": label, "status": "FAIL", "path": path})


def check_condition(
    condition: bool,
    label: str,
    results: List[Dict[str, Any]],
    detail: str = "",
) -> None:
    if condition:
        print(f"[PASS] {label}" + (f" | {detail}" if detail else ""))
        results.append({"check": label, "status": "PASS", "detail": detail})
    else:
        print(f"[FAIL] {label}" + (f" | {detail}" if detail else ""))
        results.append({"check": label, "status": "FAIL", "detail": detail})


def run_step(
    label: str,
    fn: Callable[[], Dict[str, Any]],
    results: List[Dict[str, Any]],
) -> Dict[str, Any]:
    try:
        output = fn()
        print(f"[PASS] {label}")
        results.append({"check": label, "status": "PASS"})
        return output
    except Exception as exc:
        print(f"[FAIL] {label} | {exc}")
        results.append({"check": label, "status": "FAIL", "error": str(exc)})
        return {}


def main() -> None:
    banner("AURUM PHASE 4 FULL PLATFORM VALIDATION")

    results: List[Dict[str, Any]] = []

    section("RUNNING CORE PHASE 4 ENGINES")

    from src.orchestrator.autonomous_operating_cycle import (
        run_autonomous_operating_cycle,
    )
    from src.monitoring.live_performance_engine import (
        run_live_performance_engine,
    )
    from src.monitoring.risk_history_engine import (
        run_risk_history_engine,
    )
    from src.monitoring.event_stream_monitor import (
        run_event_stream_monitor,
    )

    operating_cycle = run_step(
        "Autonomous Operating Cycle",
        run_autonomous_operating_cycle,
        results,
    )

    performance = run_step(
        "Live Performance Engine",
        run_live_performance_engine,
        results,
    )

    risk_history = run_step(
        "Risk History Engine",
        run_risk_history_engine,
        results,
    )

    event_streams = run_step(
        "Event Stream Monitor",
        run_event_stream_monitor,
        results,
    )

    section("OUTPUT FILE CHECKS")

    output_files = [
        ("results/orchestrator/orchestrator_run.json", "orchestrator run"),
        ("results/orchestrator/operating_cycle.json", "operating cycle"),
        ("results/orchestrator/event_triggers.json", "event triggers"),
        ("results/orchestrator/rebalance_schedule.json", "rebalance schedule"),
        ("results/orchestrator/decision_approval.json", "decision approval"),
        ("results/portfolio/institutional_portfolio_state.json", "institutional portfolio state"),
        ("results/portfolio/live_positions.json", "live positions"),
        ("results/governance/execution_governance_report.json", "execution governance report"),
        ("results/governance/institutional_audit_report.json", "institutional audit report"),
        ("results/memory/portfolio_memory.jsonl", "portfolio memory log"),
        ("results/memory/memory_summary.json", "memory summary"),
        ("results/ai/cio_daily_brief.json", "AI CIO JSON brief"),
        ("results/ai/cio_daily_brief.txt", "AI CIO text brief"),
        ("results/monitoring/live_performance_snapshot.json", "performance snapshot"),
        ("results/monitoring/live_performance_summary.json", "performance summary"),
        ("results/monitoring/performance_history.jsonl", "performance history"),
        ("results/monitoring/risk_snapshot.json", "risk snapshot"),
        ("results/monitoring/risk_history_summary.json", "risk history summary"),
        ("results/monitoring/risk_history.jsonl", "risk history"),
        ("results/monitoring/event_stream_snapshot.json", "event stream snapshot"),
        ("results/monitoring/event_stream_summary.json", "event stream summary"),
        ("results/monitoring/event_stream_history.jsonl", "event stream history"),
    ]

    for path, label in output_files:
        check_file(path, label, results)

    section("PLATFORM STATE CHECKS")

    oc = load_json(Path("results/orchestrator/operating_cycle.json"))
    perf_summary = load_json(Path("results/monitoring/live_performance_summary.json"))
    risk_summary = load_json(Path("results/monitoring/risk_history_summary.json"))
    stream_summary = load_json(Path("results/monitoring/event_stream_summary.json"))
    approval = load_json(Path("results/orchestrator/decision_approval.json"))
    governance = load_json(Path("results/governance/execution_governance_report.json"))
    memory = load_json(Path("results/memory/memory_summary.json"))
    cio = load_json(Path("results/ai/cio_daily_brief.json"))

    check_condition(
        oc.get("overall_status") == "PASS",
        "operating cycle PASS",
        results,
        str(oc.get("overall_status")),
    )

    check_condition(
        oc.get("orchestrator_status") == "PASS",
        "orchestrator PASS",
        results,
        str(oc.get("orchestrator_status")),
    )

    check_condition(
        oc.get("trigger_count", 0) >= 0,
        "trigger engine valid",
        results,
        f"triggers={oc.get('trigger_count')}",
    )

    check_condition(
        approval.get("status") in ["APPROVED", "ESCALATED", "REJECTED"],
        "approval workflow valid",
        results,
        str(approval.get("status")),
    )

    check_condition(
        governance.get("governance_status") in ["CLEAR", "REVIEW_REQUIRED", "BREACH"],
        "governance status valid",
        results,
        str(governance.get("governance_status")),
    )

    check_condition(
        memory.get("total_cycles", 0) >= 1,
        "memory layer valid",
        results,
        f"cycles={memory.get('total_cycles')}",
    )

    check_condition(
        "recommended_action" in cio,
        "AI CIO brief valid",
        results,
        cio.get("recommended_action", ""),
    )

    check_condition(
        perf_summary.get("history_points", 0) >= 1,
        "performance history valid",
        results,
        f"points={perf_summary.get('history_points')}",
    )

    check_condition(
        risk_summary.get("history_points", 0) >= 1,
        "risk history valid",
        results,
        f"points={risk_summary.get('history_points')}",
    )

    check_condition(
        stream_summary.get("health_status") in ["HEALTHY", "DEGRADED"],
        "event stream monitor valid",
        results,
        str(stream_summary.get("health_status")),
    )

    check_condition(
        stream_summary.get("active_streams", 0) >= 10,
        "stream coverage valid",
        results,
        f"active={stream_summary.get('active_streams')}",
    )

    section("PHASE COMPLETION CHECKS")

    phase_checks = {
        "4A_real_time_infrastructure": stream_summary.get("active_streams", 0) >= 3,
        "4B_realtime_decision_layer": Path("results/portfolio/institutional_portfolio_state.json").exists(),
        "4C_realtime_optimization": Path("results/optimization/realtime_optimized_portfolio.json").exists(),
        "4D_execution_governance": Path("results/governance/institutional_audit_report.json").exists(),
        "4E_autonomous_operating_system": oc.get("overall_status") == "PASS",
        "4F_monitoring_command_center": (
            perf_summary.get("history_points", 0) >= 1
            and risk_summary.get("history_points", 0) >= 1
            and stream_summary.get("health_status") in ["HEALTHY", "DEGRADED"]
        ),
    }

    for label, passed in phase_checks.items():
        check_condition(passed, label, results)

    section("FINAL VERDICT")

    failed = [r for r in results if r["status"] == "FAIL"]
    passed = [r for r in results if r["status"] == "PASS"]

    platform_status = "PRODUCTION_READY_SIMULATION" if not failed else "NEEDS_ATTENTION"

    print(f"Passed Checks: {len(passed)}")
    print(f"Failed Checks: {len(failed)}")
    print(f"Platform Status: {platform_status}")

    report = {
        "report_type": "AURUM_PHASE4_FULL_PLATFORM_VALIDATION",
        "platform_status": platform_status,
        "passed_checks": len(passed),
        "failed_checks": len(failed),
        "failures": failed,
        "results": results,
    }

    output_path = Path("results/monitoring/phase4_full_platform_validation.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Saved: {output_path}")

    if failed:
        raise SystemExit(1)

    print("=" * 80)
    print("[PASS] AURUM PHASE 4 FULL PLATFORM VALIDATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()