import pandas as pd
import numpy as np
from pathlib import Path


class PerformanceAttributionEngine:

    def __init__(self):

        self.market_path = Path("data/market_matrix")
        self.backtest_path = Path("data/backtesting")
        self.regime_path = Path("data/regimes")
        self.output_path = Path("data/analytics")

    def load_data(self):

        returns = pd.read_csv(
            self.market_path / "market_return_matrix.csv"
        )

        returns["Date"] = pd.to_datetime(returns["Date"])
        returns = returns.set_index("Date")

        backtest = pd.read_csv(
            self.backtest_path / "dynamic_allocation_backtest.csv",
            parse_dates=["Date"]
        )

        return returns, backtest

    def compute_asset_contributions(
        self,
        returns,
        backtest
    ):

        asset_columns = [
            col.replace("_weight", "")
            for col in backtest.columns
            if col.endswith("_weight")
        ]

        contributions = []

        for asset in asset_columns:

            weight_col = f"{asset}_weight"

            aligned_returns = returns.loc[
                backtest["Date"],
                asset
            ].values

            asset_contribution = (
                backtest[weight_col].values
                * aligned_returns
            )

            contributions.append(
                {
                    "asset": asset,
                    "mean_daily_contribution": asset_contribution.mean(),
                    "annualized_contribution": asset_contribution.mean() * 252,
                    "total_contribution": asset_contribution.sum()
                }
            )

        contribution_df = pd.DataFrame(contributions)

        contribution_df = contribution_df.sort_values(
            "annualized_contribution",
            ascending=False
        )

        return contribution_df

    def compute_regime_contributions(
        self,
        backtest
    ):

        regime_contribution = (
            backtest
            .groupby("regime")["portfolio_return"]
            .sum()
            .reset_index()
        )

        regime_contribution.columns = [
            "regime",
            "contribution"
        ]

        regime_contribution = regime_contribution.sort_values(
            "contribution",
            ascending=False
        )

        return regime_contribution

    def save_outputs(
        self,
        asset_contribution,
        regime_contribution
    ):

        self.output_path.mkdir(
            parents=True,
            exist_ok=True
        )

        asset_file = (
            self.output_path /
            "asset_performance_attribution.csv"
        )

        regime_file = (
            self.output_path /
            "regime_performance_attribution.csv"
        )

        asset_contribution.to_csv(
            asset_file,
            index=False
        )

        regime_contribution.to_csv(
            regime_file,
            index=False
        )

        print("\nASSET PERFORMANCE ATTRIBUTION")
        print("=" * 60)
        print(asset_contribution.to_string(index=False))

        print("\nREGIME PERFORMANCE ATTRIBUTION")
        print("=" * 60)
        print(regime_contribution.to_string(index=False))

        print(f"\nSaved asset attribution: {asset_file}")
        print(f"Saved regime attribution: {regime_file}")

    def run_pipeline(self):

        print("=" * 60)
        print("PERFORMANCE ATTRIBUTION ENGINE")
        print("=" * 60)

        returns, backtest = self.load_data()

        asset_contribution = (
            self.compute_asset_contributions(
                returns,
                backtest
            )
        )

        regime_contribution = (
            self.compute_regime_contributions(
                backtest
            )
        )

        self.save_outputs(
            asset_contribution,
            regime_contribution
        )


if __name__ == "__main__":

    engine = PerformanceAttributionEngine()

    engine.run_pipeline()
