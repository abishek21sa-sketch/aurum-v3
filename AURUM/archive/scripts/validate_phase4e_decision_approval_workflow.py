from pathlib import Path
import json

from src.orchestrator.decision_approval_workflow import (
    run_decision_approval_workflow,
)

print("=" * 80)
print(
    "AURUM DECISION APPROVAL WORKFLOW VALIDATION"
)
print("=" * 80)

decision = (
    run_decision_approval_workflow()
)

assert "status" in decision
assert "reason" in decision

path = Path(
    "results/orchestrator/decision_approval.json"
)

assert path.exists()

saved = json.loads(
    path.read_text(
        encoding="utf-8"
    )
)

assert "status" in saved

print(
    f"[PASS] status = "
    f"{saved['status']}"
)

print(
    f"[PASS] governance_score = "
    f"{saved['governance_score']}"
)

print(
    f"[PASS] governance_status = "
    f"{saved['governance_status']}"
)

print("=" * 80)
print(
    "[PASS] PHASE 4E.4 DECISION APPROVAL WORKFLOW"
)
print("=" * 80)