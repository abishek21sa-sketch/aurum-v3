from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from src.orchestrator.portfolio_operating_orchestrator import (
    run_portfolio_operating_orchestrator,
)

from src.orchestrator.event_trigger_engine import (
    run_event_trigger_engine,
)

from src.orchestrator.autonomous_rebalance_scheduler import (
    run_autonomous_rebalance_scheduler,
)

from src.orchestrator.decision_approval_workflow import (
    run_decision_approval_workflow,
)

from src.memory.portfolio_memory_engine import (
    run_portfolio_memory_engine,
)

from src.ai.ai_cio_copilot import (
    run_ai_cio_copilot,
)


OUTPUT_DIR = Path("results/orchestrator")
OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

OPERATING_CYCLE_PATH = (
    OUTPUT_DIR / "operating_cycle.json"
)


def now_utc():

    return datetime.now(
        timezone.utc
    ).isoformat()


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


class AutonomousOperatingCycle:

    def run(self) -> Dict[str, Any]:

        orchestrator = (
            run_portfolio_operating_orchestrator()
        )

        triggers = (
            run_event_trigger_engine()
        )

        scheduler = (
            run_autonomous_rebalance_scheduler()
        )

        approval = (
            run_decision_approval_workflow()
        )

        memory = (
            run_portfolio_memory_engine()
        )

        cio = (
            run_ai_cio_copilot()
        )

        report = {

            "cycle_id":
                f"CYCLE-"
                f"{datetime.now().strftime('%Y%m%d%H%M%S')}",

            "timestamp":
                now_utc(),

            "phase":
                "4E.7",

            "orchestrator_status":
                orchestrator.get(
                    "status",
                    "UNKNOWN",
                ),

            "orchestrator_success_rate":
                orchestrator.get(
                    "success_rate",
                    0.0,
                ),

            "trigger_count":
                triggers.get(
                    "trigger_count",
                    0,
                ),

            "action_required":
                triggers.get(
                    "action_required",
                    False,
                ),

            "schedule_type":
                scheduler.get(
                    "schedule_type",
                    "UNKNOWN",
                ),

            "approval_status":
                approval.get(
                    "status",
                    "UNKNOWN",
                ),

            "approval_reason":
                approval.get(
                    "reason",
                    "",
                ),

            "memory_cycles":
                memory["summary"].get(
                    "total_cycles",
                    0,
                ),

            "cio_brief_generated":
                True,

            "overall_status":
                (
                    "PASS"
                    if orchestrator.get(
                        "status"
                    ) == "PASS"
                    else "PARTIAL_FAILURE"
                ),
        }

        save_json(
            OPERATING_CYCLE_PATH,
            report,
        )

        return report


def run_autonomous_operating_cycle():

    return (
        AutonomousOperatingCycle()
        .run()
    )


def main():

    print("=" * 80)
    print(
        "AURUM AUTONOMOUS OPERATING CYCLE"
    )
    print("=" * 80)

    report = (
        run_autonomous_operating_cycle()
    )

    print(
        f"Cycle ID: "
        f"{report['cycle_id']}"
    )

    print(
        f"Orchestrator: "
        f"{report['orchestrator_status']}"
    )

    print(
        f"Triggers: "
        f"{report['trigger_count']}"
    )

    print(
        f"Schedule: "
        f"{report['schedule_type']}"
    )

    print(
        f"Approval: "
        f"{report['approval_status']}"
    )

    print(
        f"Memory Cycles: "
        f"{report['memory_cycles']}"
    )

    print("-" * 80)

    print(
        f"Overall Status: "
        f"{report['overall_status']}"
    )

    print("-" * 80)

    print(
        f"Saved: "
        f"{OPERATING_CYCLE_PATH}"
    )


if __name__ == "__main__":
    main()