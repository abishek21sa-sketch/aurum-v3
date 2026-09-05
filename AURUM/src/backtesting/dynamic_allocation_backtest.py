import pandas as pd
import numpy as np
from pathlib import Path


class DynamicAllocationBacktester:

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

        regime_weights = pd.read_csv(
            self.optimization_path / "regime_aware_weights.csv"
        )

        transition_matrix = pd.read_csv(
            self.regime_path / "regime_transition_matrix.csv",
            index_col=0
        )

        returns["Date"] = pd.to_datetime(returns["Date"])
        regimes["Date"] = pd.to_datetime(regimes["Date"])

        merged = returns.merge(
            regimes[["Date", "regime"]],
            on="Date",
            how="inner"
        )

        return merged, regime_weights, transition_matrix

    def compute_probabilistic_weights(
        self,
        current_regime,
        regime_weights,
        transition_matrix
    ):

        pivot_weights = regime_weights.pivot(
            index="regime",
            columns="asset",
            values="weight"
        )

        probabilities = transition_matrix.loc[
            current_regime
        ]

        weighted_rows = []

        for regime, probability in probabilities.items():

            if regime in pivot_weights.index:

                weighted_rows.append(
                    pivot_weights.loc[regime] * probability
                )

        blended_weights = pd.concat(
            weighted_rows,
            axis=1
        ).sum(axis=1)

        blended_weights = (
            blended_weights /
            blended_weights.sum()
        )

        return blended_weights

    def run_backtest(
        self,
        merged,
        regime_weights,
        transition_matrix
    ):

        asset_cols = [
            col for col in merged.columns
            if col not in ["Date", "regime"]
        ]

        records = []

        for _, row in merged.iterrows():

            current_regime = row["regime"]

            weights = self.compute_probabilistic_weights(
                current_regime,
                regime_weights,
                transition_matrix
            )

            aligned_weights = weights.reindex(
                asset_cols
            ).fillna(0)

            portfolio_return = (
                row[asset_cols].values
                @ aligned_weights.values
            )

            record = {
                    "Date": row["Date"],
                    "regime": current_regime,
                    "portfolio_return": portfolio_return
                }
            
            for asset in asset_cols:
                record[f"{asset}_weight"] = aligned_weights[asset]

            records.append(record)

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
            .rolling(60)
            .std()
            * np.sqrt(252)
        )

        portfolio_df["rolling_sharpe"] = (
            portfolio_df["portfolio_return"]
            .rolling(60)
            .mean()
            /
            portfolio_df["portfolio_return"]
            .rolling(60)
            .std()
            * np.sqrt(252)
        )

        return portfolio_df

    def save_outputs(self, portfolio_df):

        self.output_path.mkdir(
            parents=True,
            exist_ok=True
        )

        output_file = (
            self.output_path /
            "dynamic_allocation_backtest.csv"
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

        print("\nDYNAMIC PROBABILISTIC ALLOCATION BACKTEST")
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
        print("DYNAMIC ALLOCATION BACKTEST ENGINE")
        print("=" * 60)

        merged, regime_weights, transition_matrix = self.load_data()

        portfolio_df = self.run_backtest(
            merged,
            regime_weights,
            transition_matrix
        )

        self.save_outputs(portfolio_df)


if __name__ == "__main__":

    backtester = DynamicAllocationBacktester()

    backtester.run()
