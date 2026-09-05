"""
AURUM Autonomous Scheduler

Runs the full mission control cycle every 5 minutes continuously.
Designed to run in the background — start it once and leave it.

Run:
    python -m src.mission_control.autonomous_scheduler

Stop:
    Ctrl+C
"""

from pathlib import Path
from datetime import datetime, timezone
import json
import time
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
STATUS_FILE = ROOT / "results" / "mission_control" / "scheduler_status.json"
INTERVAL_SECONDS = 300


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_status(status: str, cycle_count: int, error: str = "") -> None:
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": status,
        "cycles_completed": cycle_count,
        "last_cycle": utc_now(),
        "next_run_seconds": INTERVAL_SECONDS,
        "interval_seconds": INTERVAL_SECONDS,
        "error": error,
    }
    STATUS_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def run_cycle(cycle_count: int) -> bool:
    print("=" * 70)
    print(f"AURUM AUTONOMOUS CYCLE #{cycle_count}")
    print(f"Time: {utc_now()}")
    print("=" * 70)

    write_status("running", cycle_count)

    result = subprocess.run(
        [sys.executable, "-m", "src.mission_control.run_aurum_mission_control", "--once"],
        cwd=str(ROOT),
    )

    if result.returncode == 0:
        print(f"Cycle {cycle_count} complete. Sleeping {INTERVAL_SECONDS}s...")
        write_status("sleeping", cycle_count)
        return True
    else:
        print(f"Cycle {cycle_count} failed with code {result.returncode}.")
        write_status("error", cycle_count, f"returncode={result.returncode}")
        return False


def main() -> None:
    print("AURUM Autonomous Scheduler starting...")
    print(f"Interval: {INTERVAL_SECONDS} seconds ({INTERVAL_SECONDS//60} minutes)")
    print("Press Ctrl+C to stop.")
    print()

    cycle_count = 0

    try:
        while True:
            cycle_count += 1
            run_cycle(cycle_count)
            time.sleep(INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("\nScheduler stopped.")
        write_status("stopped", cycle_count)


if __name__ == "__main__":
    main()
