from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import redis


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

OUTPUT_DIR = Path("results/realtime")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PATH = OUTPUT_DIR / "live_market_snapshot.json"

REQUIRED_TICKERS = [
    "SPY",
    "QQQ",
    "DIA",
    "TLT",
    "GLD",
    "BTC-USD",
    "ETH-USD",
    "VIX",
]


def decode_event(raw: Dict[str, Any]) -> Dict[str, Any]:
    decoded = {}

    for key, value in raw.items():
        try:
            decoded[key] = json.loads(value)
        except Exception:
            decoded[key] = value

    return decoded


def get_latest_ticks() -> Dict[str, Dict[str, Any]]:
    client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    client.ping()

    rows = client.xrevrange("market_ticks", count=1000)

    latest: Dict[str, Dict[str, Any]] = {}

    for redis_id, raw in rows:
        event = decode_event(raw)
        ticker = event.get("ticker")

        if not ticker:
            continue

        ticker = str(ticker)

        if ticker not in latest:
            event["redis_id"] = redis_id
            latest[ticker] = event

        if all(ticker in latest for ticker in REQUIRED_TICKERS):
            break

    return latest


def generate_snapshot() -> Dict[str, Any]:
    generated_at = datetime.now(timezone.utc).isoformat()
    latest = get_latest_ticks()

    records = []

    for ticker in REQUIRED_TICKERS:
        event = latest.get(ticker, {})

        records.append(
            {
                "ticker": ticker,
                "price": event.get("price"),
                "volume": event.get("volume"),
                "timestamp_utc": event.get("timestamp")
                or event.get("timestamp_utc")
                or event.get("ingested_at"),
                "source": event.get("source", "unknown"),
                "redis_id": event.get("redis_id"),
            }
        )

    snapshot = {
        "platform": "AURUM",
        "artifact": "live_market_snapshot",
        "generated_at": generated_at,
        "record_count": len(records),
        "records": records,
    }

    OUTPUT_PATH.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")

    return snapshot


def main() -> None:
    print("=" * 80)
    print("AURUM LIVE MARKET SNAPSHOT GENERATOR")
    print("=" * 80)

    snapshot = generate_snapshot()

    print(f"Generated At: {snapshot['generated_at']}")
    print(f"Records: {snapshot['record_count']}")
    print(f"Saved: {OUTPUT_PATH}")

    for row in snapshot["records"]:
        print(
            f"{row['ticker']:<8} | "
            f"price={row['price']} | "
            f"timestamp={row['timestamp_utc']} | "
            f"source={row['source']}"
        )


if __name__ == "__main__":
    main()