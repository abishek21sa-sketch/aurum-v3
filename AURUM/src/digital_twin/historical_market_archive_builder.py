# src/digital_twin/historical_market_archive_builder.py

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import pandas as pd
from src.market_data.market_data_service import MarketDataService

market = MarketDataService()

ASSETS = ["SPY", "QQQ", "DIA", "TLT", "GLD", "^VIX", "BTC-USD", "ETH-USD"]

START_DATE = "2005-01-01"

OUTPUT_DIR = Path("data/digital_twin/historical_prices")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MATRIX_PATH = Path("data/digital_twin/historical_price_matrix.csv")


class HistoricalMarketArchiveBuilder:
    def download_asset(self, ticker: str) -> pd.DataFrame:
        print(f"[DOWNLOAD] {ticker}")

        df = market.get_history(
            ticker,
            start=START_DATE,
            progress=False,
            auto_adjust=True,
        )

        if df.empty:
            raise ValueError(f"No data downloaded for {ticker}")

        if isinstance(df.columns, pd.MultiIndex):
            if "Close" in df.columns.get_level_values(0):
                close = df["Close"]
                if isinstance(close, pd.DataFrame):
                    close = close.iloc[:, 0]
            else:
                close = df.iloc[:, 0]
        else:
            if "Close" in df.columns:
                close = df["Close"]
            elif "Adj Close" in df.columns:
                close = df["Adj Close"]
            else:
                raise ValueError(
                    f"Could not find Close/Adj Close for {ticker}. "
                    f"Columns={list(df.columns)}"
                )

        result = pd.DataFrame(
            {
                "date": pd.to_datetime(df.index),
                "close": close.values,
            }
        )

        result = result.dropna()
        return result

    def safe_name(self, ticker: str) -> str:
        return ticker.replace("^", "").replace("/", "_")

    def build_archive(self) -> Dict[str, pd.DataFrame]:
        archive = {}

        for ticker in ASSETS:
            df = self.download_asset(ticker)
            name = self.safe_name(ticker)

            output_path = OUTPUT_DIR / f"{name}.csv"
            df.to_csv(output_path, index=False)

            archive[name] = df

            print(
                f"[PASS] {name:<8} "
                f"rows={len(df):<6} "
                f"start={df['date'].min().date()} "
                f"end={df['date'].max().date()}"
            )

        return archive

    def build_price_matrix(self, archive: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        matrix = None

        for asset, df in archive.items():
            asset_df = df.rename(columns={"close": asset})[["date", asset]]

            if matrix is None:
                matrix = asset_df
            else:
                matrix = matrix.merge(asset_df, on="date", how="outer")

        if matrix is None:
            raise ValueError("No asset data available for matrix.")

        matrix = matrix.sort_values("date")
        matrix = matrix.ffill()
        matrix = matrix.dropna(how="all")

        MATRIX_PATH.parent.mkdir(parents=True, exist_ok=True)
        matrix.to_csv(MATRIX_PATH, index=False)

        return matrix

    def run(self) -> None:
        print("=" * 80)
        print("AURUM HISTORICAL MARKET ARCHIVE BUILDER")
        print("=" * 80)

        archive = self.build_archive()
        matrix = self.build_price_matrix(archive)

        print("-" * 80)
        print(f"[PASS] Historical price matrix saved: {MATRIX_PATH}")
        print(f"Rows: {len(matrix)}")
        print(f"Earliest Date: {matrix['date'].min().date()}")
        print(f"Latest Date:   {matrix['date'].max().date()}")
        print("HISTORICAL MARKET ARCHIVE COMPLETE")


def main() -> None:
    HistoricalMarketArchiveBuilder().run()


if __name__ == "__main__":
    main()