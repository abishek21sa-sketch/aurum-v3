from __future__ import annotations

import pandas as pd
import yfinance as yf

from src.market.providers.base_provider import MarketProvider


class YFinanceProvider(MarketProvider):
    @property
    def provider_name(self) -> str:
        return "yfinance"

    def get_prices(
        self,
        ticker: str,
        period: str = "1y",
        interval: str = "1d",
    ) -> pd.DataFrame:
        data = yf.download(
            ticker,
            period=period,
            interval=interval,
            auto_adjust=True,
            progress=False,
            threads=False,
        )

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [
                col[0] if isinstance(col, tuple) else col for col in data.columns
            ]

        data.attrs["provider"] = self.provider_name
        data.attrs["ticker"] = ticker
        data.attrs["period"] = period
        data.attrs["interval"] = interval

        return data