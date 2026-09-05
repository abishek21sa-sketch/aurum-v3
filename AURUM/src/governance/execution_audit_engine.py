# src/governance/execution_audit_engine.py

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import redis

from src.governance.audit_cycle_manager import get_current_audit_cycle


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

AUDIT_STREAM = "execution_audit"

SOURCE_STREAMS = [
    "execution_orders",
    "trade_tickets",
    "execution_reports",
    "live_positions",
    "institutional_portfolio_state",
]

OUTPUT_DIR = Path("results/governance")
STATE_DIR = Path("results/governance/state")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
STATE_DIR.mkdir(parents=True, exist_ok=True)

AUDIT_LOG_PATH = OUTPUT_DIR / "execution_audit_log.jsonl"
CURRENT_CYCLE_AUDIT_LOG_PATH = OUTPUT_DIR / "current_cycle_audit_log.jsonl"
AUDIT_SUMMARY_PATH = OUTPUT_DIR / "execution_audit_summary.json"
PROCESSED_EVENTS_PATH = STATE_DIR / "processed_audit_events.json"


@dataclass
class AuditRecord:
    audit_id: str
    cycle_id: str
    timestamp: str
    source_stream: str
    event_type: str
    portfolio_id: str
    entity_id: str
    summary: str
    status: str
    governance_status: str
    is_current_cycle: bool
    raw_event: Dict[str, Any]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_redis_client() -> redis.Redis:
    return redis.Redis.from_url(REDIS_URL, decode_responses=True)


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def append_jsonl(path: Path, record: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def load_processed_events() -> set[str]:
    return set(load_json(PROCESSED_EVENTS_PATH, []))


def save_processed_events(processed: set[str]) -> None:
    save_json(PROCESSED_EVENTS_PATH, sorted(processed))


def decode_stream_payload(fields: Dict[str, Any]) -> Dict[str, Any]:
    payload = fields.get("payload")

    if payload:
        try:
            return json.loads(payload)
        except Exception:
            return {"raw_payload": payload}

    return dict(fields)


def read_stream_events(stream_name: str, max_count: int = 500) -> List[Dict[str, Any]]:
    r = get_redis_client()
    entries = r.xrange(stream_name, count=max_count)

    events = []
    for stream_id, fields in entries:
        payload = decode_stream_payload(fields)
        events.append(
            {
                "stream_id": stream_id,
                "source_stream": stream_name,
                "fields": dict(fields),
                "payload": payload,
            }
        )

    return events


def infer_entity_id(source_stream: str, payload: Dict[str, Any], stream_id: str) -> str:
    for key in ["execution_id", "ticket_id", "order_id", "portfolio_id", "audit_id"]:
        if payload.get(key):
            return str(payload[key])

    if source_stream == "institutional_portfolio_state":
        return str(payload.get("portfolio_id", "AURUM_LIVE_PORTFOLIO"))

    return stream_id


def infer_summary(source_stream: str, payload: Dict[str, Any]) -> str:
    ticker = payload.get("ticker")
    action = payload.get("action")
    status = payload.get("status") or payload.get("lifecycle_status")

    if source_stream == "execution_orders":
        return f"Order generated: {action} {ticker} {payload.get('quantity_pct', 0)}"

    if source_stream == "trade_tickets":
        return f"Trade ticket submitted: {action} {ticker} {payload.get('quantity_pct', 0)}"

    if source_stream == "execution_reports":
        return (
            f"Execution report: {action} {ticker} "
            f"executed={payload.get('executed_pct', 0)} status={status}"
        )

    if source_stream == "live_positions":
        return f"Live positions updated: status={status}"

    if source_stream == "institutional_portfolio_state":
        opt_source = payload.get("optimization_state", {}).get("source", "unknown")
        return f"Institutional state updated: lifecycle={status}, optimizer={opt_source}"

    return f"{source_stream} event processed"


def infer_status(payload: Dict[str, Any]) -> str:
    return str(
        payload.get("status")
        or payload.get("lifecycle_status")
        or payload.get("governance_status")
        or "RECORDED"
    )


def infer_governance_status(source_stream: str, payload: Dict[str, Any]) -> str:
    if source_stream == "institutional_portfolio_state":
        governance = payload.get("governance_state", {})
        if isinstance(governance, dict):
            return governance.get("governance_status", "UNKNOWN")

    if infer_status(payload) in {"REJECTED", "CASH_BREACH", "EXPOSURE_BREACH"}:
        return "REVIEW_REQUIRED"

    return "APPROVED"


def is_current_cycle_event(payload: Dict[str, Any]) -> bool:
    """
    Current-cycle logic:
    - Newest live records without legacy Phase 3D optimization source are current.
    - Historical fallback/default target snapshots are treated as stale audit history.
    """
    opt_state = payload.get("optimization_state", {})

    if isinstance(opt_state, dict):
        source = str(opt_state.get("source", ""))
        raw = opt_state.get("raw", {})

        if "target_portfolio.json" in source:
            return False

        if isinstance(raw, dict) and raw.get("source") == "default_phase_3d_target":
            return False

    return True


def make_audit_record(
    source_stream: str,
    stream_id: str,
    payload: Dict[str, Any],
    sequence: int,
    cycle_id: str,
) -> AuditRecord:
    event_type = str(payload.get("event_type", source_stream))
    portfolio_id = str(payload.get("portfolio_id", "AURUM_LIVE_PORTFOLIO"))
    entity_id = infer_entity_id(source_stream, payload, stream_id)

    return AuditRecord(
        audit_id=f"AUD-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{sequence:06d}",
        cycle_id=cycle_id,
        timestamp=now_utc(),
        source_stream=source_stream,
        event_type=event_type,
        portfolio_id=portfolio_id,
        entity_id=entity_id,
        summary=infer_summary(source_stream, payload),
        status=infer_status(payload),
        governance_status=infer_governance_status(source_stream, payload),
        is_current_cycle=is_current_cycle_event(payload),
        raw_event=payload,
    )


def publish_audit_record(record: AuditRecord) -> None:
    r = get_redis_client()
    payload = asdict(record)

    r.xadd(
        AUDIT_STREAM,
        {
            "event_type": "audit_record",
            "payload": json.dumps(payload),
            "audit_id": record.audit_id,
            "cycle_id": record.cycle_id,
            "source_stream": record.source_stream,
            "portfolio_id": record.portfolio_id,
            "governance_status": record.governance_status,
            "is_current_cycle": str(record.is_current_cycle),
            "timestamp": record.timestamp,
        },
    )


def run_execution_audit_engine() -> List[Dict[str, Any]]:
    cycle = get_current_audit_cycle()
    cycle_id = cycle["cycle_id"]

    processed = load_processed_events()
    new_records: List[AuditRecord] = []

    for source_stream in SOURCE_STREAMS:
        try:
            events = read_stream_events(source_stream)
        except Exception:
            continue

        for event in events:
            event_key = f"{event['source_stream']}::{event['stream_id']}"

            if event_key in processed:
                continue

            record = make_audit_record(
                source_stream=event["source_stream"],
                stream_id=event["stream_id"],
                payload=event["payload"],
                sequence=len(processed) + len(new_records) + 1,
                cycle_id=cycle_id,
            )

            new_records.append(record)
            processed.add(event_key)

    for record in new_records:
        record_dict = asdict(record)
        append_jsonl(AUDIT_LOG_PATH, record_dict)

        if record.is_current_cycle:
            append_jsonl(CURRENT_CYCLE_AUDIT_LOG_PATH, record_dict)

        publish_audit_record(record)

    save_processed_events(processed)

    summary = {
        "timestamp": now_utc(),
        "cycle_id": cycle_id,
        "new_audit_records": len(new_records),
        "new_current_cycle_records": sum(1 for r in new_records if r.is_current_cycle),
        "total_processed_events": len(processed),
        "source_streams": SOURCE_STREAMS,
        "audit_log_path": str(AUDIT_LOG_PATH),
        "current_cycle_audit_log_path": str(CURRENT_CYCLE_AUDIT_LOG_PATH),
        "audit_stream": AUDIT_STREAM,
    }

    save_json(AUDIT_SUMMARY_PATH, summary)

    return [asdict(record) for record in new_records]


def main() -> None:
    print("=" * 80)
    print("AURUM EXECUTION AUDIT ENGINE - HARDENED")
    print("=" * 80)

    records = run_execution_audit_engine()

    if not records:
        print("No new audit records. Previously processed events skipped.")
    else:
        for record in records:
            print(
                f"{record['audit_id']} | {record['cycle_id']} | "
                f"{record['source_stream']} | current={record['is_current_cycle']} | "
                f"{record['entity_id']} | {record['governance_status']}"
            )

    print("-" * 80)
    print(f"New audit records: {len(records)}")
    print(f"Saved: {AUDIT_LOG_PATH}")
    print(f"Current cycle: {CURRENT_CYCLE_AUDIT_LOG_PATH}")
    print(f"Redis stream: {AUDIT_STREAM}")


if __name__ == "__main__":
    main()