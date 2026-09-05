"""
AURUM yfinance Redis Publisher

Fetches latest prices via yfinance and pushes them
into the Redis market_ticks stream every cycle.

This bridges yfinance (reliable, free) with the Redis
streaming architecture until Finnhub WebSocket is active.

Run:
    python -m src.realtime.yfinance_redis_publisher
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import redis
import yfinance as yf

ROOT = Path(__file__).resolve().parents[2]

TICKERS = ["SPY", "QQQ", "DIA", "TLT", "GLD", "BTC-USD", "ETH-USD", "^VIX"]
TICKER_DISPLAY = ["SPY", "QQQ", "DIA", "TLT", "GLD", "BTC-USD", "ETH-USD", "VIX"]
STREAM_NAME = "market_ticks"
MAX_STREAM_LENGTH = 50000


def get_redis() -> redis.Redis:
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

    return redis.Redis(
        host=os.environ.get("REDIS_HOST", "localhost"),
        port=int(os.environ.get("REDIS_PORT", 6379)),
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
    )


def fetch_prices() -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc).isoformat()
    records = []

    try:
        data = yf.download(
            tickers=TICKERS,
            period="1d",
            interval="1m",
            progress=False,
            auto_adjust=True,
        )
        close = data["Close"]

        for ticker, display in zip(TICKERS, TICKER_DISPLAY):
            try:
                series = close[ticker].dropna()
                if len(series) == 0:
                    raise ValueError("empty")
                price = float(series.iloc[-1])
                records.append({
                    "ticker": display,
                    "price": str(round(price, 4)),
                    "volume": "0.0",
                    "timestamp": now,
                    "ingested_at": now,
                    "source": "yfinance",
                    "event_type": "tick",
                    "raw": json.dumps({
                        "provider": "yfinance",
                        "yf_symbol": ticker,
                        "mode": "mission_control_cycle",
                    }),
                })
            except Exception as e:
                print(f"  {display}: skipped ({e})")

    except Exception as e:
        print(f"Batch download failed: {e}")

    return records


def publish_to_redis(records: list[dict[str, Any]]) -> int:
    r = get_redis()
    published = 0

    for rec in records:
        try:
            r.xadd(
                STREAM_NAME,
                rec,
                maxlen=MAX_STREAM_LENGTH,
                approximate=True,
            )
            published += 1
        except Exception as e:
            print(f"  Redis publish failed for {rec.get('ticker')}: {e}")

    return published


def main() -> None:
    print("Fetching prices and publishing to Redis...")
    records = fetch_prices()
    published = publish_to_redis(records)
    print(f"Published {published}/{len(records)} ticks to Redis:{STREAM_NAME}")
    for r in records:
        print(f"  {r['ticker']:10s} ${float(r['price']):,.4f}")


if __name__ == "__main__":
    main()