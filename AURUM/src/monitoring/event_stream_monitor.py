# src/monitoring/event_stream_monitor.py

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import redis


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

OUTPUT_DIR = Path("results/monitoring")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SNAPSHOT_PATH = OUTPUT_DIR / "event_stream_snapshot.json"
HISTORY_PATH = OUTPUT_DIR / "event_stream_history.jsonl"
SUMMARY_PATH = OUTPUT_DIR / "event_stream_summary.json"

STREAMS = [
    "market_ticks",
    "market_features",
    "market_signals",
    "risk_events",
    "optimizer_events",
    "portfolio_decisions",
    "execution_orders",
    "trade_tickets",
    "execution_reports",
    "live_positions",
    "institutional_portfolio_state",
    "execution_audit",
    "governance_events",
    "rebalance_triggers",
    "alerts",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def append_jsonl(path: Path, record: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


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


def safe_json_load(value: Any) -> Any:
    if not isinstance(value, str):
        return value

    try:
        return json.loads(value)
    except Exception:
        return value


def get_redis_client() -> redis.Redis:
    return redis.Redis.from_url(
        REDIS_URL,
        decode_responses=True,
    )


class EventStreamMonitor:
    def __init__(self) -> None:
        self.redis_client = get_redis_client()

    def inspect_stream(self, stream_name: str) -> Dict[str, Any]:
        try:
            length = self.redis_client.xlen(stream_name)

            latest_id = None
            latest_event = {}

            if length > 0:
                latest = self.redis_client.xrevrange(
                    stream_name,
                    count=1,
                )

                if latest:
                    latest_id, latest_event = latest[0]

            normalized_event = {
                key: safe_json_load(value)
                for key, value in latest_event.items()
            }

            event_type = (
                normalized_event.get("event_type")
                or normalized_event.get("type")
                or "unknown"
            )

            return {
                "stream": stream_name,
                "status": "ACTIVE" if length > 0 else "EMPTY",
                "length": length,
                "latest_id": latest_id,
                "latest_event_type": event_type,
                "latest_event": normalized_event,
            }

        except Exception as exc:
            return {
                "stream": stream_name,
                "status": "ERROR",
                "length": 0,
                "latest_id": None,
                "latest_event_type": "error",
                "latest_event": {},
                "error": str(exc),
            }

    def build_snapshot(self) -> Dict[str, Any]:
        streams = [
            self.inspect_stream(stream_name)
            for stream_name in STREAMS
        ]

        active_count = sum(
            1 for stream in streams if stream["status"] == "ACTIVE"
        )

        empty_count = sum(
            1 for stream in streams if stream["status"] == "EMPTY"
        )

        error_count = sum(
            1 for stream in streams if stream["status"] == "ERROR"
        )

        total_events = sum(
            int(stream.get("length", 0))
            for stream in streams
        )

        return {
            "event_type": "event_stream_snapshot",
            "timestamp": now_utc(),
            "redis_url": REDIS_URL,
            "stream_count": len(streams),
            "active_streams": active_count,
            "empty_streams": empty_count,
            "error_streams": error_count,
            "total_events": total_events,
            "streams": streams,
        }

    def build_summary(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        history = load_jsonl(HISTORY_PATH)

        active_ratio = (
            snapshot["active_streams"] / snapshot["stream_count"]
            if snapshot["stream_count"]
            else 0.0
        )

        critical_streams = [
            "market_signals",
            "risk_events",
            "portfolio_decisions",
            "execution_reports",
            "institutional_portfolio_state",
            "governance_events",
            "rebalance_triggers",
        ]

        stream_map = {
            stream["stream"]: stream
            for stream in snapshot["streams"]
        }

        inactive_critical = [
            stream
            for stream in critical_streams
            if stream_map.get(stream, {}).get("status") != "ACTIVE"
        ]

        health_status = (
            "HEALTHY"
            if not inactive_critical and snapshot["error_streams"] == 0
            else "DEGRADED"
        )

        return {
            "event_type": "event_stream_summary",
            "timestamp": now_utc(),
            "history_points": len(history),
            "stream_count": snapshot["stream_count"],
            "active_streams": snapshot["active_streams"],
            "empty_streams": snapshot["empty_streams"],
            "error_streams": snapshot["error_streams"],
            "total_events": snapshot["total_events"],
            "active_ratio": round(active_ratio, 4),
            "inactive_critical_streams": inactive_critical,
            "health_status": health_status,
        }

    def run(self) -> Dict[str, Any]:
        snapshot = self.build_snapshot()

        save_json(SNAPSHOT_PATH, snapshot)
        append_jsonl(HISTORY_PATH, snapshot)

        summary = self.build_summary(snapshot)
        save_json(SUMMARY_PATH, summary)

        return {
            "snapshot": snapshot,
            "summary": summary,
        }


def run_event_stream_monitor() -> Dict[str, Any]:
    return EventStreamMonitor().run()


def main() -> None:
    print("=" * 80)
    print("AURUM EVENT STREAM MONITOR")
    print("=" * 80)

    result = run_event_stream_monitor()

    snapshot = result["snapshot"]
    summary = result["summary"]

    print(f"Redis URL:        {snapshot['redis_url']}")
    print(f"Stream Count:     {snapshot['stream_count']}")
    print(f"Active Streams:   {snapshot['active_streams']}")
    print(f"Empty Streams:    {snapshot['empty_streams']}")
    print(f"Error Streams:    {snapshot['error_streams']}")
    print(f"Total Events:     {snapshot['total_events']}")
    print(f"Health:           {summary['health_status']}")

    print("-" * 80)

    for stream in snapshot["streams"]:
        print(
            f"{stream['status']:8} | "
            f"{stream['stream']:32} | "
            f"length={stream['length']} | "
            f"type={stream['latest_event_type']}"
        )

    print("-" * 80)
    print(f"Saved Snapshot: {SNAPSHOT_PATH}")
    print(f"Saved History:  {HISTORY_PATH}")
    print(f"Saved Summary:  {SUMMARY_PATH}")


if __name__ == "__main__":
    main()