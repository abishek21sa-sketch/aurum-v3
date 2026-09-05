# src/realtime/event_bus.py

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import redis


DEFAULT_REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
DEFAULT_REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
DEFAULT_REDIS_DB = int(os.getenv("REDIS_DB", "0"))


class RedisEventBus:
    """
    Redis Streams event bus for AURUM.

    Everything in Phase 4A becomes an event:
    - market ticks
    - streaming features
    - risk signals
    - optimizer decisions
    - alerts
    """

    def __init__(
        self,
        host: str = DEFAULT_REDIS_HOST,
        port: int = DEFAULT_REDIS_PORT,
        db: int = DEFAULT_REDIS_DB,
        decode_responses: bool = True,
    ) -> None:
        self.client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=decode_responses,
        )
        self.client.ping()

    @staticmethod
    def utc_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _serialize_value(value: Any) -> str:
        if isinstance(value, (dict, list, tuple)):
            return json.dumps(value)
        if value is None:
            return ""
        return str(value)

    def publish(
        self,
        stream_name: str,
        event: Dict[str, Any],
        maxlen: int = 100_000,
    ) -> str:
        event = dict(event)
        event.setdefault("ingested_at", self.utc_now())

        payload = {
            key: self._serialize_value(value)
            for key, value in event.items()
        }

        return self.client.xadd(
            stream_name,
            payload,
            maxlen=maxlen,
            approximate=True,
        )

    def read_latest(
        self,
        stream_name: str,
        count: int = 10,
    ) -> List[Dict[str, Any]]:
        rows = self.client.xrevrange(stream_name, count=count)
        output: List[Dict[str, Any]] = []

        for event_id, fields in rows:
            item = {"redis_id": event_id}
            item.update(fields)
            output.append(item)

        return output

    def read_from(
        self,
        stream_name: str,
        last_id: str = "$",
        block_ms: int = 5000,
        count: int = 100,
    ) -> List[Dict[str, Any]]:
        result = self.client.xread(
            {stream_name: last_id},
            block=block_ms,
            count=count,
        )

        events: List[Dict[str, Any]] = []

        for _, rows in result:
            for event_id, fields in rows:
                item = {"redis_id": event_id}
                item.update(fields)
                events.append(item)

        return events

    def stream_length(self, stream_name: str) -> int:
        return int(self.client.xlen(stream_name))

    def health(self) -> Dict[str, Any]:
        return {
            "redis_ping": bool(self.client.ping()),
            "redis_host": DEFAULT_REDIS_HOST,
            "redis_port": DEFAULT_REDIS_PORT,
            "checked_at": self.utc_now(),
        }


EVENT_STREAMS = {
    "market_ticks": "market_ticks",
    "market_features": "market_features",
    "market_signals": "market_signals",
    "risk_events": "risk_events",
    "optimizer_events": "optimizer_events",
    "alerts": "alerts",
}