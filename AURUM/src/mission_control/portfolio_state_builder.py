"""
AURUM Mission Control - Portfolio State Builder (Real P&L Edition)
"""

from __future__ import annotations

import json
from datetime import datetime, timezone, date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = ROOT / "results"
MISSION_DIR = RESULTS_DIR / "mission_control"

PORTFOLIO_STATE_PATH = MISSION_DIR / "portfolio_state.json"
HISTORY_PATH = MISSION_DIR / "portfolio_value_history.jsonl"

BASE_PORTFOLIO_VALUE = 1_000_000.0


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def today_str() -> str:
    return date.today().isoformat()


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


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def read_history() -> list[dict[str, Any]]:
    if not HISTORY_PATH.exists():
        return []
    records = []
    try:
        for line in HISTORY_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                records.append(json.loads(line))
    except Exception:
        return []
    return records


def get_live_prices() -> dict[str, float]:
    dashboard_state = read_json(MISSION_DIR / "dashboard_state.json", {})
    markets = dashboard_state.get("live_markets", [])
    prices: dict[str, float] = {}
    for item in markets:
        ticker = str(item.get("ticker", "")).upper()
        price = item.get("price")
        if ticker and price is not None:
            try:
                prices[ticker] = float(price)
            except Exception:
                pass
    return prices


def get_reference_prices() -> dict[str, float]:
    ref_path = MISSION_DIR / "portfolio_reference_prices.json"
    data = read_json(ref_path, {})
    return data.get("prices", {})


def store_reference_prices(prices: dict[str, float]) -> None:
    ref_path = MISSION_DIR / "portfolio_reference_prices.json"
    write_json(ref_path, {
        "prices": prices,
        "stored_at": utc_now(),
        "note": "Reference prices. Delete to reset baseline."
    })


def calculate_portfolio_value(
    weights: dict[str, float],
    prices: dict[str, float],
    base_value: float,
) -> float:
    ref_prices = get_reference_prices()

    if not ref_prices:
        store_reference_prices(prices)
        return base_value

    total_return = 0.0
    total_weight = 0.0

    for asset, weight in weights.items():
        if asset == "CASH":
            total_return += weight * 1.0
            total_weight += weight
            continue
        current = prices.get(asset)
        reference = ref_prices.get(asset)
        if current is not None and reference is not None and reference > 0:
            total_return += weight * (current / reference)
            total_weight += weight

    if total_weight <= 0:
        return base_value

    return round(base_value * (total_return / total_weight), 2)


def calculate_pnl_from_history(
    current_value: float,
    history: list[dict[str, Any]],
) -> dict[str, float]:
    if not history:
        return {"daily": 0.0, "mtd": 0.0, "ytd": 0.0}

    today = today_str()
    current_month = today[:7]
    current_year = today[:4]

    prior = [r for r in history if r.get("date") != today]
    if not prior:
        return {"daily": 0.0, "mtd": 0.0, "ytd": 0.0}

    daily_pnl = round(current_value - prior[-1].get("portfolio_value", BASE_PORTFOLIO_VALUE), 2)

    ALPACA_BASE = 100_000.0

    this_month = [r for r in history if r.get("date", "").startswith(current_month)]
    if this_month:
        month_start = this_month[0].get("portfolio_value", ALPACA_BASE)
        if month_start > 500_000:
            month_start = ALPACA_BASE
    else:
        month_start = ALPACA_BASE
    mtd_pnl = round(current_value - month_start, 2)

    this_year = [r for r in history if r.get("date", "").startswith(current_year)]
    if this_year:
        year_start = this_year[0].get("portfolio_value", ALPACA_BASE)
        if year_start > 500_000:
            year_start = ALPACA_BASE
    else:
        year_start = ALPACA_BASE
    ytd_pnl = round(current_value - year_start, 2)

    return {"daily": daily_pnl, "mtd": mtd_pnl, "ytd": ytd_pnl}


def record_today_value(portfolio_value: float) -> None:
    today = today_str()
    history = read_history()
    record = {"date": today, "timestamp": utc_now(), "portfolio_value": portfolio_value}
    if today in [r.get("date") for r in history]:
        updated = [r for r in history if r.get("date") != today]
        updated.append(record)
        HISTORY_PATH.write_text("\n".join(json.dumps(r) for r in updated) + "\n", encoding="utf-8")
    else:
        append_jsonl(HISTORY_PATH, record)


def calculate_pnl_attribution(
    weights: dict[str, float],
    prices: dict[str, float],
    ref_prices: dict[str, float],
    portfolio_value: float,
) -> list[dict[str, Any]]:
    history = read_history()
    today = today_str()
    prior = [r for r in history if r.get("date") != today]
    prev_value = prior[-1].get("portfolio_value", BASE_PORTFOLIO_VALUE) if prior else BASE_PORTFOLIO_VALUE

    attribution = []
    for asset, weight in sorted(weights.items()):
        if asset == "CASH":
            attribution.append({"asset": "CASH", "weight_pct": round(weight * 100, 1), "daily_contribution": 0.0})
            continue
        current = prices.get(asset)
        ref = ref_prices.get(asset)
        if current is not None and ref is not None and ref > 0:
            daily_return = (current / ref) - 1.0
            attribution.append({
                "asset": asset,
                "weight_pct": round(weight * 100, 1),
                "price": current,
                "daily_return_pct": round(daily_return * 100, 2),
                "daily_contribution": round(weight * prev_value * daily_return, 2),
            })

    attribution.sort(key=lambda x: abs(x.get("daily_contribution", 0)), reverse=True)
    return attribution


def extract_weights(data: Any) -> dict[str, float]:
    if not data:
        return {}
    if isinstance(data, dict):
        for key in ["weights", "current_weights", "target_weights", "recommended_weights",
                    "allocation", "current_allocation", "recommended_allocation", "portfolio_weights"]:
            value = data.get(key)
            if isinstance(value, dict):
                return normalize_weights(value)
        flat = {}
        for k, v in data.items():
            if isinstance(v, (int, float)) and str(k).upper() in {
                "SPY", "QQQ", "DIA", "TLT", "GLD", "BTC-USD", "ETH-USD", "VIX", "CASH"
            }:
                flat[k] = float(v)
        if flat:
            return normalize_weights(flat)
    return {}


def normalize_weights(weights: dict[str, Any]) -> dict[str, float]:
    clean = {}
    for k, v in weights.items():
        try:
            clean[str(k).upper()] = round(float(v), 6)
        except Exception:
            pass
    total = sum(clean.values())
    if total > 1.5:
        clean = {k: round(v / 100, 6) for k, v in clean.items()}
    return clean


def build_portfolio_state() -> dict[str, Any]:
    MISSION_DIR.mkdir(parents=True, exist_ok=True)

    candidates = {
        "portfolio_directive": RESULTS_DIR / "portfolio_os" / "portfolio_directive.json",
        "reoptimizer": RESULTS_DIR / "optimization" / "latest_reoptimization.json",
        "rebalance_sim": RESULTS_DIR / "simulation" / "portfolio_rebalance_simulation.json",
        "cio_directive": RESULTS_DIR / "cio" / "cio_portfolio_directive.json",
        "paper_positions": RESULTS_DIR / "execution" / "paper_trading_state.json",
        "live_positions": RESULTS_DIR / "execution" / "live_positions.json",
        "latest_refresh": MISSION_DIR / "latest_refresh.json",
    }

    raw = {name: read_json(path, {}) for name, path in candidates.items()}

    current_weights = {}
    target_weights = {}

    for name in ["paper_positions", "live_positions", "rebalance_sim", "portfolio_directive"]:
        current_weights = extract_weights(raw.get(name))
        if current_weights:
            break

    for name in ["reoptimizer", "portfolio_directive", "cio_directive", "rebalance_sim"]:
        target_weights = extract_weights(raw.get(name))
        if target_weights:
            break

    if not current_weights:
        current_weights = {"SPY": 0.25, "QQQ": 0.20, "TLT": 0.30, "GLD": 0.15, "CASH": 0.10}
    if not target_weights:
        target_weights = {"SPY": 0.20, "QQQ": 0.10, "TLT": 0.40, "GLD": 0.20, "CASH": 0.10}

    # Try Alpaca real value first
    alpaca_state = read_json(MISSION_DIR / "alpaca_state.json", {})
    alpaca_account = alpaca_state.get("account", {})
    alpaca_value = alpaca_account.get("portfolio_value")

    prices = get_live_prices()
    ref_prices = get_reference_prices()

    if alpaca_value and alpaca_value > 0:
        portfolio_value = float(alpaca_value)
    elif prices:
        portfolio_value = calculate_portfolio_value(current_weights, prices, BASE_PORTFOLIO_VALUE)
    else:
        history = read_history()
        portfolio_value = history[-1].get("portfolio_value", BASE_PORTFOLIO_VALUE) if history else BASE_PORTFOLIO_VALUE

    record_today_value(portfolio_value)
    history = read_history()
    pnl = calculate_pnl_from_history(portfolio_value, history)

    attribution = []
    if prices and ref_prices:
        attribution = calculate_pnl_attribution(current_weights, prices, ref_prices, portfolio_value)

    assets = sorted(set(current_weights) | set(target_weights))
    rows = []
    for asset in assets:
        current = current_weights.get(asset, 0.0)
        target = target_weights.get(asset, 0.0)
        rows.append({
            "Asset": asset,
            "Current": round(current * 100, 2),
            "Target": round(target * 100, 2),
            "Delta": round((target - current) * 100, 2),
        })

    turnover = round(sum(abs(r["Delta"]) for r in rows) / 2, 2)

    state = {
        "timestamp": utc_now(),
        "portfolio_value": portfolio_value,
        "daily_pnl": pnl["daily"],
        "mtd_pnl": pnl["mtd"],
        "ytd_pnl": pnl["ytd"],
        "current_weights": current_weights,
        "target_weights": target_weights,
        "allocation_rows": rows,
        "estimated_turnover_pct": turnover,
        "pnl_attribution": attribution,
        "prices_used": prices,
        "data_source": "live_prices" if prices else "historical_fallback",
        "source_files": {name: str(path.relative_to(ROOT)) for name, path in candidates.items()},
    }

    write_json(PORTFOLIO_STATE_PATH, state)
    return state


def main() -> None:
    state = build_portfolio_state()
    print("=" * 80)
    print("AURUM PORTFOLIO STATE BUILDER")
    print("=" * 80)
    print(f"Saved:           {PORTFOLIO_STATE_PATH.relative_to(ROOT)}")
    print(f"Data source:     {state['data_source']}")
    print(f"Portfolio Value: ${state['portfolio_value']:,.2f}")
    print(f"Daily P&L:       ${state['daily_pnl']:+,.2f}")
    print(f"MTD P&L:         ${state['mtd_pnl']:+,.2f}")
    print(f"YTD P&L:         ${state['ytd_pnl']:+,.2f}")
    print(f"Turnover:        {state['estimated_turnover_pct']}%")
    if state.get("pnl_attribution"):
        print("\nP&L Attribution:")
        for item in state["pnl_attribution"][:5]:
            contrib = item.get("daily_contribution", 0)
            print(f"  {item['asset']:8s}  ${contrib:+,.0f}")
    print("=" * 80)


if __name__ == "__main__":
    main()

