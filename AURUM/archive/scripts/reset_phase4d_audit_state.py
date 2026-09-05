# scripts/reset_phase4d_audit_state.py

from pathlib import Path
import os
import redis


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

FILES_TO_DELETE = [
    Path("results/governance/execution_audit_log.jsonl"),
    Path("results/governance/current_cycle_audit_log.jsonl"),
    Path("results/governance/execution_audit_summary.json"),
    Path("results/governance/institutional_audit_report.json"),
    Path("results/governance/institutional_audit_report.txt"),
    Path("results/governance/state/processed_audit_events.json"),
]

STREAMS_TO_DELETE = [
    "execution_audit",
    "governance_events",
    "governance_alerts",
]


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 4D AUDIT STATE RESET")
    print("=" * 80)

    for path in FILES_TO_DELETE:
        if path.exists():
            path.unlink()
            print(f"[DELETED] {path}")
        else:
            print(f"[SKIP] missing {path}")

    try:
        r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        r.ping()

        for stream in STREAMS_TO_DELETE:
            deleted = r.delete(stream)
            if deleted:
                print(f"[DELETED] Redis stream: {stream}")
            else:
                print(f"[SKIP] Redis stream missing: {stream}")

    except Exception as exc:
        print(f"[WARN] Redis reset failed: {exc}")

    print("=" * 80)
    print("[PASS] AUDIT STATE RESET COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()