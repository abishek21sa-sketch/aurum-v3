"""
AURUM Mission Control 7
Main Runner

Run once:
    python -m src.mission_control.run_aurum_mission_control --once

Run continuously:
    python -m src.mission_control.run_aurum_mission_control --loop --interval 60
"""

from __future__ import annotations

import argparse
import time
from datetime import datetime, timezone
import json
from pathlib import Path

from src.mission_control.live_refresh_worker import run_refresh_cycle
from src.mission_control.dashboard_state_builder import build_dashboard_state
from src.mission_control.agent_activity_feed import update_activity_feed
from src.mission_control.recommendation_card import build_recommendation_card
from src.mission_control.copilot_service import load_context, answer_question
from src.mission_control.portfolio_state_builder import build_portfolio_state
from src.mission_control.alpaca_paper_trader import run_alpaca_cycle

# Market data publishers
def _publish_market_data() -> None:
    """Push fresh prices to Redis from yfinance + Finnhub."""
    try:
        from src.realtime.yfinance_redis_publisher import fetch_prices, publish_to_redis
        records = fetch_prices()
        n = publish_to_redis(records)
        print(f"    yfinance → Redis: {n} ticks")
    except Exception as e:
        print(f"    yfinance publisher failed: {e}")

    try:
        from src.realtime.finnhub_redis_publisher import fetch_all_quotes, publish_to_redis as pub_fh
        records = fetch_all_quotes()
        n = pub_fh(records)
        print(f"    Finnhub → Redis: {n} ticks")
    except Exception as e:
        print(f"    Finnhub publisher failed: {e}")

ROOT = Path(__file__).resolve().parents[2]
MISSION_DIR = ROOT / "results" / "mission_control"
RUNNER_STATUS_PATH = MISSION_DIR / "runner_status.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_runner_status(status: str, cycle_count: int, interval: int | None = None) -> None:
    MISSION_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp": utc_now(),
        "runner_status": status,
        "cycle_count": cycle_count,
        "interval_seconds": interval,
        "last_cycle_time": utc_now(),
        "next_refresh_seconds": interval if status == "running" else None,
    }
    RUNNER_STATUS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def run_mission_control_cycle(cycle_count: int = 1, interval: int | None = None) -> None:
    write_runner_status("running", cycle_count, interval)
    print("=" * 90)
    print("AURUM MISSION CONTROL CYCLE")
    print("=" * 90)

    print("[1] Publishing market data to Redis...")
    _publish_market_data()

    print("[1B] Running live refresh worker...")
    refresh = run_refresh_cycle()
    print(f"    Status: {refresh.status}")
    print(f"    Market data: {refresh.market_data_status}")
    print(f"    Regime: {refresh.regime}")
    print(f"    Execution: {refresh.execution_permission}")

    print("[2] Building dashboard state...")
    state = build_dashboard_state()
    print(f"    Dashboard timestamp: {state.get('timestamp')}")

    print("[3] Updating agent activity feed...")
    events = update_activity_feed()
    print(f"    Agent events: {len(events)}")

    print("[4] Building recommendation card...")
    card = build_recommendation_card()
    print(f"    Action: {card.get('recommended_action')}")
    print(f"    Next best action: {card.get('next_best_action')}")

    print("[4A] Syncing Alpaca paper trading...")
    alpaca = run_alpaca_cycle(place_trades=False)
    acc = alpaca.get("account", {})
    alpaca_value = acc.get("portfolio_value", 0)
    alpaca_pnl = acc.get("daily_pnl", 0)
    print(f"    Alpaca value: ${alpaca_value:,.2f}")
    print(f"    Daily P&L:   ${alpaca_pnl:+,.2f}")

    print("[4B] Building portfolio state...")
    portfolio_state = build_portfolio_state()
    print(f"    Portfolio value: {portfolio_state.get('portfolio_value')}")

    print("[4C] Refreshing agent health + infrastructure + providers...")
    for module in [
        "src.mission_control.agent_health_builder",
        "src.mission_control.infrastructure_status_builder",
        "src.mission_control.provider_status_builder",
    ]:
        try:
            import subprocess, sys
            subprocess.run(
                [sys.executable, "-m", module],
                cwd=str(ROOT), timeout=30, capture_output=True
            )
        except Exception as e:
            print(f"    {module} skipped: {e}")
    print("    Agent health + infrastructure + providers updated.")

    print("[5] Updating default copilot response...")
    context = load_context()
    response = answer_question("What is the current AURUM status?", context)
    print(f"    Copilot: {response.get('answer')}")

    print("-" * 90)
    print("AURUM Mission Control updated successfully.")
    print("=" * 90)
    write_runner_status("idle_after_success", cycle_count, interval)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run AURUM Mission Control.")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--loop", action="store_true")
    parser.add_argument("--interval", type=int, default=60)
    args = parser.parse_args()

    if not args.once and not args.loop:
        args.once = True

    if args.once:
        run_mission_control_cycle(cycle_count=1, interval=None)
        return

    cycle_count = 1
    while True:
        run_mission_control_cycle(cycle_count=cycle_count, interval=args.interval)
        print(f"Sleeping {args.interval} seconds...")
        write_runner_status("sleeping", cycle_count, args.interval)
        cycle_count += 1
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
