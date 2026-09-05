import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


class PerformanceAnalyticsVisualizer:

    def __init__(self):

        self.input_path = Path("data/backtesting")
        self.output_path = Path("results/figures")

    def load_analytics(self):

        df = pd.read_csv(
            self.input_path / "performance_analytics.csv"
        )

        df["Date"] = pd.to_datetime(df["Date"])

        return df

    def plot_portfolio_vs_benchmark(self, df):

        plt.figure(figsize=(12, 6))

        plt.plot(
            df["Date"],
            df["portfolio_cumulative_return"],
            label="Regime-Aware Portfolio"
        )

        plt.plot(
            df["Date"],
            df["benchmark_cumulative_return"],
            label="SPY Benchmark"
        )

        plt.title("Portfolio vs Benchmark Cumulative Return", fontsize=16)
        plt.xlabel("Date")
        plt.ylabel("Cumulative Return")
        plt.legend()
        plt.grid(True)

        self.output_path.mkdir(parents=True, exist_ok=True)

        output_file = self.output_path / "portfolio_vs_benchmark_return.png"

        plt.savefig(output_file, dpi=300, bbox_inches="tight")

        print(f"Saved figure: {output_file}")

        plt.show()

    def plot_rolling_alpha(self, df):

        plt.figure(figsize=(12, 6))

        plt.plot(
            df["Date"],
            df["rolling_alpha"]
        )

        plt.title("Rolling Alpha vs SPY", fontsize=16)
        plt.xlabel("Date")
        plt.ylabel("Rolling Annualized Alpha")
        plt.grid(True)

        output_file = self.output_path / "rolling_alpha_vs_spy.png"

        plt.savefig(output_file, dpi=300, bbox_inches="tight")

        print(f"Saved figure: {output_file}")

        plt.show()

    def plot_rolling_beta(self, df):

        plt.figure(figsize=(12, 6))

        plt.plot(
            df["Date"],
            df["rolling_beta"]
        )

        plt.title("Rolling Beta vs SPY", fontsize=16)
        plt.xlabel("Date")
        plt.ylabel("Rolling Beta")
        plt.grid(True)

        output_file = self.output_path / "rolling_beta_vs_spy.png"

        plt.savefig(output_file, dpi=300, bbox_inches="tight")

        print(f"Saved figure: {output_file}")

        plt.show()

    def plot_rolling_volatility(self, df):

        plt.figure(figsize=(12, 6))

        plt.plot(
            df["Date"],
            df["rolling_portfolio_volatility"],
            label="Portfolio Volatility"
        )

        plt.plot(
            df["Date"],
            df["rolling_benchmark_volatility"],
            label="SPY Volatility"
        )

        plt.title("Rolling Volatility: Portfolio vs SPY", fontsize=16)
        plt.xlabel("Date")
        plt.ylabel("Annualized Volatility")
        plt.legend()
        plt.grid(True)

        output_file = self.output_path / "rolling_volatility_portfolio_vs_spy.png"

        plt.savefig(output_file, dpi=300, bbox_inches="tight")

        print(f"Saved figure: {output_file}")

        plt.show()

    def run(self):

        df = self.load_analytics()

        self.plot_portfolio_vs_benchmark(df)
        self.plot_rolling_alpha(df)
        self.plot_rolling_beta(df)
        self.plot_rolling_volatility(df)


if __name__ == "__main__":

    visualizer = PerformanceAnalyticsVisualizer()

    visualizer.run()
