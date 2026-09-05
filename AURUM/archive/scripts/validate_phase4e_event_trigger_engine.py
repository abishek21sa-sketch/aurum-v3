from pathlib import Path
import json

from src.orchestrator.event_trigger_engine import (
    run_event_trigger_engine,
)

print("=" * 80)
print("AURUM EVENT TRIGGER VALIDATION")
print("=" * 80)

report = run_event_trigger_engine()

assert "trigger_count" in report
assert "triggers" in report

path = Path(
    "results/orchestrator/event_triggers.json"
)

assert path.exists()

loaded = json.loads(
    path.read_text(
        encoding="utf-8"
    )
)

assert "trigger_count" in loaded

print(
    f"[PASS] trigger count = "
    f"{loaded['trigger_count']}"
)

print(
    f"[PASS] action_required = "
    f"{loaded['action_required']}"
)

print("=" * 80)
print(
    "[PASS] PHASE 4E.2 EVENT TRIGGER ENGINE"
)
print("=" * 80)