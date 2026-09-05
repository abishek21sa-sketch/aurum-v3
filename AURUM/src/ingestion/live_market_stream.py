from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from src.market_data.market_data_service import MarketDataService

market = MarketDataService()

OUTPUT_DIR = Path("data/live")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_TICKERS = ["SPY", "QQQ", "TLT", "GLD", "BTC-USD"]


def _scalar(value):
    if isinstance(value, pd.Series):
        return float(value.iloc[0])
    return float(value)


def fetch_live_market_snapshot(tickers=None) -> pd.DataFrame:
    tickers = tickers or DEFAULT_TICKERS

    rows = []

    for ticker in tickers:
        data = market.get_history(
            ticker,
            period="5d",
            interval="1d",
            progress=False,
            auto_adjust=True,
        )

        if data.empty:
            print(f"[WARN] No data returned for {ticker}")
            continue

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        latest = data.tail(1).iloc[0]
        previous = data.tail(2).iloc[0] if len(data) >= 2 else latest

        close = _scalar(latest["Close"])
        prev_close = _scalar(previous["Close"])
        daily_return = (close / prev_close) - 1 if prev_close != 0 else 0.0

        rows.append(
            {
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "ticker": ticker,
                "open": _scalar(latest["Open"]),
                "high": _scalar(latest["High"]),
                "low": _scalar(latest["Low"]),
                "close": close,
                "volume": _scalar(latest["Volume"]),
                "daily_return": daily_return,
            }
        )

    snapshot = pd.DataFrame(rows)

    output_path = OUTPUT_DIR / "latest_live_market_snapshot.csv"
    snapshot.to_csv(output_path, index=False)

    return snapshot


if __name__ == "__main__":
    df = fetch_live_market_snapshot()
    print("\nLIVE MARKET SNAPSHOT")
    print("=" * 80)
    print(df)