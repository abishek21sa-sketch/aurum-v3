import pandas as pd
import numpy as np
from pathlib import Path
from scipy.optimize import minimize


class RollingBacktester:

    def __init__(self):

        self.matrix_path = Path("data/market_matrix")
        self.output_path = Path("data/backtesting")
        self.report_path = Path("results/reports")

    def load_returns(self):

        df = pd.read_csv(
            self.matrix_path / "market_return_matrix.csv"
        )

        df["Date"] = pd.to_datetime(df["Date"])

        return df.sort_values("Date")

    def optimize_min_variance(self, train_returns):

        asset_cols = list(train_returns.columns)

        cov_matrix = train_returns.cov().values
        n_assets = len(asset_cols)

        def portfolio_variance(weights):

            return weights.T @ cov_matrix @ weights

        constraints = (
            {
                "type": "eq",
                "fun": lambda weights: np.sum(weights) - 1
            },
        )

        bounds = tuple(
            (0, 1) for _ in range(n_assets)
        )

        initial_weights = np.ones(n_assets) / n_assets

        result = minimize(
            portfolio_variance,
            initial_weights,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={
                "ftol": 1e-12,
                "maxiter": 1000,
                "disp": False
            }
        )

        if not result.success:
            raise RuntimeError(result.message)

        return result.x

    def run_backtest(
        self,
        returns_df,
        lookback_window=60,
        rebalance_frequency=20
    ):

        asset_cols = [
            col for col in returns_df.columns
            if col != "Date"
        ]

        portfolio_records = []
        weight_records = []

        for start_idx in range(
            lookback_window,
            len(returns_df) - rebalance_frequency,
            rebalance_frequency
        ):

            train_window = returns_df.iloc[
                start_idx - lookback_window:start_idx
            ][asset_cols].dropna()

            test_window = returns_df.iloc[
                start_idx:start_idx + rebalance_frequency
            ][["Date"] + asset_cols].dropna()

            weights = self.optimize_min_variance(
                train_window
            )

            for _, row in test_window.iterrows():

                realized_return = (
                    row[asset_cols].values @ weights
                )

                portfolio_records.append(
                    {
                        "Date": row["Date"],
                        "portfolio_return": realized_return
                    }
                )

            weight_record = {
                "rebalance_date": returns_df.iloc[start_idx]["Date"]
            }

            for asset, weight in zip(asset_cols, weights):
                weight_record[asset] = weight

            weight_records.append(weight_record)

        portfolio_df = pd.DataFrame(portfolio_records)
        weights_df = pd.DataFrame(weight_records)

        portfolio_df["cumulative_return"] = (
            1 + portfolio_df["portfolio_return"]
        ).cumprod() - 1

        portfolio_df["rolling_volatility"] = (
            portfolio_df["portfolio_return"]
            .rolling(window=20)
            .std()
        )

        portfolio_df["rolling_sharpe"] = (
            portfolio_df["portfolio_return"]
            .rolling(window=20)
            .mean()
            /
            portfolio_df["portfolio_return"]
            .rolling(window=20)
            .std()
        )

        portfolio_df["running_max"] = (
            1 + portfolio_df["cumulative_return"]
        ).cummax()

        portfolio_df["drawdown"] = (
            (1 + portfolio_df["cumulative_return"])
            / portfolio_df["running_max"]
            - 1
        )

        return portfolio_df, weights_df

    def save_outputs(self, portfolio_df, weights_df):

        self.output_path.mkdir(
            parents=True,
            exist_ok=True
        )

        portfolio_file = (
            self.output_path /
            "rolling_min_variance_backtest.csv"
        )

        weights_file = (
            self.output_path /
            "rolling_min_variance_weights.csv"
        )

        portfolio_df.to_csv(
            portfolio_file,
            index=False
        )

        weights_df.to_csv(
            weights_file,
            index=False
        )

        total_return = portfolio_df["cumulative_return"].iloc[-1]
        annualized_volatility = (
            portfolio_df["portfolio_return"].std() * np.sqrt(252)
        )

        annualized_return = (
            (1 + total_return) ** (252 / len(portfolio_df)) - 1
        )

        sharpe_ratio = (
            annualized_return / annualized_volatility
            if annualized_volatility > 0
            else 0
        )

        max_drawdown = portfolio_df["drawdown"].min()

        print("\nROLLING MIN-VARIANCE BACKTEST")
        print("=" * 60)

        print(f"Total Return: {total_return:.6f}")
        print(f"Annualized Return: {annualized_return:.6f}")
        print(f"Annualized Volatility: {annualized_volatility:.6f}")
        print(f"Sharpe Ratio: {sharpe_ratio:.6f}")
        print(f"Max Drawdown: {max_drawdown:.6f}")

        print(f"\nSaved portfolio path: {portfolio_file}")
        print(f"Saved weights path: {weights_file}")

    def run(self):

        print("=" * 60)
        print("ROLLING BACKTEST ENGINE")
        print("=" * 60)

        returns_df = self.load_returns()

        portfolio_df, weights_df = self.run_backtest(
            returns_df,
            lookback_window=60,
            rebalance_frequency=20
        )

        self.save_outputs(portfolio_df, weights_df)


if __name__ == "__main__":

    backtester = RollingBacktester()

    backtester.run()
