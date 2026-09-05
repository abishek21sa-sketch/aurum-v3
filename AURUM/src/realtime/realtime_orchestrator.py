# src/realtime/realtime_orchestrator.py

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ManagedProcess:
    name: str
    command: List[str]
    process: Optional[subprocess.Popen] = None


class RealtimeOrchestrator:
    """
    Starts the full AURUM Phase 4A real-time stack:

    1. Market Data Gateway
    2. Streaming Feature Engine
    3. Real-Time Alert Engine
    4. TimescaleDB Writer
    """

    def __init__(
        self,
        provider: str = "demo",
        interval: float = 1.0,
        database_url: Optional[str] = None,
    ) -> None:
        self.provider = provider
        self.interval = interval
        self.database_url = database_url or os.getenv(
            "TIMESCALE_DATABASE_URL",
            "postgresql://aurum:aurum@127.0.0.1:5434/aurum",
        )

        self.processes: List[ManagedProcess] = [
            ManagedProcess(
                name="market_gateway",
                command=[
                    sys.executable,
                    "-m",
                    "scripts.run_realtime_market_gateway",
                    "--provider",
                    self.provider,
                    "--interval",
                    str(self.interval),
                ],
            ),
            ManagedProcess(
                name="streaming_feature_engine",
                command=[
                    sys.executable,
                    "-m",
                    "scripts.run_streaming_feature_engine",
                ],
            ),
            ManagedProcess(
                name="realtime_alert_engine",
                command=[
                    sys.executable,
                    "-m",
                    "scripts.run_realtime_alert_engine",
                ],
            ),
            ManagedProcess(
                name="timescale_writer",
                command=[
                    sys.executable,
                    "-m",
                    "scripts.run_timescale_writer",
                    "--database-url",
                    self.database_url,
                ],
            ),
        ]

    def start_all(self) -> None:
        print("=" * 80)
        print("AURUM PHASE 4A REAL-TIME ORCHESTRATOR")
        print("=" * 80)
        print(f"Provider: {self.provider}")
        print(f"Gateway interval: {self.interval}")
        print(f"Timescale URL: {self.database_url}")
        print("=" * 80)

        for managed in self.processes:
            print(f"[STARTING] {managed.name}")

            managed.process = subprocess.Popen(
                managed.command,
                stdout=None,
                stderr=None,
                env={
                    **os.environ,
                    "TIMESCALE_DATABASE_URL": self.database_url,
                },
            )

            time.sleep(1.5)

            if managed.process.poll() is not None:
                raise RuntimeError(
                    f"{managed.name} exited early with code {managed.process.returncode}"
                )

            print(f"[RUNNING] {managed.name} | pid={managed.process.pid}")

        print("=" * 80)
        print("FULL REAL-TIME STACK RUNNING")
        print("Press CTRL+C to stop.")
        print("=" * 80)

    def stop_all(self) -> None:
        print("\n" + "=" * 80)
        print("STOPPING AURUM REAL-TIME STACK")
        print("=" * 80)

        for managed in reversed(self.processes):
            if managed.process and managed.process.poll() is None:
                print(f"[STOPPING] {managed.name} | pid={managed.process.pid}")
                managed.process.terminate()

        time.sleep(2)

        for managed in reversed(self.processes):
            if managed.process and managed.process.poll() is None:
                print(f"[KILLING] {managed.name} | pid={managed.process.pid}")
                managed.process.kill()

        print("[STOPPED] All managed processes stopped.")

    def monitor(self) -> None:
        try:
            self.start_all()

            while True:
                for managed in self.processes:
                    if managed.process and managed.process.poll() is not None:
                        raise RuntimeError(
                            f"{managed.name} stopped unexpectedly "
                            f"with code {managed.process.returncode}"
                        )

                time.sleep(5)

        except KeyboardInterrupt:
            self.stop_all()

        except Exception as exc:
            print(f"[ERROR] {exc}")
            self.stop_all()
            raise


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the full AURUM Phase 4A real-time stack."
    )
    parser.add_argument("--provider", default="demo")
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument(
        "--database-url",
        default=os.getenv(
            "TIMESCALE_DATABASE_URL",
            "postgresql://aurum:aurum@127.0.0.1:5434/aurum",
        ),
    )

    args = parser.parse_args()

    orchestrator = RealtimeOrchestrator(
        provider=args.provider,
        interval=args.interval,
        database_url=args.database_url,
    )
    orchestrator.monitor()


if __name__ == "__main__":
    main()