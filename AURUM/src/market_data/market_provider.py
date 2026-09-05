from abc import ABC, abstractmethod


class MarketProvider(ABC):

    @abstractmethod
    def get_latest_price(self, ticker: str):
        pass

    @abstractmethod
    def get_history(
        self,
        ticker: str,
        period: str = "1y"
    ):
        pass

    @abstractmethod
    def get_provider_name(self):
        pass