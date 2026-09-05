# scripts/validate_phase4f_event_stream_monitor.py

from pathlib import Path
import json

from src.monitoring.event_stream_monitor import run_event_stream_monitor


print("=" * 80)
print("AURUM PHASE 4F EVENT STREAM MONITOR VALIDATION")
print("=" * 80)

result = run_event_stream_monitor()

snapshot = result["snapshot"]
summary = result["summary"]

required_snapshot_fields = [
    "stream_count",
    "active_streams",
    "empty_streams",
    "error_streams",
    "total_events",
    "streams",
]

missing = [field for field in required_snapshot_fields if field not in snapshot]
assert not missing, f"missing snapshot fields: {missing}"

snapshot_path = Path("results/monitoring/event_stream_snapshot.json")
history_path = Path("results/monitoring/event_stream_history.jsonl")
summary_path = Path("results/monitoring/event_stream_summary.json")

assert snapshot_path.exists()
assert history_path.exists()
assert summary_path.exists()

saved_snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
saved_summary = json.loads(summary_path.read_text(encoding="utf-8"))

assert saved_snapshot.get("stream_count", 0) > 0
assert isinstance(saved_snapshot.get("streams", []), list)
assert saved_summary.get("health_status") in ["HEALTHY", "DEGRADED"]

print(f"[PASS] stream_count = {saved_snapshot['stream_count']}")
print(f"[PASS] active_streams = {saved_snapshot['active_streams']}")
print(f"[PASS] empty_streams = {saved_snapshot['empty_streams']}")
print(f"[PASS] error_streams = {saved_snapshot['error_streams']}")
print(f"[PASS] total_events = {saved_snapshot['total_events']}")
print(f"[PASS] health_status = {saved_summary['health_status']}")

if saved_summary.get("inactive_critical_streams"):
    print(
        f"[WARN] inactive critical streams = "
        f"{saved_summary['inactive_critical_streams']}"
    )

print("=" * 80)
print("[PASS] PHASE 4F EVENT STREAM MONITOR VALIDATION COMPLETE")
print("=" * 80)