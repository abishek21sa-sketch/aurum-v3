from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PORTFOLIO_STATE_PATH = Path(
    "results/portfolio/institutional_portfolio_state.json"
)

APPROVAL_PATH = Path(
    "results/orchestrator/decision_approval.json"
)

SCHEDULE_PATH = Path(
    "results/orchestrator/rebalance_schedule.json"
)

MEMORY_SUMMARY_PATH = Path(
    "results/memory/memory_summary.json"
)

OUTPUT_DIR = Path("results/ai")
OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

BRIEF_JSON_PATH = OUTPUT_DIR / "cio_daily_brief.json"
BRIEF_TXT_PATH = OUTPUT_DIR / "cio_daily_brief.txt"


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


def save_json(path: Path, data):

    path.write_text(
        json.dumps(
            data,
            indent=2,
        ),
        encoding="utf-8",
    )


class AICIOCopilot:

    def __init__(self):

        self.portfolio_state = load_json(
            PORTFOLIO_STATE_PATH,
            {},
        )

        self.approval = load_json(
            APPROVAL_PATH,
            {},
        )

        self.schedule = load_json(
            SCHEDULE_PATH,
            {},
        )

        self.memory = load_json(
            MEMORY_SUMMARY_PATH,
            {},
        )

    def build_brief(self):

        market_state = self.portfolio_state.get(
            "market_state",
            {}
        )

        risk_state = self.portfolio_state.get(
            "risk_state",
            {}
        )

        governance_state = self.portfolio_state.get(
            "governance_state",
            {}
        )

        market_state = self.portfolio_state.get(
            "market_state",
            {}
        )

        market_regime = (
            market_state.get(
                "market_regime"
            )
            or market_state.get(
                "regime"
            )
            or "unknown"
        )

        stress_score = (
            market_state.get(
                "market_stress"
            )
            or market_state.get(
                "stress_score"
            )
            or 0.0
        )

        risk_level = risk_state.get(
            "risk_level",
            "unknown",
        )

        governance_status = governance_state.get(
            "status",
            self.approval.get(
                "governance_status",
                "unknown",
            ),
        )

        schedule_type = self.schedule.get(
            "schedule_type",
            "UNKNOWN",
        )

        approval_status = self.approval.get(
            "status",
            "UNKNOWN",
        )

        total_cycles = self.memory.get(
            "total_cycles",
            0,
        )

        market_view = (
            f"Market regime remains "
            f"{market_regime} with "
            f"stress score {stress_score}."
        )

        risk_view = (
            f"Risk conditions are "
            f"{risk_level}."
        )

        portfolio_view = (
            f"Current portfolio state "
            f"remains ACTIVE. "
            f"Scheduler selected "
            f"{schedule_type} execution."
        )

        governance_view = (
            f"Governance status is "
            f"{governance_status}. "
            f"Approval workflow result: "
            f"{approval_status}."
        )

        if approval_status == "ESCALATED":

            recommended_action = (
                "Escalate to investment "
                "committee review before "
                "execution."
            )

        elif approval_status == "REJECTED":

            recommended_action = (
                "Do not execute portfolio "
                "changes until governance "
                "issues are resolved."
            )

        else:

            recommended_action = (
                "Execution approved."
            )

        return {
            "timestamp": now_utc(),
            "market_view": market_view,
            "risk_view": risk_view,
            "portfolio_view": portfolio_view,
            "governance_view": governance_view,
            "recommended_action": recommended_action,
            "historical_cycles": total_cycles,
        }

    def build_text_report(
        self,
        brief,
    ):

        lines = [
            "AURUM CIO DAILY BRIEF",
            "=" * 60,
            "",
            brief["market_view"],
            "",
            brief["risk_view"],
            "",
            brief["portfolio_view"],
            "",
            brief["governance_view"],
            "",
            f"Recommended Action: "
            f"{brief['recommended_action']}",
            "",
            f"Historical Cycles: "
            f"{brief['historical_cycles']}",
        ]

        return "\n".join(lines)

    def run(self):

        brief = self.build_brief()

        save_json(
            BRIEF_JSON_PATH,
            brief,
        )

        BRIEF_TXT_PATH.write_text(
            self.build_text_report(
                brief
            ),
            encoding="utf-8",
        )

        return brief


def run_ai_cio_copilot():

    return AICIOCopilot().run()


def main():

    print("=" * 80)
    print("AURUM AI CIO COPILOT")
    print("=" * 80)

    brief = run_ai_cio_copilot()

    print(
        brief["market_view"]
    )

    print(
        brief["risk_view"]
    )

    print(
        brief["governance_view"]
    )

    print("-" * 80)

    print(
        f"Action: "
        f"{brief['recommended_action']}"
    )

    print("-" * 80)

    print(
        f"Saved: {BRIEF_JSON_PATH}"
    )

    print(
        f"Saved: {BRIEF_TXT_PATH}"
    )


if __name__ == "__main__":
    main()