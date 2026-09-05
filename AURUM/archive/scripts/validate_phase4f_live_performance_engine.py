# scripts/validate_phase4f_live_performance_engine.py

from pathlib import Path
import json

from src.monitoring.live_performance_engine import run_live_performance_engine


print("=" * 80)
print("AURUM PHASE 4F LIVE PERFORMANCE ENGINE VALIDATION")
print("=" * 80)

result = run_live_performance_engine()

snapshot = result["snapshot"]
summary = result["summary"]

required_snapshot_fields = [
    "nav_proxy",
    "daily_pnl_proxy",
    "mtd_pnl_proxy",
    "ytd_pnl_proxy",
    "cash_weight",
    "gross_exposure",
    "risk_level",
    "governance_status",
    "approval_status",
]

missing_snapshot = [field for field in required_snapshot_fields if field not in snapshot]

assert not missing_snapshot, f"missing snapshot fields: {missing_snapshot}"

snapshot_path = Path("results/monitoring/live_performance_snapshot.json")
history_path = Path("results/monitoring/performance_history.jsonl")
summary_path = Path("results/monitoring/live_performance_summary.json")

assert snapshot_path.exists()
assert history_path.exists()
assert summary_path.exists()

saved_snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
saved_summary = json.loads(summary_path.read_text(encoding="utf-8"))

assert "nav_proxy" in saved_snapshot
assert saved_summary.get("history_points", 0) >= 1

print(f"[PASS] nav_proxy = {saved_snapshot['nav_proxy']}")
print(f"[PASS] daily_pnl_proxy = {saved_snapshot['daily_pnl_proxy']}")
print(f"[PASS] cash_weight = {saved_snapshot['cash_weight']}")
print(f"[PASS] gross_exposure = {saved_snapshot['gross_exposure']}")
print(f"[PASS] risk_level = {saved_snapshot['risk_level']}")
print(f"[PASS] governance_status = {saved_snapshot['governance_status']}")
print(f"[PASS] approval_status = {saved_snapshot['approval_status']}")
print(f"[PASS] history_points = {saved_summary['history_points']}")

print("=" * 80)
print("[PASS] PHASE 4F LIVE PERFORMANCE ENGINE VALIDATION COMPLETE")
print("=" * 80)