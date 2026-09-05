# scripts/reset_phase4d_execution_state.py

from pathlib import Path
import os
import redis


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

FILES_TO_DELETE = [
    Path("results/execution/execution_orders.json"),
    Path("results/execution/trade_tickets.json"),
    Path("results/execution/execution_reports.json"),
    Path("results/execution/state/processed_order_ids.json"),
    Path("results/execution/state/processed_ticket_ids.json"),
]

STREAMS_TO_DELETE = [
    "execution_orders",
    "trade_tickets",
    "execution_reports",
]


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 4D EXECUTION STATE RESET")
    print("=" * 80)

    print("LOCAL FILE RESET")
    print("-" * 80)

    for path in FILES_TO_DELETE:
        if path.exists():
            path.unlink()
            print(f"[DELETED] {path}")
        else:
            print(f"[SKIP] missing {path}")

    print("-" * 80)
    print("REDIS STREAM RESET")
    print("-" * 80)

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
    print("[PASS] PHASE 4D EXECUTION STATE RESET COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()