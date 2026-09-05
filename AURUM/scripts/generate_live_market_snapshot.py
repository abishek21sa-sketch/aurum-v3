"""
AURUM Live Market Snapshot Generator

Reads latest prices from Redis market_ticks stream.
Falls back to yfinance if Redis is unavailable.

Run:
    python -m scripts.generate_live_market_snapshot
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
SNAPSHOT_PATH = RESULTS_DIR / "realtime" / "live_market_snapshot.json"
MISSION_DIR = RESULTS_DIR / "mission_control"

REQUIRED_TICKERS = ["SPY", "QQQ", "DIA", "TLT", "GLD", "BTC-USD", "ETH-USD", "VIX"]


def load_env() -> None:
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_from_redis() -> list[dict[str, Any]]:
    import redis as redis_lib
    load_env()
    r = redis_lib.Redis(
        host=os.environ.get("REDIS_HOST", "localhost"),
        port=int(os.environ.get("REDIS_PORT", 6379)),
        decode_responses=True,
        socket_connect_timeout=3,
        socket_timeout=3,
    )
    r.ping()

    rows = r.xrevrange("market_ticks", count=100)
    latest = {}
    for rid, data in rows:
        ticker = data.get("ticker")
        if ticker and ticker not in latest:
            latest[ticker] = data
        if len(latest) >= len(REQUIRED_TICKERS):
            break

    records = []
    now = utc_now()
    for ticker in REQUIRED_TICKERS:
        data = latest.get(ticker)
        if data:
            records.append({
                "ticker": ticker,
                "price": float(data["price"]),
                "timestamp": data.get("ingested_at", now),
                "source": data.get("source", "redis"),
                "freshness": "fresh",
            })
        else:
            records.append({
                "ticker": ticker,
                "price": None,
                "timestamp": now,
                "source": "redis",
                "freshness": "missing",
            })

    return records


def get_from_yfinance() -> list[dict[str, Any]]:
    import yfinance as yf
    TICKERS = ["SPY", "QQQ", "DIA", "TLT", "GLD", "BTC-USD", "ETH-USD", "^VIX"]
    now = utc_now()
    records = []
    for ticker, display in zip(TICKERS, REQUIRED_TICKERS):
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="1d", interval="1m")
            price = float(hist["Close"].dropna().iloc[-1])
            records.append({
                "ticker": display,
                "price": price,
                "timestamp": now,
                "source": "yfinance_fallback",
                "freshness": "fresh",
            })
        except Exception as e:
            records.append({
                "ticker": display,
                "price": None,
                "timestamp": now,
                "source": "yfinance_fallback",
                "freshness": "failed",
            })
    return records


def generate_snapshot() -> dict[str, Any]:
    generated_at = utc_now()

    try:
        records = get_from_redis()
        source = "redis"
        print("  Source: Redis market_ticks stream")
    except Exception as e:
        print(f"  Redis unavailable ({e}), falling back to yfinance...")
        records = get_from_yfinance()
        source = "yfinance_fallback"

    snapshot = {
        "platform": "AURUM",
        "artifact": "live_market_snapshot",
        "generated_at": generated_at,
        "source": source,
        "record_count": len(records),
        "records": records,
    }

    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_PATH.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")

    # Update dashboard_state live_markets
    ds_path = MISSION_DIR / "dashboard_state.json"
    if ds_path.exists():
        try:
            ds = json.loads(ds_path.read_text(encoding="utf-8"))
            ds["live_markets"] = [
                {
                    "ticker": r["ticker"],
                    "price": r["price"],
                    "timestamp": r["timestamp"],
                    "source": r["source"],
                    "freshness": r["freshness"],
                }
                for r in records if r.get("price") is not None
            ]
            ds_path.write_text(json.dumps(ds, indent=2), encoding="utf-8")
        except Exception as e:
            print(f"  Warning: could not update dashboard_state: {e}")

    return snapshot


def main() -> None:
    print("=" * 60)
    print("AURUM LIVE MARKET SNAPSHOT GENERATOR")
    print("=" * 60)
    snapshot = generate_snapshot()
    print(f"Generated: {snapshot['generated_at']}")
    print(f"Source:    {snapshot['source']}")
    print(f"Records:   {snapshot['record_count']}")
    for r in snapshot["records"]:
        if r.get("price"):
            print(f"  {r['ticker']:10s} ${float(r['price']):,.4f}  [{r['source']}]")


if __name__ == "__main__":
    main()
