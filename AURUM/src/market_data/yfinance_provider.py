from __future__ import annotations

from src.market_data.market_provider import MarketProvider

try:  # Live market data is optional for offline/unit-test execution.
    import yfinance as yf
except ModuleNotFoundError:  # pragma: no cover - exercised by clean-room runtime
    yf = None


def _require_yfinance():
    if yf is None:
        raise RuntimeError(
            "yfinance is required for live market-data access. Install the repository requirements before running live ingestion."
        )
    return yf


class YFinanceProvider(MarketProvider):
    def get_latest_price(self, ticker):
        client = _require_yfinance()
        data = client.Ticker(ticker)
        return float(data.history(period="1d")["Close"].iloc[-1])

    def get_history(self, ticker, period="1y"):
        client = _require_yfinance()
        return client.download(
            ticker,
            period=period,
            auto_adjust=True,
            progress=False,
        )

    def get_provider_name(self):
        return "yfinance"
