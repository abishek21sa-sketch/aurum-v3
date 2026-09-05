# scripts/run_realtime_stack.py

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path


class RealtimeStackLauncher:
    def __init__(self) -> None:
        self.processes = []

    def launch(self, name: str, command: list[str]) -> subprocess.Popen:
        print("=" * 80)
        print(f"STARTING: {name}")
        print("=" * 80)
        print(" ".join(command))

        process = subprocess.Popen(command)

        self.processes.append(
            {
                "name": name,
                "process": process,
            }
        )

        time.sleep(2)

        if process.poll() is not None:
            raise RuntimeError(f"{name} failed to start")

        print(f"[PASS] {name} | pid={process.pid}")
        return process

    def run(self) -> None:
        print("\n")
        print("=" * 80)
        print("AURUM REAL-TIME STACK LAUNCHER")
        print("=" * 80)

        self.launch(
            "Realtime Orchestrator",
            [
                sys.executable,
                "-m",
                "src.realtime.realtime_orchestrator",
            ],
        )

        self.launch(
            "Infrastructure Monitor",
            [
                sys.executable,
                "-m",
                "src.realtime.infrastructure_monitor",
            ],
        )

        print("\n")
        print("=" * 80)
        print("REAL-TIME STACK STARTED")
        print("=" * 80)

        print("Dashboard:")
        print(
            "streamlit run dashboard/realtime_dashboard.py "
            "--server.port 8502"
        )

        print("\nComponents:")
        print("  [RUNNING] Redis Streams")
        print("  [RUNNING] Tick Publisher")
        print("  [RUNNING] Storage Consumer")
        print("  [RUNNING] Streaming Feature Engine")
        print("  [RUNNING] Alert Engine")
        print("  [RUNNING] Infrastructure Monitor")

        print("\nPress CTRL+C to stop launcher.")

        try:
            while True:
                alive = True

                for item in self.processes:
                    process = item["process"]

                    if process.poll() is not None:
                        print(
                            f"[FAILED] {item['name']} "
                            f"exit_code={process.returncode}"
                        )
                        alive = False

                if not alive:
                    break

                time.sleep(5)

        except KeyboardInterrupt:
            print("\nStopping stack...")

            for item in self.processes:
                process = item["process"]

                if process.poll() is None:
                    process.terminate()

            print("Stack stopped.")


def main() -> None:
    launcher = RealtimeStackLauncher()
    launcher.run()


if __name__ == "__main__":
    main()