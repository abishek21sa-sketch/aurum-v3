# scripts/validate_phase4f_risk_history_engine.py

from pathlib import Path
import json

from src.monitoring.risk_history_engine import run_risk_history_engine


print("=" * 80)
print("AURUM PHASE 4F RISK HISTORY ENGINE VALIDATION")
print("=" * 80)

result = run_risk_history_engine()

snapshot = result["snapshot"]
summary = result["summary"]

required_snapshot_fields = [
    "market_regime",
    "stress_score",
    "risk_level",
    "var_95",
    "cvar_95",
    "drawdown",
    "governance_status",
    "approval_status",
    "nav_proxy",
]

missing = [field for field in required_snapshot_fields if field not in snapshot]
assert not missing, f"missing snapshot fields: {missing}"

snapshot_path = Path("results/monitoring/risk_snapshot.json")
history_path = Path("results/monitoring/risk_history.jsonl")
summary_path = Path("results/monitoring/risk_history_summary.json")

assert snapshot_path.exists()
assert history_path.exists()
assert summary_path.exists()

saved_snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
saved_summary = json.loads(summary_path.read_text(encoding="utf-8"))

assert "risk_level" in saved_snapshot
assert saved_summary.get("history_points", 0) >= 1

print(f"[PASS] regime = {saved_snapshot['market_regime']}")
print(f"[PASS] stress_score = {saved_snapshot['stress_score']}")
print(f"[PASS] risk_level = {saved_snapshot['risk_level']}")
print(f"[PASS] var_95 = {saved_snapshot['var_95']}")
print(f"[PASS] cvar_95 = {saved_snapshot['cvar_95']}")
print(f"[PASS] drawdown = {saved_snapshot['drawdown']}")
print(f"[PASS] critical_cycles = {saved_summary['critical_cycles']}")
print(f"[PASS] review_required_cycles = {saved_summary['review_required_cycles']}")
print(f"[PASS] history_points = {saved_summary['history_points']}")

print("=" * 80)
print("[PASS] PHASE 4F RISK HISTORY ENGINE VALIDATION COMPLETE")
print("=" * 80)