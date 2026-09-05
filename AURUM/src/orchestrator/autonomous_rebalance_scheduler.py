from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

TRIGGER_PATH = Path(
    "results/orchestrator/event_triggers.json"
)

OUTPUT_DIR = Path(
    "results/orchestrator"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

SCHEDULE_PATH = OUTPUT_DIR / "rebalance_schedule.json"


def now_utc():
    return datetime.now(
        timezone.utc
    ).isoformat()


def load_json(path, default):

    if not path.exists():
        return default

    try:
        return json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

    except Exception:
        return default


def save_json(path, data):

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            data,
            indent=2,
        ),
        encoding="utf-8",
    )


class AutonomousRebalanceScheduler:

    def __init__(self):

        self.trigger_report = load_json(
            TRIGGER_PATH,
            {},
        )

    def determine_schedule(self):

        triggers = self.trigger_report.get(
            "triggers",
            [],
        )

        trigger_types = {
            t["trigger_type"]
            for t in triggers
        }

        schedule_type = "NO_ACTION"

        execute_at = None

        approval_required = False

        reason = (
            "No triggers active."
        )

        if (
            "EMERGENCY_REBALANCE"
            in trigger_types
        ):

            schedule_type = (
                "EMERGENCY"
            )

            execute_at = now_utc()

            approval_required = True

            reason = (
                "Critical market stress detected."
            )

        elif (
            "DEFENSIVE_REBALANCE"
            in trigger_types
        ):

            schedule_type = (
                "INTRADAY"
            )

            execute_at = now_utc()

            approval_required = False

            reason = (
                "Defensive regime active."
            )

        elif (
            "EXECUTION_REVIEW"
            in trigger_types
        ):

            schedule_type = (
                "REVIEW"
            )

            execute_at = now_utc()

            approval_required = True

            reason = (
                "Execution quality review required."
            )

        return {
            "schedule_id":
                f"SCH-"
                f"{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "timestamp":
                now_utc(),
            "schedule_type":
                schedule_type,
            "execute_at":
                execute_at,
            "approval_required":
                approval_required,
            "reason":
                reason,
            "trigger_count":
                len(triggers),
            "trigger_types":
                list(trigger_types),
        }

    def run(self):

        schedule = (
            self.determine_schedule()
        )

        save_json(
            SCHEDULE_PATH,
            schedule,
        )

        return schedule


def run_autonomous_rebalance_scheduler():

    scheduler = (
        AutonomousRebalanceScheduler()
    )

    return scheduler.run()


def main():

    print("=" * 80)
    print(
        "AURUM AUTONOMOUS REBALANCE SCHEDULER"
    )
    print("=" * 80)

    schedule = (
        run_autonomous_rebalance_scheduler()
    )

    print(
        f"Schedule Type: "
        f"{schedule['schedule_type']}"
    )

    print(
        f"Approval Required: "
        f"{schedule['approval_required']}"
    )

    print(
        f"Reason: "
        f"{schedule['reason']}"
    )

    print("-" * 80)

    print(
        f"Saved: {SCHEDULE_PATH}"
    )


if __name__ == "__main__":
    main()