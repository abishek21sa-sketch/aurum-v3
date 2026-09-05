# src/governance/audit_cycle_manager.py

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


OUTPUT_DIR = Path("results/governance")
STATE_DIR = Path("results/governance/state")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
STATE_DIR.mkdir(parents=True, exist_ok=True)

CURRENT_CYCLE_PATH = STATE_DIR / "current_audit_cycle.json"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_cycle_id() -> str:
    return f"REBALANCE_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def create_new_audit_cycle(reason: str = "Phase 4D audit cycle") -> Dict[str, Any]:
    cycle = {
        "cycle_id": make_cycle_id(),
        "created_at": now_utc(),
        "status": "ACTIVE",
        "reason": reason,
        "portfolio_id": "AURUM_LIVE_PORTFOLIO",
    }

    save_json(CURRENT_CYCLE_PATH, cycle)
    return cycle


def get_current_audit_cycle() -> Dict[str, Any]:
    cycle = load_json(CURRENT_CYCLE_PATH, {})

    if not cycle:
        cycle = create_new_audit_cycle()

    return cycle


def main() -> None:
    print("=" * 80)
    print("AURUM AUDIT CYCLE MANAGER")
    print("=" * 80)

    cycle = create_new_audit_cycle("Manual audit cycle reset")

    print(f"Cycle ID: {cycle['cycle_id']}")
    print(f"Created At: {cycle['created_at']}")
    print(f"Status: {cycle['status']}")
    print(f"Saved: {CURRENT_CYCLE_PATH}")


if __name__ == "__main__":
    main()