import pandas as pd
import numpy as np
from pathlib import Path


class PortfolioAttributionEngine:

    def __init__(self):

        self.market_path = Path("data/market_matrix")
        self.backtest_path = Path("data/backtesting")
        self.output_path = Path("data/analytics")

    def load_data(self):

        returns = pd.read_csv(
            self.market_path / "market_return_matrix.csv"
        )

        returns["Date"] = pd.to_datetime(returns["Date"])

        returns = returns.set_index("Date")

        backtest = pd.read_csv(
            self.backtest_path / "regime_aware_backtest.csv",
            parse_dates=["Date"]
        )

        backtest = backtest.set_index("Date")

        return returns, backtest

    def compute_asset_return_contribution(
        self,
        returns,
        backtest
    ):

        weights_path = Path(
            "data/optimization/regime_aware_weights.csv"
        )

        regime_weights = pd.read_csv(weights_path)

        pivot_weights = (
            regime_weights
            .pivot(
                index="regime",
                columns="asset",
                values="weight"
            )
        )

        weight_rows = []

        for _, row in backtest.iterrows():

            regime = row["regime"]

            regime_vector = pivot_weights.loc[regime]

            weight_rows.append(regime_vector)

        weights_df = pd.DataFrame(
            weight_rows,
            index=backtest.index
        )

        common_assets = [
            col for col in weights_df.columns
            if col in returns.columns
        ]

        weights_df = weights_df[common_assets]

        aligned_returns = returns.loc[
            weights_df.index,
            common_assets
        ]

        contribution_df = (
            weights_df * aligned_returns
        )

        mean_daily_contribution = contribution_df.mean()

        annualized_contribution = (
            mean_daily_contribution * 252
        )

        attribution = pd.DataFrame({
            "asset": annualized_contribution.index,
            "annualized_return_contribution":
                annualized_contribution.values
        })

        attribution[
            "absolute_contribution"
        ] = (
            attribution[
                "annualized_return_contribution"
            ].abs()
        )

        attribution = attribution.sort_values(
            "absolute_contribution",
            ascending=False
        )

        return attribution

    def compute_regime_contribution(
        self,
        backtest
    ):

        regime_summary = (
            backtest
            .groupby("regime")["portfolio_return"]
            .agg([
                "mean",
                "sum",
                "count",
                "std"
            ])
            .reset_index()
        )

        regime_summary.columns = [
            "regime",
            "mean_return",
            "total_return",
            "observations",
            "volatility"
        ]

        return regime_summary

    def save_outputs(
        self,
        attribution,
        regime_summary
    ):

        self.output_path.mkdir(
            parents=True,
            exist_ok=True
        )

        attribution.to_csv(
            self.output_path / "asset_return_attribution.csv",
            index=False
        )

        regime_summary.to_csv(
            self.output_path / "regime_return_attribution.csv",
            index=False
        )

    def run(self):

        print("=" * 60)
        print("PORTFOLIO ATTRIBUTION ENGINE")
        print("=" * 60)

        returns, backtest = self.load_data()

        attribution = (
            self.compute_asset_return_contribution(
                returns,
                backtest
            )
        )

        regime_summary = (
            self.compute_regime_contribution(
                backtest
            )
        )

        print("\nASSET RETURN ATTRIBUTION")
        print("=" * 60)
        print(attribution.to_string(index=False))

        print("\nREGIME RETURN ATTRIBUTION")
        print("=" * 60)
        print(regime_summary.to_string(index=False))

        self.save_outputs(
            attribution,
            regime_summary
        )

        print("\nSaved attribution outputs:")
        print("data/analytics/asset_return_attribution.csv")
        print("data/analytics/regime_return_attribution.csv")


if __name__ == "__main__":

    engine = PortfolioAttributionEngine()

    engine.run()
