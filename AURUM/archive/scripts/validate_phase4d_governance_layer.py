# scripts/validate_phase4d_governance_layer.py

from __future__ import annotations

import importlib
import json
import os
from pathlib import Path

import redis


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

OUTPUTS = [
    Path("results/governance/execution_audit_log.jsonl"),
    Path("results/governance/current_cycle_audit_log.jsonl"),
    Path("results/governance/execution_audit_summary.json"),
    Path("results/governance/execution_governance_report.json"),
    Path("results/governance/governance_alerts.json"),
    Path("results/governance/institutional_audit_report.json"),
    Path("results/governance/institutional_audit_report.txt"),
]

STREAMS = [
    "execution_audit",
    "governance_events",
]


def check_import(module_name: str) -> bool:
    try:
        importlib.import_module(module_name)
        print(f"[PASS] import {module_name}")
        return True
    except Exception as exc:
        print(f"[FAIL] import {module_name}: {exc}")
        return False


def check_file(path: Path) -> bool:
    if not path.exists():
        print(f"[FAIL] missing output: {path}")
        return False

    if path.suffix == ".json":
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"[FAIL] invalid JSON: {path} | {exc}")
            return False

    if path.suffix == ".jsonl" and path.stat().st_size == 0:
        print(f"[FAIL] empty JSONL: {path}")
        return False

    print(f"[PASS] output exists: {path}")
    return True


def check_stream(stream: str) -> bool:
    try:
        r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        r.ping()
        length = r.xlen(stream)

        if length <= 0:
            print(f"[FAIL] Redis stream empty: {stream}")
            return False

        print(f"[PASS] Redis stream active: {stream} | length={length}")
        return True

    except Exception as exc:
        print(f"[FAIL] Redis stream check failed: {stream} | {exc}")
        return False


def check_hardened_audit_schema(audit_report: dict) -> bool:
    required = [
        "cycle_id",
        "optimizer_source",
        "certification_status",
        "audit_records_all_time",
        "audit_records_current_cycle",
        "stale_audit_records",
        "governance_status",
        "governance_score",
    ]

    missing = [field for field in required if field not in audit_report]

    if missing:
        print(f"[FAIL] hardened audit report missing fields: {missing}")
        return False

    if audit_report.get("certification_status") not in {
        "CERTIFIED",
        "REVIEW_REQUIRED",
    }:
        print(
            "[FAIL] invalid certification status: "
            f"{audit_report.get('certification_status')}"
        )
        return False

    if int(audit_report.get("audit_records_current_cycle", 0)) <= 0:
        print("[FAIL] no current-cycle audit records")
        return False

    print(
        "[PASS] hardened audit schema valid | "
        f"cycle={audit_report['cycle_id']} "
        f"certification={audit_report['certification_status']} "
        f"current_cycle={audit_report['audit_records_current_cycle']} "
        f"stale={audit_report['stale_audit_records']}"
    )
    return True


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 4D GOVERNANCE LAYER VALIDATION")
    print("=" * 80)

    checks = []

    modules = [
        "src.governance.execution_audit_engine",
        "src.governance.execution_governance_engine",
        "src.governance.execution_governance_escalation",
        "src.governance.institutional_audit_report",
        "src.governance.audit_cycle_manager",
    ]

    for module in modules:
        checks.append(check_import(module))

    print("-" * 80)
    print("RUNNING GOVERNANCE PIPELINE")
    print("-" * 80)

    try:
        from src.governance.execution_audit_engine import run_execution_audit_engine

        records = run_execution_audit_engine()
        print(f"[PASS] audit engine ran | new_records={len(records)}")
        checks.append(True)
    except Exception as exc:
        print(f"[FAIL] audit engine failed: {exc}")
        checks.append(False)

    try:
        from src.governance.execution_governance_engine import (
            run_execution_governance_engine,
        )

        report = run_execution_governance_engine()
        print(
            f"[PASS] governance engine ran | "
            f"status={report['governance_status']} "
            f"score={report['governance_score']}"
        )
        checks.append(True)
    except Exception as exc:
        print(f"[FAIL] governance engine failed: {exc}")
        checks.append(False)

    try:
        from src.governance.execution_governance_escalation import (
            run_execution_governance_escalation,
        )

        alerts = run_execution_governance_escalation()
        print(f"[PASS] escalation engine ran | alerts={len(alerts)}")
        checks.append(True)
    except Exception as exc:
        print(f"[FAIL] escalation engine failed: {exc}")
        checks.append(False)

    try:
        from src.governance.institutional_audit_report import (
            run_institutional_audit_report,
        )

        audit_report = run_institutional_audit_report()

        print(
            f"[PASS] institutional audit report ran | "
            f"current_cycle={audit_report.get('audit_records_current_cycle', 0)} "
            f"stale={audit_report.get('stale_audit_records', 0)} "
            f"certification={audit_report.get('certification_status', 'UNKNOWN')}"
        )

        checks.append(check_hardened_audit_schema(audit_report))

    except Exception as exc:
        print(f"[FAIL] institutional audit report failed: {exc}")
        checks.append(False)

    print("-" * 80)
    print("OUTPUT CHECKS")
    print("-" * 80)

    for path in OUTPUTS:
        checks.append(check_file(path))

    print("-" * 80)
    print("REDIS STREAM CHECKS")
    print("-" * 80)

    for stream in STREAMS:
        checks.append(check_stream(stream))

    print("=" * 80)

    if all(checks):
        print("[PASS] PHASE 4D GOVERNANCE LAYER VALIDATION COMPLETE")
    else:
        print("[FAIL] PHASE 4D GOVERNANCE LAYER VALIDATION FAILED")

    print("=" * 80)


if __name__ == "__main__":
    main()