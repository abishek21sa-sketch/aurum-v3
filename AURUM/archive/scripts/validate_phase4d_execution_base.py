# scripts/validate_phase4d_execution_base.py

from __future__ import annotations

import importlib
import json
import os
from pathlib import Path

import redis


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

STREAMS = [
    "execution_orders",
    "trade_tickets",
    "execution_reports",
]

OUTPUT_FILES = [
    Path("results/execution/execution_orders.json"),
    Path("results/execution/trade_tickets.json"),
    Path("results/execution/execution_reports.json"),
]


def check_import(module_name: str) -> bool:
    try:
        importlib.import_module(module_name)
        print(f"[PASS] import {module_name}")
        return True
    except Exception as exc:
        print(f"[FAIL] import {module_name}: {exc}")
        return False


def check_file(path: Path) -> bool:
    if not path.exists():
        print(f"[FAIL] missing output file: {path}")
        return False

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[FAIL] invalid JSON: {path} | {exc}")
        return False

    if not isinstance(data, list) or len(data) == 0:
        print(f"[FAIL] empty output file: {path}")
        return False

    print(f"[PASS] output file exists: {path} | rows={len(data)}")
    return True


def check_stream(r: redis.Redis, stream: str) -> bool:
    try:
        length = r.xlen(stream)
        if length <= 0:
            print(f"[FAIL] Redis stream empty: {stream}")
            return False

        print(f"[PASS] Redis stream active: {stream} | length={length}")
        return True
    except Exception as exc:
        print(f"[FAIL] Redis stream check failed: {stream} | {exc}")
        return False


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 4D EXECUTION BASE VALIDATION")
    print("=" * 80)

    checks = []

    modules = [
        "src.execution.execution_order_generator",
        "src.execution.trade_ticket_engine",
        "src.execution.portfolio_execution_simulator",
    ]

    for module in modules:
        checks.append(check_import(module))

    print("-" * 80)
    print("RUNNING EXECUTION BASE PIPELINE")
    print("-" * 80)

    from src.execution.execution_order_generator import run_execution_order_generator
    from src.execution.trade_ticket_engine import run_trade_ticket_engine
    from src.execution.portfolio_execution_simulator import run_portfolio_execution_simulator

    try:
        orders = run_execution_order_generator()
        print(f"[PASS] execution order generator ran | orders={len(orders)}")
        checks.append(len(orders) > 0)
    except Exception as exc:
        print(f"[FAIL] execution order generator failed: {exc}")
        checks.append(False)

    try:
        tickets = run_trade_ticket_engine()
        print(f"[PASS] trade ticket engine ran | tickets={len(tickets)}")
        checks.append(len(tickets) > 0)
    except Exception as exc:
        print(f"[FAIL] trade ticket engine failed: {exc}")
        checks.append(False)

    try:
        reports = run_portfolio_execution_simulator()
        print(f"[PASS] execution simulator ran | reports={len(reports)}")
        checks.append(len(reports) > 0)
    except Exception as exc:
        print(f"[FAIL] execution simulator failed: {exc}")
        checks.append(False)

    print("-" * 80)
    print("OUTPUT FILE CHECKS")
    print("-" * 80)

    for path in OUTPUT_FILES:
        checks.append(check_file(path))

    print("-" * 80)
    print("REDIS STREAM CHECKS")
    print("-" * 80)

    try:
        r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        r.ping()
        print("[PASS] Redis connection")
        checks.append(True)

        for stream in STREAMS:
            checks.append(check_stream(r, stream))

    except Exception as exc:
        print(f"[FAIL] Redis connection failed: {exc}")
        checks.append(False)

    print("=" * 80)

    if all(checks):
        print("[PASS] PHASE 4D EXECUTION BASE VALIDATION COMPLETE")
    else:
        print("[FAIL] PHASE 4D EXECUTION BASE VALIDATION FAILED")

    print("=" * 80)


if __name__ == "__main__":
    main()