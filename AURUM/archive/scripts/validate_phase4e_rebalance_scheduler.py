from pathlib import Path
import json

from src.orchestrator.autonomous_rebalance_scheduler import (
    run_autonomous_rebalance_scheduler,
)

print("=" * 80)
print("AURUM PHASE 4E REBALANCE SCHEDULER VALIDATION")
print("=" * 80)

schedule = run_autonomous_rebalance_scheduler()

assert "schedule_type" in schedule
assert "approval_required" in schedule

schedule_path = Path(
    "results/orchestrator/rebalance_schedule.json"
)

assert schedule_path.exists()

saved = json.loads(
    schedule_path.read_text(
        encoding="utf-8"
    )
)

assert "schedule_type" in saved

print(
    f"[PASS] schedule_type = "
    f"{saved['schedule_type']}"
)

print(
    f"[PASS] approval_required = "
    f"{saved['approval_required']}"
)

print(
    f"[PASS] trigger_count = "
    f"{saved['trigger_count']}"
)

print("=" * 80)
print(
    "[PASS] PHASE 4E.3 AUTONOMOUS REBALANCE SCHEDULER"
)
print("=" * 80)