"""
AURUM Finnhub Redis Publisher

Fetches real-time quotes from Finnhub REST API
and pushes them into Redis market_ticks stream.

Runs every cycle alongside yfinance publisher.
Finnhub provides: current price, daily change,
high/low, previous close.

Run:
    python -m src.realtime.finnhub_redis_publisher
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import redis
import requests

ROOT = Path(__file__).resolve().parents[2]

TICKERS = {
    "SPY": "SPY",
    "QQQ": "QQQ",
    "DIA": "DIA",
    "TLT": "TLT",
    "GLD": "GLD",
    "BTC-USD": "BINANCE:BTCUSDT",
    "ETH-USD": "BINANCE:ETHUSDT",
}

STREAM_NAME = "market_ticks"
MAX_STREAM_LENGTH = 50000
FINNHUB_BASE = "https://finnhub.io/api/v1"


def load_env() -> None:
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def get_redis() -> redis.Redis:
    return redis.Redis(
        host=os.environ.get("REDIS_HOST", "localhost"),
        port=int(os.environ.get("REDIS_PORT", 6379)),
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
    )


def fetch_finnhub_quote(symbol: str, api_key: str) -> dict[str, Any] | None:
    try:
        r = requests.get(
            f"{FINNHUB_BASE}/quote",
            params={"symbol": symbol, "token": api_key},
            timeout=5,
        )
        if r.status_code == 200:
            data = r.json()
            if data.get("c") and float(data["c"]) > 0:
                return data
    except Exception as e:
        print(f"  Finnhub {symbol} failed: {e}")
    return None


def fetch_all_quotes() -> list[dict[str, Any]]:
    load_env()
    api_key = os.environ.get("FINNHUB_API_KEY", "")
    if not api_key:
        print("  No FINNHUB_API_KEY found")
        return []

    now = datetime.now(timezone.utc).isoformat()
    records = []

    for display, symbol in TICKERS.items():
        quote = fetch_finnhub_quote(symbol, api_key)
        if quote:
            price = float(quote["c"])
            prev_close = float(quote.get("pc", price))
            change_pct = ((price - prev_close) / prev_close * 100) if prev_close else 0

            records.append({
                "ticker": display,
                "price": str(round(price, 4)),
                "volume": "0.0",
                "timestamp": now,
                "ingested_at": now,
                "source": "finnhub",
                "event_type": "tick",
                "daily_change": str(round(float(quote.get("d", 0)), 4)),
                "daily_change_pct": str(round(change_pct, 4)),
                "high": str(round(float(quote.get("h", price)), 4)),
                "low": str(round(float(quote.get("l", price)), 4)),
                "prev_close": str(round(prev_close, 4)),
                "raw": json.dumps({
                    "provider": "finnhub",
                    "symbol": symbol,
                    "full_quote": quote,
                }),
            })
            print(f"  {display:10s} ${price:,.4f}  ({change_pct:+.2f}%)")
        else:
            print(f"  {display:10s} skipped")

    return records


def publish_to_redis(records: list[dict[str, Any]]) -> int:
    if not records:
        return 0
    r = get_redis()
    published = 0
    for rec in records:
        try:
            r.xadd(STREAM_NAME, rec, maxlen=MAX_STREAM_LENGTH, approximate=True)
            published += 1
        except Exception as e:
            print(f"  Redis publish failed for {rec.get('ticker')}: {e}")
    return published


def main() -> None:
    print("Fetching Finnhub quotes and publishing to Redis...")
    records = fetch_all_quotes()
    published = publish_to_redis(records)
    print(f"Published {published}/{len(records)} Finnhub ticks to Redis:{STREAM_NAME}")


if __name__ == "__main__":
    main()