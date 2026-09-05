"""
AURUM Mission Control
Infrastructure Status Builder

Output:
    results/mission_control/infrastructure_status.json

Run:
    python -m src.mission_control.infrastructure_status_builder
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MISSION_DIR = ROOT / "results" / "mission_control"
INFRA_STATUS_PATH = MISSION_DIR / "infrastructure_status.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def check_redis() -> dict[str, Any]:
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    try:
        import redis

        client = redis.Redis.from_url(redis_url, socket_connect_timeout=2)
        pong = client.ping()

        stream_names = [
            "market_ticks",
            "market_features",
            "market_signals",
            "risk_events",
            "optimizer_events",
            "portfolio_decisions",
            "alerts",
            "execution_orders",
            "trade_tickets",
            "execution_reports",
            "live_positions",
        ]

        streams = {}
        active_count = 0

        for stream in stream_names:
            try:
                length = client.xlen(stream)
                streams[stream] = int(length)
                if length > 0:
                    active_count += 1
            except Exception:
                streams[stream] = None

        return {
            "status": "connected" if pong else "not_connected",
            "url": redis_url,
            "active_streams": active_count,
            "streams": streams,
        }

    except Exception as exc:
        return {
            "status": "not_available",
            "url": redis_url,
            "active_streams": 0,
            "streams": {},
            "error": str(exc),
        }


def check_timescale() -> dict[str, Any]:
    db_url = os.getenv("TIMESCALE_DATABASE_URL") or os.getenv("DATABASE_URL")

    if not db_url:
        return {
            "status": "not_configured",
            "url_configured": False,
        }

    try:
        import psycopg2

        conn = psycopg2.connect(db_url, connect_timeout=2)
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        result = cur.fetchone()
        cur.close()
        conn.close()

        return {
            "status": "connected" if result and result[0] == 1 else "not_connected",
            "url_configured": True,
        }

    except Exception as exc:
        return {
            "status": "not_available",
            "url_configured": True,
            "error": str(exc),
        }


def build_infrastructure_status() -> dict[str, Any]:
    redis_status = check_redis()
    timescale_status = check_timescale()

    health = "healthy"

    if redis_status.get("status") not in {"connected"}:
        health = "degraded"

    if timescale_status.get("status") not in {"connected", "not_configured"}:
        health = "degraded"

    payload = {
        "timestamp": utc_now(),
        "overall_infrastructure_status": health,
        "redis": redis_status,
        "timescale": timescale_status,
    }

    write_json(INFRA_STATUS_PATH, payload)
    return payload


def main() -> None:
    status = build_infrastructure_status()

    print("=" * 80)
    print("AURUM INFRASTRUCTURE STATUS")
    print("=" * 80)
    print(f"Saved: {INFRA_STATUS_PATH.relative_to(ROOT)}")
    print(f"Overall:   {status.get('overall_infrastructure_status')}")
    print(f"Redis:     {status.get('redis', {}).get('status')}")
    print(f"Streams:   {status.get('redis', {}).get('active_streams')}")
    print(f"Timescale: {status.get('timescale', {}).get('status')}")
    print("=" * 80)


if __name__ == "__main__":
    main()