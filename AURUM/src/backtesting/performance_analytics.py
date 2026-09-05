import pandas as pd
import numpy as np
from pathlib import Path


class PerformanceAnalytics:

    def __init__(self):

        self.backtest_path = Path("data/backtesting")
        self.matrix_path = Path("data/market_matrix")
        self.output_path = Path("data/backtesting")

    def load_data(self):

        portfolio = pd.read_csv(
            self.backtest_path / "regime_aware_backtest.csv"
        )

        market = pd.read_csv(
            self.matrix_path / "market_return_matrix.csv"
        )

        portfolio["Date"] = pd.to_datetime(portfolio["Date"])
        market["Date"] = pd.to_datetime(market["Date"])

        df = portfolio.merge(
            market[["Date", "SPY"]],
            on="Date",
            how="inner"
        )

        return df

    def compute_rolling_beta(self, portfolio_returns, benchmark_returns):

        covariance = portfolio_returns.rolling(60).cov(benchmark_returns)
        benchmark_variance = benchmark_returns.rolling(60).var()

        beta = covariance / benchmark_variance

        return beta

    def compute_analytics(self, df):

        df["benchmark_return"] = df["SPY"]

        df["excess_return"] = (
            df["portfolio_return"] - df["benchmark_return"]
        )

        df["portfolio_cumulative_return"] = (
            1 + df["portfolio_return"]
        ).cumprod() - 1

        df["benchmark_cumulative_return"] = (
            1 + df["benchmark_return"]
        ).cumprod() - 1

        df["rolling_portfolio_volatility"] = (
            df["portfolio_return"]
            .rolling(60)
            .std()
            * np.sqrt(252)
        )

        df["rolling_benchmark_volatility"] = (
            df["benchmark_return"]
            .rolling(60)
            .std()
            * np.sqrt(252)
        )

        df["rolling_sharpe"] = (
            df["portfolio_return"]
            .rolling(60)
            .mean()
            /
            df["portfolio_return"]
            .rolling(60)
            .std()
            * np.sqrt(252)
        )

        df["rolling_alpha"] = (
            df["excess_return"]
            .rolling(60)
            .mean()
            * 252
        )

        df["rolling_beta"] = self.compute_rolling_beta(
            df["portfolio_return"],
            df["benchmark_return"]
        )

        df["running_max"] = (
            1 + df["portfolio_cumulative_return"]
        ).cummax()

        df["drawdown"] = (
            (1 + df["portfolio_cumulative_return"])
            / df["running_max"]
            - 1
        )

        return df

    def save_outputs(self, analytics_df):

        self.output_path.mkdir(
            parents=True,
            exist_ok=True
        )

        output_file = (
            self.output_path /
            "performance_analytics.csv"
        )

        analytics_df.to_csv(
            output_file,
            index=False
        )

        total_return = analytics_df["portfolio_cumulative_return"].iloc[-1]
        benchmark_return = analytics_df["benchmark_cumulative_return"].iloc[-1]
        excess_return = total_return - benchmark_return
        max_drawdown = analytics_df["drawdown"].min()

        annualized_return = (
            (1 + total_return) ** (252 / len(analytics_df)) - 1
        )

        annualized_volatility = (
            analytics_df["portfolio_return"].std() * np.sqrt(252)
        )

        sharpe_ratio = (
            annualized_return / annualized_volatility
            if annualized_volatility > 0
            else 0
        )

        print("\nPERFORMANCE ANALYTICS")
        print("=" * 60)

        print(f"Portfolio Total Return: {total_return:.6f}")
        print(f"Benchmark Total Return: {benchmark_return:.6f}")
        print(f"Excess Return: {excess_return:.6f}")
        print(f"Annualized Return: {annualized_return:.6f}")
        print(f"Annualized Volatility: {annualized_volatility:.6f}")
        print(f"Sharpe Ratio: {sharpe_ratio:.6f}")
        print(f"Max Drawdown: {max_drawdown:.6f}")

        print(f"\nSaved analytics: {output_file}")

    def run(self):

        print("=" * 60)
        print("PERFORMANCE ANALYTICS ENGINE")
        print("=" * 60)

        df = self.load_data()

        analytics_df = self.compute_analytics(df)

        self.save_outputs(analytics_df)


if __name__ == "__main__":

    analytics = PerformanceAnalytics()

    analytics.run()
