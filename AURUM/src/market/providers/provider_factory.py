from __future__ import annotations

import os

from src.market.providers.alpaca_provider import AlpacaProvider
from src.market.providers.base_provider import MarketProvider
from src.market.providers.polygon_provider import PolygonProvider
from src.market.providers.yfinance_provider import YFinanceProvider


def get_provider(name: str | None = None) -> MarketProvider:
    selected = (name or os.getenv("AURUM_MARKET_PROVIDER") or "yfinance").lower()

    if selected == "yfinance":
        return YFinanceProvider()

    if selected == "polygon":
        return PolygonProvider()

    if selected == "alpaca":
        return AlpacaProvider()

    raise ValueError(f"Unknown market provider: {selected}")


def available_providers() -> list[str]:
    return ["yfinance", "polygon", "alpaca"]