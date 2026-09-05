import pandas as pd
import numpy as np
from pathlib import Path


class VolatilityForecaster:

    def __init__(self):

        self.matrix_path = Path("data/market_matrix")
        self.output_path = Path("data/forecasting")

    def load_returns(self):

        df = pd.read_csv(
            self.matrix_path / "market_return_matrix.csv"
        )

        df["Date"] = pd.to_datetime(df["Date"])

        return df.sort_values("Date")

    def compute_volatility_forecasts(self, df):

        asset_cols = [
            col for col in df.columns
            if col != "Date"
        ]

        forecast_df = df[["Date"]].copy()

        for asset in asset_cols:

            returns = df[asset]

            forecast_df[f"{asset}_rolling_vol_20"] = (
                returns.rolling(20).std()
            )

            forecast_df[f"{asset}_rolling_vol_60"] = (
                returns.rolling(60).std()
            )

            forecast_df[f"{asset}_ewma_vol"] = (
                returns.ewm(span=20, adjust=False).std()
            )

        return forecast_df.dropna()

    def save_outputs(self, forecast_df):

        self.output_path.mkdir(
            parents=True,
            exist_ok=True
        )

        output_file = (
            self.output_path /
            "volatility_forecasts.csv"
        )

        forecast_df.to_csv(
            output_file,
            index=False
        )

        print("\nVOLATILITY FORECASTS")
        print("=" * 60)

        print(forecast_df.tail().to_string(index=False))

        print(f"\nSaved forecasts: {output_file}")

    def run_pipeline(self):

        print("=" * 60)
        print("VOLATILITY FORECASTING ENGINE")
        print("=" * 60)

        df = self.load_returns()

        forecast_df = self.compute_volatility_forecasts(df)

        self.save_outputs(forecast_df)


if __name__ == "__main__":

    forecaster = VolatilityForecaster()

    forecaster.run_pipeline()
