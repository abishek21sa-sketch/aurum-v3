from __future__ import annotations

import argparse
import os
import random
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.realtime.event_bus import RedisEventBus, EVENT_STREAMS
from src.market_data.market_data_service import MarketDataService
from src.market.providers.provider_factory import get_provider

DEFAULT_TICKERS = ["SPY", "QQQ", "DIA", "TLT", "GLD", "BTC-USD", "ETH-USD", "VIX"]


class MarketDataGateway:
    """
    Real-time market data gateway.

    Supported modes:
    - demo: synthetic infrastructure-validation ticks
    - yfinance: external research-grade market data snapshot polling

    Future production providers:
    - polygon
    - alpaca
    - databento
    - ibkr
    """

    def __init__(
        self,
        event_bus: RedisEventBus,
        tickers: Optional[List[str]] = None,
        provider: str = "demo",
        interval_seconds: float = 1.0,
    ) -> None:
        self.event_bus = event_bus
        self.tickers = tickers or DEFAULT_TICKERS
        self.provider = provider.lower().strip()
        self.interval_seconds = interval_seconds
        self.market = MarketDataService()

        self.external_provider = None
        if self.provider in {"yfinance", "polygon", "alpaca"}:
            self.external_provider = get_provider(self.provider)

        self.demo_prices = {
            "SPY": 520.0,
            "QQQ": 450.0,
            "DIA": 390.0,
            "TLT": 92.0,
            "GLD": 215.0,
            "BTC-USD": 68000.0,
            "ETH-USD": 3500.0,
            "VIX": 15.0,
        }

    @staticmethod
    def utc_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def normalize_tick(
        self,
        ticker: str,
        price: float,
        volume: float,
        source: str,
        raw: Optional[Dict[str, Any]] = None,
        timestamp: Optional[str] = None,
    ) -> Dict[str, Any]:
        return {
            "event_type": "tick",
            "source": source,
            "ticker": ticker,
            "price": round(float(price), 6),
            "volume": round(float(volume), 6),
            "timestamp": timestamp or self.utc_now(),
            "ingested_at": self.utc_now(),
            "raw": raw or {},
        }

    def _generate_demo_tick(self, ticker: str) -> Dict[str, Any]:
        base_price = self.demo_prices.get(ticker, 100.0)

        shock = random.gauss(0, 0.0008)
        new_price = max(base_price * (1 + shock), 0.01)
        self.demo_prices[ticker] = new_price

        volume = max(random.gauss(25_000, 8_000), 100)

        if ticker == "VIX":
            volume = max(random.gauss(5_000, 2_000), 50)

        return self.normalize_tick(
            ticker=ticker,
            price=new_price,
            volume=volume,
            source="demo",
            raw={"mode": "synthetic_validation_tick"},
        )

    def _download_market_snapshot(self):
        ticks = {}

        if self.external_provider is not None:
            try:
                records = self.external_provider.get_prices(
                    tickers=self.tickers,
                    period="5d",
                    interval="1Min",
                )

                for record in records:
                    ticker = record.get("ticker")
                    price = record.get("price")

                    if ticker is None or price is None:
                        print(f"[WARN] no valid provider record: {record}")
                        continue

                    ticks[ticker] = self.normalize_tick(
                        ticker=ticker,
                        price=float(price),
                        volume=float(record.get("volume", 0.0) or 0.0),
                        source=record.get("source", self.provider),
                        raw={
                            "provider": record.get("source", self.provider),
                            "status": record.get("status", "ok"),
                            "mode": "external_provider_layer",
                        },
                        timestamp=record.get("timestamp"),
                    )

                return ticks

            except Exception as exc:
                print(f"[WARN] external provider failed for {self.provider}: {exc}")
                return ticks

        for ticker in self.tickers:
            try:
                history = self.market.get_history(
                    ticker=ticker,
                    period="5d"
                )

                if history is None or history.empty:
                    continue

                latest = history.iloc[-1]

                price = float(latest["Close"])

                volume = float(
                    latest.get("Volume", 0.0)
                )

                ticks[ticker] = self.normalize_tick(
                    ticker=ticker,
                    price=price,
                    volume=volume,
                    source=self.market.provider_name(),
                    raw={
                        "provider": self.market.provider_name(),
                        "mode": "market_provider_layer",
                    },
                )

            except Exception as exc:
                print(
                    f"[WARN] market tick failed for {ticker}: {exc}"
                )

        return ticks

    def run_demo_forever(self) -> None:
        self.print_header()

        while True:
            for ticker in self.tickers:
                tick = self._generate_demo_tick(ticker)
                self.publish_tick(tick)

            time.sleep(self.interval_seconds)

    def run_market_provider_forever(self) -> None:
        self.print_header()

        while True:
            ticks = self._download_market_snapshot()

            for ticker in self.tickers:
                tick = ticks.get(ticker)

                if not tick:
                    print(f"[WARN] no market tick for {ticker}")
                    continue

                self.publish_tick(tick)

            time.sleep(self.interval_seconds)

    def publish_tick(self, tick: Dict[str, Any]) -> str:
        event_id = self.event_bus.publish(EVENT_STREAMS["market_ticks"], tick)

        print(
            f"[TICK] {event_id} | "
            f"{tick['ticker']} | "
            f"price={tick['price']} | "
            f"volume={tick['volume']} | "
            f"source={tick['source']} | "
            f"timestamp={tick['timestamp']}"
        )

        return event_id

    def print_header(self) -> None:
        print("=" * 80)
        print("AURUM MARKET DATA GATEWAY")
        print("=" * 80)
        print(f"Provider: {self.provider}")
        print(f"Tickers: {', '.join(self.tickers)}")
        print(f"Publishing to Redis stream: {EVENT_STREAMS['market_ticks']}")
        print("=" * 80)

    def run(self) -> None:
        if self.provider == "demo":
            self.run_demo_forever()

        elif self.provider in {"yfinance", "polygon", "alpaca"}:
            self.run_market_provider_forever()

        elif self.provider == "databento":
            raise NotImplementedError("Databento production provider is not wired yet.")

        elif self.provider == "ibkr":
            raise NotImplementedError("IBKR production provider is not wired yet.")

        else:
            raise ValueError(f"Unsupported provider: {self.provider}")


def parse_tickers(value: Optional[str]) -> List[str]:
    if not value:
        return DEFAULT_TICKERS

    return [ticker.strip().upper() for ticker in value.split(",") if ticker.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run AURUM real-time market data gateway.")
    parser.add_argument("--provider", default=os.getenv("MARKET_DATA_PROVIDER", "demo"))
    parser.add_argument("--tickers", default=os.getenv("AURUM_TICKERS", ""))
    parser.add_argument(
        "--interval",
        type=float,
        default=float(os.getenv("GATEWAY_INTERVAL_SECONDS", "60")),
    )

    args = parser.parse_args()

    bus = RedisEventBus()
    gateway = MarketDataGateway(
        event_bus=bus,
        tickers=parse_tickers(args.tickers),
        provider=args.provider,
        interval_seconds=args.interval,
    )
    gateway.run()


if __name__ == "__main__":
    main()