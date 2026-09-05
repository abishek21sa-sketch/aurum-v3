# src/portfolio/portfolio_audit_trail.py

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


AUDIT_DIR = Path("results/portfolio_audit")
AUDIT_LOG_PATH = AUDIT_DIR / "portfolio_audit_log.jsonl"


class PortfolioAuditTrail:
    def __init__(self, audit_dir: Path = AUDIT_DIR):
        self.audit_dir = audit_dir
        self.audit_log_path = audit_dir / "portfolio_audit_log.jsonl"
        self.audit_dir.mkdir(parents=True, exist_ok=True)

    def record_event(
        self,
        event_type: str,
        decision_stage: str,
        payload: Dict[str, Any],
        status: str = "RECORDED",
    ) -> Dict[str, Any]:
        event = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "decision_stage": decision_stage,
            "status": status,
            "payload": payload,
        }

        with self.audit_log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, default=str) + "\n")

        return event

    def latest_events(self, limit: int = 20):
        if not self.audit_log_path.exists():
            return []

        lines = self.audit_log_path.read_text(encoding="utf-8").splitlines()
        return [json.loads(line) for line in lines[-limit:]]


def main():
    audit = PortfolioAuditTrail()
    event = audit.record_event(
        event_type="SYSTEM_INITIALIZATION",
        decision_stage="PHASE_3H_START",
        payload={
            "message": "Portfolio operating system audit trail initialized.",
            "phase": "3H",
        },
    )

    print("=" * 80)
    print("AURUM PORTFOLIO AUDIT TRAIL")
    print("=" * 80)
    print(json.dumps(event, indent=2))


if __name__ == "__main__":
    main()