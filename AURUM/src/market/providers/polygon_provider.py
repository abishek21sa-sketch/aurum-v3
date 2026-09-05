from __future__ import annotations

import os

import pandas as pd

from src.market.providers.base_provider import MarketProvider


class PolygonProvider(MarketProvider):
    @property
    def provider_name(self) -> str:
        return "polygon"

    def get_prices(
        self,
        ticker: str,
        period: str = "1y",
        interval: str = "1d",
    ) -> pd.DataFrame:
        api_key = os.getenv("POLYGON_API_KEY")

        if not api_key:
            raise NotImplementedError(
                "Polygon provider exists but POLYGON_API_KEY is not configured."
            )

        raise NotImplementedError(
            "Polygon provider interface reserved. Implement REST aggregation call next."
        )