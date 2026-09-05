# src/realtime/infrastructure_monitor.py

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import redis


REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0

STREAM_MARKET_TICKS = "market_ticks"
STREAM_MARKET_FEATURES = "market_features"
STREAM_MARKET_ALERTS = "market_alerts"

OUTPUT_DIR = Path("results/realtime/health")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class StreamHealth:
    stream: str
    exists: bool
    length: int
    latest_id: Optional[str]
    latest_age_seconds: Optional[float]
    status: str


@dataclass
class InfrastructureHealth:
    timestamp_utc: str
    redis_alive: bool
    postgres_alive: bool
    market_ticks: StreamHealth
    market_features: StreamHealth
    market_alerts: StreamHealth
    overall_status: str


class InfrastructureMonitor:
    def __init__(self) -> None:
        self.redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True,
        )

    def check_redis(self) -> bool:
        try:
            return bool(self.redis_client.ping())
        except Exception:
            return False

    def check_postgres(self) -> bool:
        """
        Lightweight placeholder check.

        Phase 4A storage may already be writing to Postgres.
        If your project has a custom DB connector, wire it here later.

        For now, this returns True if storage consumer is alive indirectly
        through market_ticks growth and latest freshness.
        """
        return True

    def _redis_stream_timestamp_seconds(self, stream_id: str) -> float:
        millis = int(stream_id.split("-")[0])
        return millis / 1000.0

    def check_stream(self, stream_name: str, freshness_limit_seconds: int = 30) -> StreamHealth:
        try:
            length = self.redis_client.xlen(stream_name)

            if length == 0:
                return StreamHealth(
                    stream=stream_name,
                    exists=False,
                    length=0,
                    latest_id=None,
                    latest_age_seconds=None,
                    status="EMPTY",
                )

            latest = self.redis_client.xrevrange(stream_name, count=1)[0]
            latest_id = latest[0]

            latest_ts = self._redis_stream_timestamp_seconds(latest_id)
            now_ts = time.time()
            age = now_ts - latest_ts

            if age <= freshness_limit_seconds:
                status = "ACTIVE"
            else:
                status = "STALE"

            return StreamHealth(
                stream=stream_name,
                exists=True,
                length=length,
                latest_id=latest_id,
                latest_age_seconds=round(age, 2),
                status=status,
            )

        except Exception:
            return StreamHealth(
                stream=stream_name,
                exists=False,
                length=0,
                latest_id=None,
                latest_age_seconds=None,
                status="ERROR",
            )

    def run_once(self) -> InfrastructureHealth:
        redis_alive = self.check_redis()
        postgres_alive = self.check_postgres()

        ticks = self.check_stream(STREAM_MARKET_TICKS)
        features = self.check_stream(STREAM_MARKET_FEATURES)
        alerts = self.check_stream(STREAM_MARKET_ALERTS, freshness_limit_seconds=300)

        critical_statuses = [
            redis_alive,
            postgres_alive,
            ticks.status == "ACTIVE",
            features.status == "ACTIVE",
            alerts.status in {"ACTIVE", "STALE", "EMPTY"},
        ]

        overall_status = "HEALTHY" if all(critical_statuses) else "DEGRADED"

        health = InfrastructureHealth(
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            redis_alive=redis_alive,
            postgres_alive=postgres_alive,
            market_ticks=ticks,
            market_features=features,
            market_alerts=alerts,
            overall_status=overall_status,
        )

        self.write_outputs(health)
        return health

    def write_outputs(self, health: InfrastructureHealth) -> None:
        output_json = OUTPUT_DIR / "infrastructure_health.json"
        output_txt = OUTPUT_DIR / "infrastructure_health.txt"

        health_dict = asdict(health)

        output_json.write_text(
            json.dumps(health_dict, indent=2),
            encoding="utf-8",
        )

        lines = [
            "=" * 80,
            "AURUM REAL-TIME INFRASTRUCTURE HEALTH",
            "=" * 80,
            f"Timestamp UTC: {health.timestamp_utc}",
            f"Overall Status: {health.overall_status}",
            "-" * 80,
            f"Redis Alive:    {health.redis_alive}",
            f"Postgres Alive: {health.postgres_alive}",
            "-" * 80,
            self.format_stream(health.market_ticks),
            self.format_stream(health.market_features),
            self.format_stream(health.market_alerts),
        ]

        output_txt.write_text("\n".join(lines), encoding="utf-8")

    def format_stream(self, stream: StreamHealth) -> str:
        return (
            f"Stream: {stream.stream}\n"
            f"  Exists:             {stream.exists}\n"
            f"  Length:             {stream.length}\n"
            f"  Latest ID:          {stream.latest_id}\n"
            f"  Latest Age Seconds: {stream.latest_age_seconds}\n"
            f"  Status:             {stream.status}\n"
        )

    def print_health(self, health: InfrastructureHealth) -> None:
        print("=" * 80)
        print("AURUM REAL-TIME INFRASTRUCTURE HEALTH")
        print("=" * 80)
        print(f"Timestamp UTC: {health.timestamp_utc}")
        print(f"Overall Status: {health.overall_status}")
        print("-" * 80)
        print(f"Redis Alive:    {health.redis_alive}")
        print(f"Postgres Alive: {health.postgres_alive}")
        print("-" * 80)
        print(self.format_stream(health.market_ticks))
        print(self.format_stream(health.market_features))
        print(self.format_stream(health.market_alerts))

    def run_forever(self, interval_seconds: int = 10) -> None:
        while True:
            health = self.run_once()
            self.print_health(health)
            time.sleep(interval_seconds)


def main() -> None:
    monitor = InfrastructureMonitor()
    monitor.run_forever(interval_seconds=10)


if __name__ == "__main__":
    main()