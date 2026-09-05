# src/governance/execution_governance_escalation.py

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import redis


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

GOVERNANCE_ALERTS_STREAM = "governance_alerts"

OUTPUT_DIR = Path("results/governance")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

GOVERNANCE_REPORT_PATH = OUTPUT_DIR / "execution_governance_report.json"
ALERTS_PATH = OUTPUT_DIR / "governance_alerts.json"


@dataclass
class GovernanceAlert:
    alert_id: str
    timestamp: str
    portfolio_id: str
    rule: str
    severity: str
    message: str
    observed: Any
    limit: Any
    status: str = "OPEN"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_redis_client() -> redis.Redis:
    return redis.Redis.from_url(REDIS_URL, decode_responses=True)


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def publish_alert(alert: GovernanceAlert) -> None:
    r = get_redis_client()
    payload = asdict(alert)

    r.xadd(
        GOVERNANCE_ALERTS_STREAM,
        {
            "event_type": "governance_alert",
            "payload": json.dumps(payload),
            "alert_id": alert.alert_id,
            "portfolio_id": alert.portfolio_id,
            "severity": alert.severity,
            "rule": alert.rule,
            "timestamp": alert.timestamp,
        },
    )


def run_execution_governance_escalation() -> List[Dict[str, Any]]:
    report = load_json(GOVERNANCE_REPORT_PATH, {})

    portfolio_id = report.get("portfolio_id", "AURUM_LIVE_PORTFOLIO")
    violations = report.get("violations", [])

    alerts: List[GovernanceAlert] = []

    for i, violation in enumerate(violations, start=1):
        if violation.get("severity") not in {"MEDIUM", "HIGH", "CRITICAL"}:
            continue

        alert = GovernanceAlert(
            alert_id=f"ALT-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{i:03d}",
            timestamp=now_utc(),
            portfolio_id=portfolio_id,
            rule=violation.get("rule", "unknown"),
            severity=violation.get("severity", "UNKNOWN"),
            message=violation.get("message", "Governance violation detected."),
            observed=violation.get("observed"),
            limit=violation.get("limit"),
        )

        alerts.append(alert)

    alert_dicts = [asdict(alert) for alert in alerts]
    save_json(ALERTS_PATH, alert_dicts)

    for alert in alerts:
        publish_alert(alert)

    return alert_dicts


def main() -> None:
    print("=" * 80)
    print("AURUM EXECUTION GOVERNANCE ESCALATION ENGINE")
    print("=" * 80)

    alerts = run_execution_governance_escalation()

    if not alerts:
        print("No governance alerts generated.")
    else:
        for alert in alerts:
            print(
                f"{alert['alert_id']} | {alert['severity']} | "
                f"{alert['rule']} | {alert['status']}"
            )

    print("-" * 80)
    print(f"Alerts generated: {len(alerts)}")
    print(f"Saved: {ALERTS_PATH}")
    print(f"Redis stream: {GOVERNANCE_ALERTS_STREAM}")


if __name__ == "__main__":
    main()