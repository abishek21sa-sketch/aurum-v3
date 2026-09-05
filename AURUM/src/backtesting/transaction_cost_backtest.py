import pandas as pd
import numpy as np
from pathlib import Path
from scipy.optimize import minimize


class TransactionCostBacktester:

    def __init__(self):

        self.matrix_path = Path("data/market_matrix")
        self.output_path = Path("data/backtesting")

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

        bounds = tuple((0, 1) for _ in range(n_assets))
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
        rebalance_frequency=20,
        transaction_cost_rate=0.001
    ):

        asset_cols = [
            col for col in returns_df.columns
            if col != "Date"
        ]

        portfolio_records = []
        weight_records = []

        previous_weights = np.ones(len(asset_cols)) / len(asset_cols)

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

            new_weights = self.optimize_min_variance(train_window)

            turnover = np.sum(
                np.abs(new_weights - previous_weights)
            )

            transaction_cost = transaction_cost_rate * turnover

            first_day = True

            for _, row in test_window.iterrows():

                gross_return = row[asset_cols].values @ new_weights

                net_return = (
                    gross_return - transaction_cost
                    if first_day
                    else gross_return
                )

                portfolio_records.append(
                    {
                        "Date": row["Date"],
                        "gross_return": gross_return,
                        "transaction_cost": transaction_cost if first_day else 0,
                        "net_return": net_return,
                        "turnover": turnover if first_day else 0
                    }
                )

                first_day = False

            weight_record = {
                "rebalance_date": returns_df.iloc[start_idx]["Date"],
                "turnover": turnover,
                "transaction_cost": transaction_cost
            }

            for asset, weight in zip(asset_cols, new_weights):
                weight_record[asset] = weight

            weight_records.append(weight_record)

            previous_weights = new_weights

        portfolio_df = pd.DataFrame(portfolio_records)
        weights_df = pd.DataFrame(weight_records)

        portfolio_df["gross_cumulative_return"] = (
            1 + portfolio_df["gross_return"]
        ).cumprod() - 1

        portfolio_df["net_cumulative_return"] = (
            1 + portfolio_df["net_return"]
        ).cumprod() - 1

        portfolio_df["running_max"] = (
            1 + portfolio_df["net_cumulative_return"]
        ).cummax()

        portfolio_df["net_drawdown"] = (
            (1 + portfolio_df["net_cumulative_return"])
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
            "transaction_cost_backtest.csv"
        )

        weights_file = (
            self.output_path /
            "transaction_cost_weights.csv"
        )

        portfolio_df.to_csv(portfolio_file, index=False)
        weights_df.to_csv(weights_file, index=False)

        gross_total_return = portfolio_df["gross_cumulative_return"].iloc[-1]
        net_total_return = portfolio_df["net_cumulative_return"].iloc[-1]

        annualized_net_volatility = (
            portfolio_df["net_return"].std() * np.sqrt(252)
        )

        annualized_net_return = (
            (1 + net_total_return) ** (252 / len(portfolio_df)) - 1
        )

        net_sharpe = (
            annualized_net_return / annualized_net_volatility
            if annualized_net_volatility > 0
            else 0
        )

        max_net_drawdown = portfolio_df["net_drawdown"].min()
        total_transaction_cost = portfolio_df["transaction_cost"].sum()
        average_turnover = weights_df["turnover"].mean()

        print("\nTRANSACTION COST BACKTEST")
        print("=" * 60)

        print(f"Gross Total Return: {gross_total_return:.6f}")
        print(f"Net Total Return: {net_total_return:.6f}")
        print(f"Annualized Net Return: {annualized_net_return:.6f}")
        print(f"Annualized Net Volatility: {annualized_net_volatility:.6f}")
        print(f"Net Sharpe Ratio: {net_sharpe:.6f}")
        print(f"Max Net Drawdown: {max_net_drawdown:.6f}")
        print(f"Total Transaction Cost: {total_transaction_cost:.6f}")
        print(f"Average Rebalance Turnover: {average_turnover:.6f}")

        print(f"\nSaved portfolio path: {portfolio_file}")
        print(f"Saved weights path: {weights_file}")

    def run(self):

        print("=" * 60)
        print("TRANSACTION COST BACKTEST ENGINE")
        print("=" * 60)

        returns_df = self.load_returns()

        portfolio_df, weights_df = self.run_backtest(
            returns_df,
            lookback_window=60,
            rebalance_frequency=20,
            transaction_cost_rate=0.001
        )

        self.save_outputs(portfolio_df, weights_df)


if __name__ == "__main__":

    backtester = TransactionCostBacktester()

    backtester.run()
