# scripts/validate_phase4d_position_management.py

from __future__ import annotations

import importlib
import json
import os
from pathlib import Path

import redis

from src.portfolio.position_management_engine import run_position_management_engine


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

LIVE_POSITIONS_PATH = Path("results/portfolio/live_positions.json")
PROCESSED_EXECUTIONS_PATH = Path("results/portfolio/state/processed_execution_ids.json")


def load_json(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def check_import(module_name: str) -> bool:
    try:
        importlib.import_module(module_name)
        print(f"[PASS] import {module_name}")
        return True
    except Exception as exc:
        print(f"[FAIL] import {module_name}: {exc}")
        return False


def check_live_positions_file() -> bool:
    data = load_json(LIVE_POSITIONS_PATH)

    if not data:
        print(f"[FAIL] missing live positions file: {LIVE_POSITIONS_PATH}")
        return False

    required = [
        "timestamp",
        "portfolio_id",
        "positions",
        "gross_exposure",
        "net_exposure",
        "cash_weight",
        "status",
    ]

    missing = [field for field in required if field not in data]

    if missing:
        print(f"[FAIL] live positions missing fields: {missing}")
        return False

    position_sum = sum(float(v) for v in data["positions"].values())

    if abs(position_sum - 1.0) > 0.02:
        print(f"[FAIL] position weights not normalized: sum={position_sum}")
        return False

    print(f"[PASS] live positions file valid | sum={position_sum:.4f}")
    return True


def check_processed_executions_file() -> bool:
    data = load_json(PROCESSED_EXECUTIONS_PATH)

    if data is None:
        print(f"[FAIL] missing processed execution state: {PROCESSED_EXECUTIONS_PATH}")
        return False

    if not isinstance(data, list):
        print("[FAIL] processed executions state is not a list")
        return False

    print(f"[PASS] processed execution state valid | count={len(data)}")
    return True


def check_redis_stream() -> bool:
    try:
        r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        r.ping()

        length = r.xlen("live_positions")

        if length <= 0:
            print("[FAIL] live_positions stream empty")
            return False

        print(f"[PASS] live_positions stream active | length={length}")
        return True

    except Exception as exc:
        print(f"[FAIL] Redis check failed: {exc}")
        return False


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 4D POSITION MANAGEMENT VALIDATION")
    print("=" * 80)

    checks = []

    checks.append(check_import("src.portfolio.position_management_engine"))

    print("-" * 80)
    print("PASS 1: APPLY EXECUTION REPORTS")
    print("-" * 80)

    snapshot_1 = run_position_management_engine()
    print(f"[PASS] position manager ran | processed={snapshot_1['processed_executions']}")

    checks.append(snapshot_1["processed_executions"] >= 0)

    print("-" * 80)
    print("PASS 2: REPLAY PROTECTION")
    print("-" * 80)

    snapshot_2 = run_position_management_engine()
    print(f"[PASS] position manager reran | processed={snapshot_2['processed_executions']}")

    replay_protected = snapshot_2["processed_executions"] == 0

    if replay_protected:
        print("[PASS] execution replay protection")
    else:
        print("[FAIL] execution replay protection")

    checks.append(replay_protected)

    print("-" * 80)
    print("OUTPUT CHECKS")
    print("-" * 80)

    checks.append(check_live_positions_file())
    checks.append(check_processed_executions_file())
    checks.append(check_redis_stream())

    print("=" * 80)

    if all(checks):
        print("[PASS] PHASE 4D POSITION MANAGEMENT VALIDATION COMPLETE")
    else:
        print("[FAIL] PHASE 4D POSITION MANAGEMENT VALIDATION FAILED")

    print("=" * 80)


if __name__ == "__main__":
    main()