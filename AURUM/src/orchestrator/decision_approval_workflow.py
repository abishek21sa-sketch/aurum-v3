from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


SCHEDULE_PATH = Path(
    "results/orchestrator/rebalance_schedule.json"
)

GOVERNANCE_REPORT_PATH = Path(
    "results/governance/execution_governance_report.json"
)

OUTPUT_DIR = Path(
    "results/orchestrator"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

APPROVAL_PATH = OUTPUT_DIR / "decision_approval.json"


def now_utc() -> str:
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


def save_json(path: Path, data: Any):

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


class DecisionApprovalWorkflow:

    def __init__(self):

        self.schedule = load_json(
            SCHEDULE_PATH,
            {},
        )

        self.governance = load_json(
            GOVERNANCE_REPORT_PATH,
            {},
        )

    def evaluate(self):

        governance_status = str(
            self.governance.get(
                "governance_status",
                "UNKNOWN",
            )
        )

        governance_score = float(
            self.governance.get(
                "governance_score",
                0,
            )
        )

        approval_required = bool(
            self.schedule.get(
                "approval_required",
                False,
            )
        )

        schedule_type = self.schedule.get(
            "schedule_type",
            "UNKNOWN",
        )

        status = "APPROVED"

        reason = (
            "Governance controls satisfied."
        )

        if governance_score < 30:

            status = "REJECTED"

            reason = (
                "Governance score below minimum threshold."
            )

        elif (
            approval_required
            or governance_status
            == "REVIEW_REQUIRED"
        ):

            status = "ESCALATED"

            reason = (
                "Manual governance review required."
            )

        elif (
            governance_status == "CLEAR"
            and governance_score >= 80
        ):

            status = "APPROVED"

            reason = (
                "Governance controls approved."
            )

        return {
            "decision_id":
                f"APR-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "timestamp":
                now_utc(),
            "status":
                status,
            "schedule_type":
                schedule_type,
            "approval_required":
                approval_required,
            "governance_status":
                governance_status,
            "governance_score":
                governance_score,
            "reason":
                reason,
        }

    def run(self):

        decision = self.evaluate()

        save_json(
            APPROVAL_PATH,
            decision,
        )

        return decision


def run_decision_approval_workflow():

    workflow = (
        DecisionApprovalWorkflow()
    )

    return workflow.run()


def main():

    print("=" * 80)
    print(
        "AURUM DECISION APPROVAL WORKFLOW"
    )
    print("=" * 80)

    decision = (
        run_decision_approval_workflow()
    )

    print(
        f"Status: "
        f"{decision['status']}"
    )

    print(
        f"Schedule: "
        f"{decision['schedule_type']}"
    )

    print(
        f"Governance: "
        f"{decision['governance_status']}"
    )

    print(
        f"Score: "
        f"{decision['governance_score']}"
    )

    print("-" * 80)

    print(
        f"Reason: "
        f"{decision['reason']}"
    )

    print("-" * 80)

    print(
        f"Saved: {APPROVAL_PATH}"
    )


if __name__ == "__main__":
    main()