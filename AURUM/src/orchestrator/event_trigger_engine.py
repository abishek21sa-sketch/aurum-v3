from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

TRIGGER_STREAM = "rebalance_triggers"

DIGITAL_TWIN_PATH = Path(
    "results/digital_twin/live_state/live_market_state.json"
)

PORTFOLIO_STATE_PATH = Path(
    "results/portfolio/institutional_portfolio_state.json"
)

GOVERNANCE_REPORT_PATH = Path(
    "results/governance/execution_governance_report.json"
)

OUTPUT_DIR = Path("results/orchestrator")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

EVENT_TRIGGER_PATH = OUTPUT_DIR / "event_triggers.json"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any):
    if not path.exists():
        return default

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, data: Any):
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )


def get_redis_client():
    return redis.Redis.from_url(
        REDIS_URL,
        decode_responses=True,
    )


class EventTriggerEngine:

    def __init__(self):

        self.digital_twin = load_json(
            DIGITAL_TWIN_PATH,
            {},
        )

        self.portfolio_state = load_json(
            PORTFOLIO_STATE_PATH,
            {},
        )

        self.governance_report = load_json(
            GOVERNANCE_REPORT_PATH,
            {},
        )

        self.triggers: List[Dict[str, Any]] = []

    def add_trigger(
        self,
        trigger_type: str,
        severity: str,
        action: str,
        reason: str,
    ):

        self.triggers.append(
            {
                "trigger_id":
                    f"TRG-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    f"-{len(self.triggers)+1:03d}",
                "timestamp": now_utc(),
                "trigger_type": trigger_type,
                "severity": severity,
                "action": action,
                "reason": reason,
            }
        )

    def check_market_stress(self):

        stress_score = float(
            self.digital_twin.get(
                "market_stress_score",
                0.0,
            )
        )

        if stress_score >= 0.75:

            self.add_trigger(
                "EMERGENCY_REBALANCE",
                "CRITICAL",
                "REBALANCE",
                f"Stress score {stress_score:.2f} exceeds threshold",
            )

    def check_regime(self):

        regime = str(
            self.digital_twin.get(
                "current_regime",
                "unknown",
            )
        ).lower()

        if regime == "defensive":

            self.add_trigger(
                "DEFENSIVE_REBALANCE",
                "HIGH",
                "REBALANCE",
                "Defensive market regime detected",
            )

    def check_cash_protection(self):

        position_state = self.portfolio_state.get(
            "position_state",
            {},
        )

        cash_weight = float(
            position_state.get(
                "cash_weight",
                0.0,
            )
        )

        if cash_weight < 0.05:

            self.add_trigger(
                "CASH_PROTECTION",
                "HIGH",
                "INCREASE_CASH",
                f"Cash weight {cash_weight:.2%} below minimum",
            )

    def check_governance(self):

        lifecycle_governance = self.portfolio_state.get(
            "governance_state",
            {},
        )

        governance_status = str(
            lifecycle_governance.get(
                "status",
                "UNKNOWN",
            )
        )

        if governance_status == "UNKNOWN":

            governance_status = str(
                self.governance_report.get(
                    "governance_status",
                    "UNKNOWN",
                )
            )

        if governance_status != "CLEAR":

            self.add_trigger(
                "GOVERNANCE_REVIEW",
                "HIGH",
                "ESCALATE",
                f"Governance status {governance_status}",
            )

    def check_execution_quality(self):

        execution_state = self.portfolio_state.get(
            "execution_state",
            {},
        )

        fill_ratio = float(
            execution_state.get(
                "aggregate_fill_ratio",
                1.0,
            )
        )

        if fill_ratio < 0.85:

            self.add_trigger(
                "EXECUTION_REVIEW",
                "MEDIUM",
                "REVIEW_EXECUTION",
                f"Fill ratio {fill_ratio:.2%} below threshold",
            )

    def run_rules(self):

        self.check_market_stress()
        self.check_regime()
        self.check_cash_protection()
        self.check_governance()
        self.check_execution_quality()

    def publish_to_redis(self):

        try:

            r = get_redis_client()

            for trigger in self.triggers:

                r.xadd(
                    TRIGGER_STREAM,
                    {
                        "event_type": "rebalance_trigger",
                        "payload": json.dumps(trigger),
                    },
                )

        except Exception:
            pass

    def run(self):

        self.run_rules()

        self.publish_to_redis()

        report = {
            "event_type": "event_trigger_engine",
            "timestamp": now_utc(),
            "trigger_count": len(self.triggers),
            "action_required": len(self.triggers) > 0,
            "triggers": self.triggers,
        }

        save_json(
            EVENT_TRIGGER_PATH,
            report,
        )

        return report


def run_event_trigger_engine():

    return EventTriggerEngine().run()


def main():

    print("=" * 80)
    print("AURUM EVENT TRIGGER ENGINE")
    print("=" * 80)

    report = run_event_trigger_engine()

    print(
        f"Triggers Generated: {report['trigger_count']}"
    )

    print(
        f"Action Required: {report['action_required']}"
    )

    print("-" * 80)

    for trigger in report["triggers"]:

        print(
            f"{trigger['severity']:8} | "
            f"{trigger['trigger_type']}"
        )

    print("-" * 80)

    print(f"Saved: {EVENT_TRIGGER_PATH}")
    print(f"Redis stream: {TRIGGER_STREAM}")


if __name__ == "__main__":
    main()