import pandas as pd
import numpy as np
from pathlib import Path


class MarketRegimeDetector:

    def __init__(self):

        self.matrix_path = Path("data/market_matrix")
        self.output_path = Path("data/regimes")

    def load_market_data(self):

        df = pd.read_csv(
            self.matrix_path / "market_return_matrix.csv"
        )

        df["Date"] = pd.to_datetime(df["Date"])

        return df

    def compute_market_features(self, df):

        spy_returns = df["SPY"]

        rolling_return = (
            spy_returns
            .rolling(20)
            .mean()
        )

        rolling_volatility = (
            spy_returns
            .rolling(20)
            .std()
        )

        vix_level = df["VIX"]

        features = pd.DataFrame(
            {
                "Date": df["Date"],
                "rolling_return": rolling_return,
                "rolling_volatility": rolling_volatility,
                "vix_level": vix_level
            }
        )

        return features.dropna()

    def classify_regime(self, row):

        if (
            row["rolling_return"] < -0.001
            and row["vix_level"] > 0.02
        ):
            return "crisis"

        elif (
            row["rolling_volatility"] > 0.015
        ):
            return "high_volatility"

        elif (
            row["rolling_return"] > 0.001
            and row["vix_level"] < 0
        ):
            return "bull"

        else:
            return "normal"

    def detect_regimes(self, features):

        features["regime"] = features.apply(
            self.classify_regime,
            axis=1
        )

        return features

    def build_summary(self, regime_df):

        summary = (
            regime_df["regime"]
            .value_counts()
            .reset_index()
        )

        summary.columns = [
            "regime",
            "count"
        ]

        summary["percentage"] = (
            summary["count"]
            / summary["count"].sum()
        )

        return summary

    def save_outputs(self, regime_df, summary):

        self.output_path.mkdir(
            parents=True,
            exist_ok=True
        )

        regime_file = (
            self.output_path /
            "market_regimes.csv"
        )

        summary_file = (
            self.output_path /
            "market_regime_summary.csv"
        )

        regime_df.to_csv(
            regime_file,
            index=False
        )

        summary.to_csv(
            summary_file,
            index=False
        )

        print("\nMARKET REGIME SUMMARY")
        print("=" * 60)

        print(summary.to_string(index=False))

        print(f"\nSaved regimes: {regime_file}")
        print(f"Saved summary: {summary_file}")

    def run_pipeline(self):

        print("=" * 60)
        print("MARKET REGIME DETECTION ENGINE")
        print("=" * 60)

        df = self.load_market_data()

        features = self.compute_market_features(df)

        regime_df = self.detect_regimes(features)

        summary = self.build_summary(regime_df)

        self.save_outputs(
            regime_df,
            summary
        )


if __name__ == "__main__":

    detector = MarketRegimeDetector()

    detector.run_pipeline()
