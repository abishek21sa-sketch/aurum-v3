from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Optional

import pandas as pd


@dataclass
class MarketDataRequest:
    ticker: str
    period: str = "1y"
    interval: str = "1d"
    metadata: Optional[Dict[str, str]] = None


class MarketProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_prices(
        self,
        ticker: str,
        period: str = "1y",
        interval: str = "1d",
    ) -> pd.DataFrame:
        raise NotImplementedError

    def validate_prices(self, data: pd.DataFrame) -> bool:
        if data is None or data.empty:
            return False

        required_any = {"Close", "Adj Close", "close", "price"}
        return any(col in data.columns for col in required_any)