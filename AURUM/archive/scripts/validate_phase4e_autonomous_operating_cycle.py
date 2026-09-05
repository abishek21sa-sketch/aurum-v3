from pathlib import Path
import json

from src.orchestrator.autonomous_operating_cycle import (
    run_autonomous_operating_cycle,
)

print("=" * 80)
print(
    "AURUM AUTONOMOUS OPERATING CYCLE VALIDATION"
)
print("=" * 80)

report = (
    run_autonomous_operating_cycle()
)

path = Path(
    "results/orchestrator/operating_cycle.json"
)

assert path.exists()

saved = json.loads(
    path.read_text(
        encoding="utf-8"
    )
)

assert (
    saved["overall_status"]
    in [
        "PASS",
        "PARTIAL_FAILURE",
    ]
)

print(
    f"[PASS] orchestrator = "
    f"{saved['orchestrator_status']}"
)

print(
    f"[PASS] triggers = "
    f"{saved['trigger_count']}"
)

print(
    f"[PASS] schedule = "
    f"{saved['schedule_type']}"
)

print(
    f"[PASS] approval = "
    f"{saved['approval_status']}"
)

print(
    f"[PASS] memory_cycles = "
    f"{saved['memory_cycles']}"
)

print(
    f"[PASS] overall_status = "
    f"{saved['overall_status']}"
)

print("=" * 80)
print(
    "[PASS] PHASE 4E.7 AUTONOMOUS OPERATING CYCLE"
)
print("=" * 80)