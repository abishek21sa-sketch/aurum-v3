from pathlib import Path
from datetime import datetime, timezone

import pandas as pd
from src.market_data.market_data_service import MarketDataService

market = MarketDataService()

class LiveMarketSnapshot:
    def __init__(
        self,
        tickers=None,
        output_snapshot_path="data/live/live_market_snapshot.csv",
        output_returns_path="data/live/live_market_return_snapshot.csv",
    ):
        self.tickers = tickers or [
            "SPY",
            "QQQ",
            "DIA",
            "TLT",
            "GLD",
            "BTC-USD",
            "ETH-USD",
            "^VIX",
        ]

        self.output_snapshot_path = Path(output_snapshot_path)
        self.output_returns_path = Path(output_returns_path)

    def fetch_market_data(self):
        data = market.get_history(
            self.tickers,
            period="7d",
            interval="1d",
            auto_adjust=True,
            progress=False,
            group_by="ticker",
        )

        return data

    def build_snapshot(self, data):
        rows = []
        run_timestamp = datetime.now(timezone.utc).isoformat()

        for ticker in self.tickers:
            try:
                ticker_data = data[ticker].dropna()

                if ticker_data.empty:
                    continue

                latest = ticker_data.iloc[-1]
                previous = ticker_data.iloc[-2]

                latest_close = latest["Close"]
                previous_close = previous["Close"]

                daily_return = latest_close / previous_close - 1

                rows.append({
                    "timestamp_utc": run_timestamp,
                    "ticker": ticker,
                    "latest_date": ticker_data.index[-1],
                    "latest_close": latest_close,
                    "previous_close": previous_close,
                    "daily_return": daily_return,
                    "latest_volume": latest.get("Volume", None),
                })

            except Exception as exc:
                rows.append({
                    "timestamp_utc": run_timestamp,
                    "ticker": ticker,
                    "latest_date": None,
                    "latest_close": None,
                    "previous_close": None,
                    "daily_return": None,
                    "latest_volume": None,
                    "error": str(exc),
                })

        return pd.DataFrame(rows)

    def build_return_snapshot(self, snapshot):
        clean = snapshot.dropna(subset=["daily_return"]).copy()

        rename_map = {
            "^VIX": "VIX",
        }

        clean["asset"] = clean["ticker"].replace(rename_map)

        return_matrix = clean.set_index("asset")[["daily_return"]].T
        return_matrix.insert(0, "Date", datetime.now(timezone.utc).date())

        return return_matrix

    def run(self):
        data = self.fetch_market_data()
        snapshot = self.build_snapshot(data)
        return_snapshot = self.build_return_snapshot(snapshot)

        self.output_snapshot_path.parent.mkdir(parents=True, exist_ok=True)

        snapshot.to_csv(self.output_snapshot_path, index=False)
        return_snapshot.to_csv(self.output_returns_path, index=False)

        print("LIVE MARKET SNAPSHOT COMPLETE")
        print("=" * 70)
        print(snapshot.to_string(index=False))
        print()
        print("Return snapshot:")
        print(return_snapshot.to_string(index=False))
        print()
        print(f"Saved snapshot: {self.output_snapshot_path}")
        print(f"Saved returns: {self.output_returns_path}")

        return snapshot, return_snapshot


if __name__ == "__main__":
    engine = LiveMarketSnapshot()
    engine.run()