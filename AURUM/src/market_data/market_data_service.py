from src.market_data.yfinance_provider import YFinanceProvider


class MarketDataService:

    def __init__(self, provider=None):

        self.provider = provider or YFinanceProvider()

    def get_price(self, ticker):

        return self.provider.get_latest_price(
            ticker
        )

    def get_history(
        self,
        ticker,
        period="1y"
    ):
        return self.provider.get_history(
            ticker,
            period
        )

    def provider_name(self):

        return self.provider.get_provider_name()