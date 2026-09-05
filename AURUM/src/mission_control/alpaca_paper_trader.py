"""
AURUM Alpaca Paper Trading Integration

Connects AURUM to Alpaca paper trading account.
- Reads real account value, positions, P&L from Alpaca
- Places paper trades based on target weights from portfolio directive
- Writes results to results/mission_control/alpaca_state.json

Run:
    python -m src.mission_control.alpaca_paper_trader
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = ROOT / "results"
MISSION_DIR = RESULTS_DIR / "mission_control"
ALPACA_STATE_PATH = MISSION_DIR / "alpaca_state.json"

BASE_URL = "https://paper-api.alpaca.markets"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_env() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def get_headers() -> dict[str, str]:
    return {
        "APCA-API-KEY-ID": os.environ.get("ALPACA_API_KEY", ""),
        "APCA-API-SECRET-KEY": os.environ.get("ALPACA_SECRET_KEY", ""),
    }


def read_json(path: Path, default: Any = None) -> Any:
    if default is None:
        default = {}
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default
    return default


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def get_account() -> dict[str, Any]:
    """Fetch real paper account data from Alpaca."""
    try:
        r = requests.get(
            f"{BASE_URL}/v2/account",
            headers=get_headers(),
            timeout=10,
        )
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"  [Alpaca] Account fetch error: {e}")
    return {}


def get_positions() -> list[dict[str, Any]]:
    """Fetch current paper positions from Alpaca."""
    try:
        r = requests.get(
            f"{BASE_URL}/v2/positions",
            headers=get_headers(),
            timeout=10,
        )
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"  [Alpaca] Positions fetch error: {e}")
    return []


def get_portfolio_history() -> dict[str, Any]:
    """Fetch portfolio value history for P&L calculation."""
    try:
        r = requests.get(
            f"{BASE_URL}/v2/account/portfolio/history?period=1M&timeframe=1D",
            headers=get_headers(),
            timeout=10,
        )
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"  [Alpaca] History fetch error: {e}")
    return {}


def get_target_weights() -> dict[str, float]:
    """
    Read target weights from the portfolio directive.
    Falls back to default defensive allocation if not found.
    """
    sources = [
        RESULTS_DIR / "portfolio_os" / "portfolio_directive.json",
        RESULTS_DIR / "cio" / "cio_portfolio_directive.json",
        MISSION_DIR / "portfolio_state.json",
    ]

    for path in sources:
        data = read_json(path, {})
        for key in ["target_weights", "weights", "recommended_weights"]:
            weights = data.get(key)
            if isinstance(weights, dict) and weights:
                # Normalize
                clean = {}
                for k, v in weights.items():
                    try:
                        clean[str(k).upper()] = float(v)
                    except Exception:
                        pass
                total = sum(clean.values())
                if total > 1.5:
                    clean = {k: v / 100 for k, v in clean.items()}
                return clean

    # Default defensive allocation
    return {
        "SPY": 0.20,
        "QQQ": 0.10,
        "TLT": 0.40,
        "GLD": 0.20,
        "CASH": 0.10,
    }


def calculate_trades(
    current_positions: list[dict[str, Any]],
    target_weights: dict[str, float],
    portfolio_value: float,
) -> list[dict[str, Any]]:
    """
    Calculate what trades need to be placed to reach target weights.
    Returns list of trade instructions.
    """
    # Current position values
    current_values: dict[str, float] = {}
    for pos in current_positions:
        symbol = pos.get("symbol", "").upper()
        market_value = float(pos.get("market_value", 0))
        current_values[symbol] = market_value

    trades = []
    for asset, target_weight in target_weights.items():
        if asset == "CASH":
            continue

        target_value = portfolio_value * target_weight
        current_value = current_values.get(asset, 0.0)
        delta_value = target_value - current_value

        # Only trade if drift is more than 2% of portfolio
        if abs(delta_value) < portfolio_value * 0.02:
            continue

        trades.append({
            "symbol": asset,
            "side": "buy" if delta_value > 0 else "sell",
            "notional": round(abs(delta_value), 2),
            "delta_value": round(delta_value, 2),
            "target_weight": target_weight,
            "current_value": current_value,
        })

    return trades


def place_trade(trade: dict[str, Any]) -> dict[str, Any]:
    """Place a single paper trade on Alpaca."""
    symbol = trade["symbol"]
    side = trade["side"]
    notional = trade["notional"]

    # Skip crypto and VIX — not tradeable as ETFs on Alpaca paper
    if symbol in {"BTC-USD", "ETH-USD", "VIX", "DIA"}:
        return {"symbol": symbol, "status": "skipped", "reason": "not_supported"}

    payload = {
        "symbol": symbol,
        "notional": str(round(notional, 2)),
        "side": side,
        "type": "market",
        "time_in_force": "day",
    }

    try:
        r = requests.post(
            f"{BASE_URL}/v2/orders",
            headers={**get_headers(), "Content-Type": "application/json"},
            json=payload,
            timeout=10,
        )
        if r.status_code in {200, 201}:
            data = r.json()
            return {
                "symbol": symbol,
                "status": "placed",
                "order_id": data.get("id"),
                "side": side,
                "notional": notional,
            }
        else:
            return {
                "symbol": symbol,
                "status": "failed",
                "error": r.text[:200],
            }
    except Exception as e:
        return {"symbol": symbol, "status": "error", "error": str(e)}


def run_alpaca_cycle(place_trades: bool = False) -> dict[str, Any]:
    """
    Main cycle:
    1. Fetch account data
    2. Fetch positions
    3. Calculate P&L
    4. Optionally place rebalancing trades
    5. Write state file
    """
    load_env()
    print("  [Alpaca] Fetching account...")
    account = get_account()

    if not account:
        result = {
            "timestamp": utc_now(),
            "status": "error",
            "error": "Could not connect to Alpaca",
        }
        write_json(ALPACA_STATE_PATH, result)
        return result

    portfolio_value = float(account.get("portfolio_value", 100000))
    cash = float(account.get("cash", 100000))
    equity = float(account.get("equity", 100000))
    last_equity = float(account.get("last_equity", 100000))
    daily_pnl = round(equity - last_equity, 2)
    daily_pnl_pct = round((daily_pnl / last_equity) * 100, 4) if last_equity > 0 else 0.0

    print(f"  [Alpaca] Portfolio value: ${portfolio_value:,.2f}")
    print(f"  [Alpaca] Daily P&L: ${daily_pnl:+,.2f} ({daily_pnl_pct:+.2f}%)")

    print("  [Alpaca] Fetching positions...")
    positions = get_positions()

    position_rows = []
    for pos in positions:
        symbol = pos.get("symbol", "")
        qty = float(pos.get("qty", 0))
        market_value = float(pos.get("market_value", 0))
        unrealized_pl = float(pos.get("unrealized_pl", 0))
        unrealized_plpc = float(pos.get("unrealized_plpc", 0))
        current_price = float(pos.get("current_price", 0))
        weight = market_value / portfolio_value if portfolio_value > 0 else 0

        position_rows.append({
            "symbol": symbol,
            "qty": qty,
            "market_value": round(market_value, 2),
            "weight_pct": round(weight * 100, 2),
            "current_price": current_price,
            "unrealized_pl": round(unrealized_pl, 2),
            "unrealized_plpc": round(float(unrealized_plpc) * 100, 2),
        })

    # Calculate target weights and trades needed
    target_weights = get_target_weights()
    trades_needed = calculate_trades(positions, target_weights, portfolio_value)

    trade_results = []
    if place_trades and trades_needed:
        print(f"  [Alpaca] Placing {len(trades_needed)} rebalancing trades...")
        for trade in trades_needed:
            result = place_trade(trade)
            trade_results.append(result)
            print(f"    {trade['symbol']}: {result['status']}")
    elif trades_needed:
        print(f"  [Alpaca] {len(trades_needed)} trades needed (not placing — governance blocked)")

    state = {
        "timestamp": utc_now(),
        "status": "ok",
        "account": {
            "portfolio_value": portfolio_value,
            "cash": cash,
            "equity": equity,
            "daily_pnl": daily_pnl,
            "daily_pnl_pct": daily_pnl_pct,
            "buying_power": float(account.get("buying_power", 0)),
        },
        "positions": position_rows,
        "target_weights": target_weights,
        "trades_needed": trades_needed,
        "trade_results": trade_results,
        "trades_placed": len(trade_results),
    }

    write_json(ALPACA_STATE_PATH, state)
    return state


def main() -> None:
    state = run_alpaca_cycle(place_trades=False)

    print("=" * 80)
    print("AURUM ALPACA PAPER TRADING")
    print("=" * 80)
    if state.get("status") == "ok":
        acc = state["account"]
        print(f"Portfolio Value:  ${acc['portfolio_value']:,.2f}")
        print(f"Cash:             ${acc['cash']:,.2f}")
        print(f"Daily P&L:        ${acc['daily_pnl']:+,.2f} ({acc['daily_pnl_pct']:+.2f}%)")
        print(f"Positions:        {len(state['positions'])}")
        print(f"Trades needed:    {len(state['trades_needed'])}")
        if state["positions"]:
            print("\nCurrent Positions:")
            for p in state["positions"]:
                print(f"  {p['symbol']:8s}  ${p['market_value']:>10,.2f}  {p['weight_pct']:>6.1f}%  P&L: ${p['unrealized_pl']:+,.2f}")
        if state["trades_needed"]:
            print("\nTrades Needed:")
            for t in state["trades_needed"]:
                print(f"  {t['side'].upper():4s}  {t['symbol']:8s}  ${t['notional']:>10,.2f}")
    else:
        print(f"Error: {state.get('error')}")
    print("=" * 80)


if __name__ == "__main__":
    main()