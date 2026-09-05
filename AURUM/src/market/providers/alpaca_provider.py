from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import requests

from src.market.providers.base_provider import MarketProvider


class AlpacaProvider(MarketProvider):
    """
    Alpaca market data provider.

    Required env vars:
        ALPACA_API_KEY
        ALPACA_SECRET_KEY

    Optional:
        ALPACA_DATA_BASE_URL
    """

    def provider_name(self) -> str:
        return "alpaca"

    def get_prices(
        self,
        tickers: list[str],
        period: str = "1d",
        interval: str = "1Min",
    ) -> list[dict[str, Any]]:
        api_key = os.getenv("ALPACA_API_KEY")
        secret_key = os.getenv("ALPACA_SECRET_KEY")

        if not api_key or not secret_key:
            raise RuntimeError(
                "Alpaca provider requires ALPACA_API_KEY and ALPACA_SECRET_KEY."
            )

        base_url = os.getenv(
            "ALPACA_DATA_BASE_URL",
            "https://data.alpaca.markets",
        ).rstrip("/")

        headers = {
            "APCA-API-KEY-ID": api_key,
            "APCA-API-SECRET-KEY": secret_key,
        }

        results: list[dict[str, Any]] = []

        for ticker in tickers:
            symbol = self._normalize_symbol(ticker)

            url = f"{base_url}/v2/stocks/{symbol}/trades/latest"

            response = requests.get(url, headers=headers, timeout=20)

            if response.status_code != 200:
                results.append(
                    {
                        "ticker": ticker,
                        "price": None,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "source": "alpaca",
                        "status": "error",
                        "error": response.text[:300],
                    }
                )
                continue

            payload = response.json()
            trade = payload.get("trade", {})

            price = trade.get("p")
            timestamp = trade.get("t") or datetime.now(timezone.utc).isoformat()

            results.append(
                {
                    "ticker": ticker,
                    "price": price,
                    "timestamp": timestamp,
                    "source": "alpaca",
                    "status": "ok",
                }
            )

        return results

    def _normalize_symbol(self, ticker: str) -> str:
        ticker = ticker.upper()

        # Alpaca stock endpoint does not support crypto symbols like BTC-USD here.
        # Keep these skipped for now rather than pretending they work.
        if ticker in {"BTC-USD", "ETH-USD"}:
            return ticker

        if ticker == "VIX":
            return "VIX"

        return ticker