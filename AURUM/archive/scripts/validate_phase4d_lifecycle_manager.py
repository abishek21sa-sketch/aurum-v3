# scripts/validate_phase4d_lifecycle_manager.py

from __future__ import annotations

import importlib
import json
import os
from pathlib import Path

import redis

from src.portfolio.portfolio_lifecycle_manager import run_portfolio_lifecycle_manager


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

STATE_PATH = Path("results/portfolio/institutional_portfolio_state.json")
SUMMARY_PATH = Path("results/portfolio/portfolio_lifecycle_summary.json")


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


def check_state_file() -> bool:
    data = load_json(STATE_PATH)

    if not data:
        print(f"[FAIL] missing institutional state file: {STATE_PATH}")
        return False

    required = [
        "timestamp",
        "portfolio_id",
        "market_state",
        "risk_state",
        "decision_state",
        "optimization_state",
        "execution_state",
        "position_state",
        "performance_state",
        "governance_state",
        "lifecycle_status",
        "state_version",
    ]

    missing = [field for field in required if field not in data]

    if missing:
        print(f"[FAIL] institutional state missing fields: {missing}")
        return False

    print(
        f"[PASS] institutional state file valid | "
        f"status={data['lifecycle_status']} version={data['state_version']}"
    )
    return True


def check_summary_file() -> bool:
    data = load_json(SUMMARY_PATH)

    if not data:
        print(f"[FAIL] missing lifecycle summary: {SUMMARY_PATH}")
        return False

    required = [
        "timestamp",
        "portfolio_id",
        "lifecycle_status",
        "governance_status",
        "alerts",
        "gross_exposure",
        "cash_weight",
        "aggregate_fill_ratio",
        "total_execution_cost_bps",
    ]

    missing = [field for field in required if field not in data]

    if missing:
        print(f"[FAIL] lifecycle summary missing fields: {missing}")
        return False

    print(
        f"[PASS] lifecycle summary valid | "
        f"governance={data['governance_status']} alerts={len(data['alerts'])}"
    )
    return True


def check_redis_stream() -> bool:
    try:
        r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        r.ping()

        length = r.xlen("institutional_portfolio_state")

        if length <= 0:
            print("[FAIL] institutional_portfolio_state stream empty")
            return False

        print(f"[PASS] institutional_portfolio_state stream active | length={length}")
        return True

    except Exception as exc:
        print(f"[FAIL] Redis check failed: {exc}")
        return False


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 4D LIFECYCLE MANAGER VALIDATION")
    print("=" * 80)

    checks = []

    checks.append(check_import("src.portfolio.portfolio_lifecycle_manager"))

    print("-" * 80)
    print("RUNNING LIFECYCLE MANAGER")
    print("-" * 80)

    try:
        state = run_portfolio_lifecycle_manager()
        print(
            f"[PASS] lifecycle manager ran | "
            f"status={state['lifecycle_status']}"
        )
        checks.append(True)
    except Exception as exc:
        print(f"[FAIL] lifecycle manager failed: {exc}")
        checks.append(False)

    print("-" * 80)
    print("OUTPUT CHECKS")
    print("-" * 80)

    checks.append(check_state_file())
    checks.append(check_summary_file())
    checks.append(check_redis_stream())

    print("=" * 80)

    if all(checks):
        print("[PASS] PHASE 4D LIFECYCLE MANAGER VALIDATION COMPLETE")
    else:
        print("[FAIL] PHASE 4D LIFECYCLE MANAGER VALIDATION FAILED")

    print("=" * 80)


if __name__ == "__main__":
    main()