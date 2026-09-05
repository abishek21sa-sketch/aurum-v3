# scripts/validate_phase4b_runtime_control.py

from __future__ import annotations

import importlib
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import redis


REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0

STREAM_TICKS = "market_ticks"
STREAM_FEATURES = "market_features"
STREAM_ALERTS = "market_alerts"

HEALTH_PATH = Path("results/realtime/health/infrastructure_health.json")
DASHBOARD_PATH = Path("dashboard/realtime_dashboard.py")
ORCHESTRATOR_PATH = Path("src/realtime/realtime_orchestrator.py")
MONITOR_PATH = Path("src/realtime/infrastructure_monitor.py")
RUN_SCRIPT_PATH = Path("scripts/run_realtime_stack.py")


class Phase4BRuntimeValidator:
    def __init__(self) -> None:
        self.results: List[Tuple[str, bool, str]] = []
        self.redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True,
        )

    def record(self, name: str, passed: bool, detail: str = "") -> None:
        self.results.append((name, passed, detail))

        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {name}")

        if detail:
            print(f"       {detail}")

    def validate_imports(self) -> None:
        print("\nMODULE IMPORT CHECKS")
        print("-" * 80)

        modules = [
            "src.realtime.realtime_orchestrator",
            "src.realtime.infrastructure_monitor",
        ]

        for module in modules:
            try:
                importlib.import_module(module)
                self.record(module, True)
            except Exception as exc:
                self.record(module, False, str(exc))

    def validate_files(self) -> None:
        print("\nFILE EXISTENCE CHECKS")
        print("-" * 80)

        files = [
            ORCHESTRATOR_PATH,
            MONITOR_PATH,
            DASHBOARD_PATH,
            RUN_SCRIPT_PATH,
        ]

        for path in files:
            self.record(
                str(path),
                path.exists(),
                f"path={path}",
            )

    def validate_redis(self) -> None:
        print("\nREDIS CHECKS")
        print("-" * 80)

        try:
            alive = bool(self.redis_client.ping())
            self.record("Redis reachable", alive)
        except Exception as exc:
            self.record("Redis reachable", False, str(exc))

    def get_latest_stream_age(self, stream: str) -> float | None:
        rows = self.redis_client.xrevrange(stream, count=1)

        if not rows:
            return None

        latest_id = rows[0][0]
        millis = int(latest_id.split("-")[0])
        latest_ts = millis / 1000.0

        return time.time() - latest_ts

    def validate_stream(self, stream: str, freshness_seconds: int) -> None:
        try:
            length = self.redis_client.xlen(stream)

            self.record(
                f"{stream} exists",
                length > 0,
                f"length={length}",
            )

            age = self.get_latest_stream_age(stream)

            if age is None:
                self.record(
                    f"{stream} latest freshness",
                    False,
                    "no latest entry",
                )
                return

            self.record(
                f"{stream} latest freshness",
                age <= freshness_seconds,
                f"age_seconds={round(age, 2)} limit={freshness_seconds}",
            )

        except Exception as exc:
            self.record(f"{stream} validation", False, str(exc))

    def validate_streams(self) -> None:
        print("\nSTREAM ACTIVITY CHECKS")
        print("-" * 80)

        self.validate_stream(STREAM_TICKS, freshness_seconds=30)
        self.validate_stream(STREAM_FEATURES, freshness_seconds=30)
        self.validate_stream(STREAM_ALERTS, freshness_seconds=300)

    def validate_health_file(self) -> None:
        print("\nHEALTH OUTPUT CHECKS")
        print("-" * 80)

        if not HEALTH_PATH.exists():
            self.record(
                "Infrastructure health output exists",
                False,
                f"missing={HEALTH_PATH}",
            )
            return

        self.record(
            "Infrastructure health output exists",
            True,
            f"path={HEALTH_PATH}",
        )

        try:
            health: Dict[str, Any] = json.loads(
                HEALTH_PATH.read_text(encoding="utf-8")
            )

            overall_status = health.get("overall_status")

            self.record(
                "Infrastructure health status",
                overall_status == "HEALTHY",
                f"overall_status={overall_status}",
            )

            self.record(
                "Health confirms Redis alive",
                health.get("redis_alive") is True,
                f"redis_alive={health.get('redis_alive')}",
            )

        except Exception as exc:
            self.record("Infrastructure health JSON readable", False, str(exc))

    def summarize(self) -> None:
        print("\n" + "=" * 80)
        print("PHASE 4B RUNTIME CONTROL VALIDATION SUMMARY")
        print("=" * 80)

        passed = sum(1 for _, ok, _ in self.results if ok)
        total = len(self.results)
        failed = total - passed

        print(f"Passed: {passed}/{total}")
        print(f"Failed: {failed}/{total}")

        if failed == 0:
            print("\nPHASE 4B COMPLETE")
            print("AURUM Real-Time Runtime Control Tower is operational.")
        else:
            print("\nPHASE 4B NOT COMPLETE")
            print("Fix failed checks above and rerun validation.")

    def run(self) -> None:
        print("=" * 80)
        print("AURUM PHASE 4B REAL-TIME RUNTIME CONTROL VALIDATION")
        print("=" * 80)

        self.validate_imports()
        self.validate_files()
        self.validate_redis()
        self.validate_streams()
        self.validate_health_file()
        self.summarize()


def main() -> None:
    validator = Phase4BRuntimeValidator()
    validator.run()


if __name__ == "__main__":
    main()