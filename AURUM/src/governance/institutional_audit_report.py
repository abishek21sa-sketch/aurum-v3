# src/governance/institutional_audit_report.py

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from src.governance.audit_cycle_manager import get_current_audit_cycle


OUTPUT_DIR = Path("results/governance")
EXECUTION_DIR = Path("results/execution")
PORTFOLIO_DIR = Path("results/portfolio")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

AUDIT_LOG_PATH = OUTPUT_DIR / "execution_audit_log.jsonl"
CURRENT_CYCLE_AUDIT_LOG_PATH = OUTPUT_DIR / "current_cycle_audit_log.jsonl"
GOVERNANCE_REPORT_PATH = OUTPUT_DIR / "execution_governance_report.json"
ALERTS_PATH = OUTPUT_DIR / "governance_alerts.json"

REPORT_JSON_PATH = OUTPUT_DIR / "institutional_audit_report.json"
REPORT_TXT_PATH = OUTPUT_DIR / "institutional_audit_report.txt"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []

    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    return rows


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def save_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run_institutional_audit_report() -> Dict[str, Any]:
    cycle = get_current_audit_cycle()
    cycle_id = cycle["cycle_id"]

    orders = load_json(EXECUTION_DIR / "execution_orders.json", [])
    tickets = load_json(EXECUTION_DIR / "trade_tickets.json", [])
    reports = load_json(EXECUTION_DIR / "execution_reports.json", [])
    state = load_json(PORTFOLIO_DIR / "institutional_portfolio_state.json", {})
    all_audit_records = load_jsonl(AUDIT_LOG_PATH)
    current_cycle_records = load_jsonl(CURRENT_CYCLE_AUDIT_LOG_PATH)
    governance_report = load_json(GOVERNANCE_REPORT_PATH, {})
    alerts = load_json(ALERTS_PATH, [])

    execution_state = state.get("execution_state", {})
    position_state = state.get("position_state", {})
    optimization_state = state.get("optimization_state", {})

    stale_records = [
        r for r in all_audit_records if not bool(r.get("is_current_cycle", True))
    ]

    report = {
        "report_type": "AURUM_GOVERNANCE_CERTIFIED_AUDIT_REPORT",
        "timestamp": now_utc(),
        "cycle_id": cycle_id,
        "portfolio_id": state.get("portfolio_id", "AURUM_LIVE_PORTFOLIO"),
        "lifecycle_status": state.get("lifecycle_status", "UNKNOWN"),
        "optimizer_source": optimization_state.get("source", "unknown"),
        "target_assets": optimization_state.get("target_assets", 0),
        "governance_status": governance_report.get("governance_status", "UNKNOWN"),
        "governance_score": governance_report.get("governance_score", 0),
        "orders_generated": len(orders),
        "tickets_generated": len(tickets),
        "execution_reports": len(reports),
        "audit_records_all_time": len(all_audit_records),
        "audit_records_current_cycle": len(current_cycle_records),
        "stale_audit_records": len(stale_records),
        "alerts_generated": len(alerts),
        "fill_ratio": execution_state.get("aggregate_fill_ratio", 0.0),
        "execution_cost_bps": execution_state.get("total_execution_cost_bps", 0.0),
        "gross_exposure": position_state.get("gross_exposure", 0.0),
        "cash_weight": position_state.get("cash_weight", 0.0),
        "violations": governance_report.get("violations", []),
        "latest_current_cycle_audit_records": current_cycle_records[-20:],
        "latest_stale_records": stale_records[-10:],
        "alerts": alerts,
        "certification_status": "CERTIFIED"
        if governance_report.get("governance_status") == "CLEAR"
        and len(alerts) == 0
        else "REVIEW_REQUIRED",
    }

    save_json(REPORT_JSON_PATH, report)

    text = f"""
AURUM GOVERNANCE-CERTIFIED AUDIT REPORT
================================================================================
Timestamp: {report['timestamp']}
Cycle ID: {report['cycle_id']}
Portfolio ID: {report['portfolio_id']}
Lifecycle Status: {report['lifecycle_status']}
Optimizer Source: {report['optimizer_source']}
Target Assets: {report['target_assets']}

GOVERNANCE
--------------------------------------------------------------------------------
Governance Status:      {report['governance_status']}
Governance Score:       {report['governance_score']}
Violations:             {len(report['violations'])}
Alerts Generated:       {report['alerts_generated']}
Certification Status:   {report['certification_status']}

EXECUTION SUMMARY
--------------------------------------------------------------------------------
Orders Generated:       {report['orders_generated']}
Tickets Generated:      {report['tickets_generated']}
Execution Reports:      {report['execution_reports']}

AUDIT SUMMARY
--------------------------------------------------------------------------------
All-Time Audit Records:       {report['audit_records_all_time']}
Current-Cycle Audit Records:  {report['audit_records_current_cycle']}
Stale Audit Records:          {report['stale_audit_records']}

EXECUTION QUALITY
--------------------------------------------------------------------------------
Fill Ratio:             {float(report['fill_ratio']):.2%}
Execution Cost:         {report['execution_cost_bps']} bps

PORTFOLIO STATE
--------------------------------------------------------------------------------
Gross Exposure:         {float(report['gross_exposure']):.2%}
Cash Weight:            {float(report['cash_weight']):.2%}

FINAL VERDICT
--------------------------------------------------------------------------------
{report['certification_status']}
================================================================================
""".strip()

    save_text(REPORT_TXT_PATH, text)

    return report


def main() -> None:
    print("=" * 80)
    print("AURUM GOVERNANCE-CERTIFIED AUDIT REPORT")
    print("=" * 80)

    report = run_institutional_audit_report()

    print(f"Cycle ID: {report['cycle_id']}")
    print(f"Portfolio ID: {report['portfolio_id']}")
    print(f"Lifecycle Status: {report['lifecycle_status']}")
    print(f"Optimizer Source: {report['optimizer_source']}")
    print(f"Governance Status: {report['governance_status']}")
    print(f"Governance Score: {report['governance_score']}")
    print(f"Certification: {report['certification_status']}")
    print(f"Current-Cycle Audit Records: {report['audit_records_current_cycle']}")
    print(f"Stale Audit Records: {report['stale_audit_records']}")
    print("-" * 80)
    print(f"Saved JSON: {REPORT_JSON_PATH}")
    print(f"Saved TXT:  {REPORT_TXT_PATH}")


if __name__ == "__main__":
    main()