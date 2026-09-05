from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


PORTFOLIO_STATE_PATH = Path(
    "results/portfolio/institutional_portfolio_state.json"
)

TRIGGER_PATH = Path(
    "results/orchestrator/event_triggers.json"
)

SCHEDULE_PATH = Path(
    "results/orchestrator/rebalance_schedule.json"
)

APPROVAL_PATH = Path(
    "results/orchestrator/decision_approval.json"
)

MEMORY_DIR = Path("results/memory")
MEMORY_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

MEMORY_LOG_PATH = MEMORY_DIR / "portfolio_memory.jsonl"

MEMORY_SUMMARY_PATH = (
    MEMORY_DIR / "memory_summary.json"
)


def now_utc():

    return datetime.now(
        timezone.utc
    ).isoformat()


def load_json(path: Path, default: Any):

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


def append_jsonl(
    path: Path,
    record: Dict[str, Any],
):

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        path,
        "a",
        encoding="utf-8",
    ) as f:

        f.write(
            json.dumps(record)
            + "\n"
        )


def save_json(
    path: Path,
    data: Dict[str, Any],
):

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


def count_jsonl_records(
    path: Path,
):

    if not path.exists():
        return 0

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as f:

        return sum(
            1
            for line in f
            if line.strip()
        )


class PortfolioMemoryEngine:

    def __init__(self):

        self.portfolio_state = load_json(
            PORTFOLIO_STATE_PATH,
            {},
        )

        self.trigger_report = load_json(
            TRIGGER_PATH,
            {},
        )

        self.schedule = load_json(
            SCHEDULE_PATH,
            {},
        )

        self.approval = load_json(
            APPROVAL_PATH,
            {},
        )

    def build_memory_record(self):

        governance_state = (
            self.portfolio_state.get(
                "governance_state",
                {}
            )
        )

        market_state = (
            self.portfolio_state.get(
                "market_state",
                {}
            )
        )

        risk_state = (
            self.portfolio_state.get(
                "risk_state",
                {}
            )
        )

        return {

            "memory_id":
                f"MEM-"
                f"{datetime.now().strftime('%Y%m%d%H%M%S')}",

            "timestamp":
                now_utc(),

            "regime":
                market_state.get(
                    "market_regime",
                    "unknown",
                ),

            "stress_score":
                market_state.get(
                    "market_stress",
                    0.0,
                ),

            "risk_level":
                risk_state.get(
                    "risk_level",
                    "unknown",
                ),

            "schedule_type":
                self.schedule.get(
                    "schedule_type",
                    "UNKNOWN",
                ),

            "approval_status":
                self.approval.get(
                    "status",
                    "UNKNOWN",
                ),

            "governance_status":
                governance_state.get(
                    "status",
                    "UNKNOWN",
                ),

            "portfolio_status":
                self.portfolio_state.get(
                    "status",
                    "UNKNOWN",
                ),

            "trigger_count":
                self.trigger_report.get(
                    "trigger_count",
                    0,
                ),
        }

    def update_summary(self):

        total_cycles = (
            count_jsonl_records(
                MEMORY_LOG_PATH
            )
        )

        approved = 0
        escalated = 0
        rejected = 0

        if MEMORY_LOG_PATH.exists():

            with open(
                MEMORY_LOG_PATH,
                "r",
                encoding="utf-8",
            ) as f:

                for line in f:

                    if not line.strip():
                        continue

                    record = json.loads(
                        line
                    )

                    status = (
                        record.get(
                            "approval_status",
                            "",
                        )
                    )

                    if status == "APPROVED":
                        approved += 1

                    elif status == "ESCALATED":
                        escalated += 1

                    elif status == "REJECTED":
                        rejected += 1

        summary = {
            "timestamp":
                now_utc(),
            "total_cycles":
                total_cycles,
            "approved":
                approved,
            "escalated":
                escalated,
            "rejected":
                rejected,
        }

        save_json(
            MEMORY_SUMMARY_PATH,
            summary,
        )

        return summary

    def run(self):

        memory_record = (
            self.build_memory_record()
        )

        append_jsonl(
            MEMORY_LOG_PATH,
            memory_record,
        )

        summary = (
            self.update_summary()
        )

        return {
            "memory_record":
                memory_record,
            "summary":
                summary,
        }


def run_portfolio_memory_engine():

    engine = (
        PortfolioMemoryEngine()
    )

    return engine.run()


def main():

    print("=" * 80)
    print(
        "AURUM PORTFOLIO MEMORY ENGINE"
    )
    print("=" * 80)

    result = (
        run_portfolio_memory_engine()
    )

    record = (
        result["memory_record"]
    )

    summary = (
        result["summary"]
    )

    print(
        f"Memory ID: "
        f"{record['memory_id']}"
    )

    print(
        f"Approval: "
        f"{record['approval_status']}"
    )

    print(
        f"Regime: "
        f"{record['regime']}"
    )

    print(
        f"Risk: "
        f"{record['risk_level']}"
    )

    print("-" * 80)

    print(
        f"Total Cycles: "
        f"{summary['total_cycles']}"
    )

    print(
        f"Approved: "
        f"{summary['approved']}"
    )

    print(
        f"Escalated: "
        f"{summary['escalated']}"
    )

    print(
        f"Rejected: "
        f"{summary['rejected']}"
    )

    print("-" * 80)

    print(
        f"Saved: "
        f"{MEMORY_LOG_PATH}"
    )

    print(
        f"Saved: "
        f"{MEMORY_SUMMARY_PATH}"
    )


if __name__ == "__main__":
    main()