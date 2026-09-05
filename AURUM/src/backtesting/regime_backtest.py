import pandas as pd
import numpy as np
from pathlib import Path


class RegimeBacktester:

    def __init__(self):

        self.matrix_path = Path("data/market_matrix")
        self.regime_path = Path("data/regimes")
        self.optimization_path = Path("data/optimization")
        self.output_path = Path("data/backtesting")

    def load_data(self):

        returns = pd.read_csv(
            self.matrix_path / "market_return_matrix.csv"
        )

        regimes = pd.read_csv(
            self.regime_path / "market_regimes.csv"
        )

        weights = pd.read_csv(
            self.optimization_path / "regime_aware_weights.csv"
        )

        returns["Date"] = pd.to_datetime(returns["Date"])
        regimes["Date"] = pd.to_datetime(regimes["Date"])

        merged = returns.merge(
            regimes[["Date", "regime"]],
            on="Date",
            how="inner"
        )

        return merged, weights

    def build_weight_lookup(self, weights):

        lookup = {}

        for regime in weights["regime"].unique():

            regime_weights = weights[
                weights["regime"] == regime
            ].set_index("asset")["weight"]

            lookup[regime] = regime_weights

        return lookup

    def run_backtest(self, merged, weights):

        asset_cols = [
            col for col in merged.columns
            if col not in ["Date", "regime"]
        ]

        weight_lookup = self.build_weight_lookup(weights)

        records = []

        for _, row in merged.iterrows():

            regime = row["regime"]

            if regime not in weight_lookup:
                continue

            regime_weights = weight_lookup[regime].reindex(
                asset_cols
            ).fillna(0).values

            portfolio_return = (
                row[asset_cols].values @ regime_weights
            )

            records.append(
                {
                    "Date": row["Date"],
                    "regime": regime,
                    "portfolio_return": portfolio_return
                }
            )

        portfolio_df = pd.DataFrame(records)

        portfolio_df["cumulative_return"] = (
            1 + portfolio_df["portfolio_return"]
        ).cumprod() - 1

        portfolio_df["running_max"] = (
            1 + portfolio_df["cumulative_return"]
        ).cummax()

        portfolio_df["drawdown"] = (
            (1 + portfolio_df["cumulative_return"])
            / portfolio_df["running_max"]
            - 1
        )

        portfolio_df["rolling_volatility"] = (
            portfolio_df["portfolio_return"]
            .rolling(20)
            .std()
        )

        portfolio_df["rolling_sharpe"] = (
            portfolio_df["portfolio_return"]
            .rolling(20)
            .mean()
            /
            portfolio_df["portfolio_return"]
            .rolling(20)
            .std()
        )

        return portfolio_df

    def save_outputs(self, portfolio_df):

        self.output_path.mkdir(
            parents=True,
            exist_ok=True
        )

        output_file = (
            self.output_path /
            "regime_aware_backtest.csv"
        )

        portfolio_df.to_csv(
            output_file,
            index=False
        )

        total_return = portfolio_df["cumulative_return"].iloc[-1]

        annualized_return = (
            (1 + total_return) ** (252 / len(portfolio_df)) - 1
        )

        annualized_volatility = (
            portfolio_df["portfolio_return"].std() * np.sqrt(252)
        )

        sharpe_ratio = (
            annualized_return / annualized_volatility
            if annualized_volatility > 0
            else 0
        )

        max_drawdown = portfolio_df["drawdown"].min()

        print("\nREGIME-AWARE DYNAMIC BACKTEST")
        print("=" * 60)

        print(f"Total Return: {total_return:.6f}")
        print(f"Annualized Return: {annualized_return:.6f}")
        print(f"Annualized Volatility: {annualized_volatility:.6f}")
        print(f"Sharpe Ratio: {sharpe_ratio:.6f}")
        print(f"Max Drawdown: {max_drawdown:.6f}")

        print("\nRegime Usage:")
        print(
            portfolio_df["regime"]
            .value_counts()
            .to_string()
        )

        print(f"\nSaved backtest: {output_file}")

    def run(self):

        print("=" * 60)
        print("REGIME-AWARE BACKTEST ENGINE")
        print("=" * 60)

        merged, weights = self.load_data()

        portfolio_df = self.run_backtest(
            merged,
            weights
        )

        self.save_outputs(portfolio_df)


if __name__ == "__main__":

    backtester = RegimeBacktester()

    backtester.run()
