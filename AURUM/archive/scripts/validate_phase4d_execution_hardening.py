# scripts/validate_phase4d_execution_hardening.py

from __future__ import annotations

import json
from pathlib import Path

from src.execution.execution_order_generator import run_execution_order_generator
from src.execution.trade_ticket_engine import run_trade_ticket_engine
from src.execution.portfolio_execution_simulator import run_portfolio_execution_simulator


def load_json(path: Path):
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def count_file_rows(path: Path) -> int:
    data = load_json(path)
    return len(data) if isinstance(data, list) else 0


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 4D EXECUTION HARDENING VALIDATION")
    print("=" * 80)

    ticket_path = Path("results/execution/trade_tickets.json")
    report_path = Path("results/execution/execution_reports.json")

    print("PASS 1: normal execution")
    print("-" * 80)

    orders_1 = run_execution_order_generator()
    tickets_1 = run_trade_ticket_engine()
    reports_1 = run_portfolio_execution_simulator()

    print(f"orders_1={len(orders_1)}")
    print(f"new_tickets_1={len(tickets_1)}")
    print(f"new_reports_1={len(reports_1)}")

    tickets_after_pass_1 = count_file_rows(ticket_path)
    reports_after_pass_1 = count_file_rows(report_path)

    print("-" * 80)
    print("PASS 2: replay protection test")
    print("-" * 80)

    orders_2 = run_execution_order_generator()
    tickets_2 = run_trade_ticket_engine()
    reports_2 = run_portfolio_execution_simulator()

    print(f"orders_2={len(orders_2)}")
    print(f"new_tickets_2={len(tickets_2)}")
    print(f"new_reports_2={len(reports_2)}")

    tickets_after_pass_2 = count_file_rows(ticket_path)
    reports_after_pass_2 = count_file_rows(report_path)

    print("-" * 80)
    print("IDEMPOTENCY CHECKS")
    print("-" * 80)

    checks = []

    check_ticket_replay = tickets_2 == []
    checks.append(check_ticket_replay)
    print(
        "[PASS] ticket replay protection"
        if check_ticket_replay
        else "[FAIL] ticket replay protection"
    )

    check_report_replay = reports_2 == []
    checks.append(check_report_replay)
    print(
        "[PASS] execution report replay protection"
        if check_report_replay
        else "[FAIL] execution report replay protection"
    )

    check_ticket_count_stable = tickets_after_pass_1 == tickets_after_pass_2
    checks.append(check_ticket_count_stable)
    print(
        "[PASS] ticket file count stable"
        if check_ticket_count_stable
        else "[FAIL] ticket file count changed"
    )

    check_report_count_stable = reports_after_pass_1 == reports_after_pass_2
    checks.append(check_report_count_stable)
    print(
        "[PASS] report file count stable"
        if check_report_count_stable
        else "[FAIL] report file count changed"
    )

    print("=" * 80)

    if all(checks):
        print("[PASS] PHASE 4D EXECUTION HARDENING VALIDATION COMPLETE")
    else:
        print("[FAIL] PHASE 4D EXECUTION HARDENING VALIDATION FAILED")

    print("=" * 80)


if __name__ == "__main__":
    main()