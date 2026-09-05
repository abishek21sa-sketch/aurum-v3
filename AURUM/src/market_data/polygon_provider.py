from src.market_data.market_provider import MarketProvider


class PolygonProvider(MarketProvider):

    def __init__(self, api_key=None):
        self.api_key = api_key

    def get_latest_price(self, ticker):
        raise NotImplementedError

    def get_history(self, ticker, period="1y"):
        raise NotImplementedError

    def get_provider_name(self):
        return "polygon"