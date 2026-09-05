import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


class RollingBacktestVisualizer:

    def __init__(self):

        self.input_path = Path("data/backtesting")
        self.output_path = Path("results/figures")

    def load_backtest(self):

        df = pd.read_csv(
            self.input_path / "rolling_min_variance_backtest.csv"
        )

        df["Date"] = pd.to_datetime(df["Date"])

        return df

    def plot_cumulative_return(self, df):

        plt.figure(figsize=(12, 6))

        plt.plot(
            df["Date"],
            df["cumulative_return"]
        )

        plt.title("Rolling Min-Variance Backtest: Cumulative Return", fontsize=16)
        plt.xlabel("Date")
        plt.ylabel("Cumulative Return")
        plt.grid(True)

        self.output_path.mkdir(
            parents=True,
            exist_ok=True
        )

        output_file = (
            self.output_path /
            "rolling_min_variance_cumulative_return.png"
        )

        plt.savefig(
            output_file,
            dpi=300,
            bbox_inches="tight"
        )

        print(f"Saved cumulative return figure: {output_file}")

        plt.show()

    def plot_drawdown(self, df):

        plt.figure(figsize=(12, 6))

        plt.plot(
            df["Date"],
            df["drawdown"]
        )

        plt.title("Rolling Min-Variance Backtest: Drawdown", fontsize=16)
        plt.xlabel("Date")
        plt.ylabel("Drawdown")
        plt.grid(True)

        output_file = (
            self.output_path /
            "rolling_min_variance_drawdown.png"
        )

        plt.savefig(
            output_file,
            dpi=300,
            bbox_inches="tight"
        )

        print(f"Saved drawdown figure: {output_file}")

        plt.show()

    def plot_rolling_sharpe(self, df):

        plt.figure(figsize=(12, 6))

        plt.plot(
            df["Date"],
            df["rolling_sharpe"]
        )

        plt.title("Rolling Min-Variance Backtest: Rolling Sharpe", fontsize=16)
        plt.xlabel("Date")
        plt.ylabel("Rolling Sharpe")
        plt.grid(True)

        output_file = (
            self.output_path /
            "rolling_min_variance_rolling_sharpe.png"
        )

        plt.savefig(
            output_file,
            dpi=300,
            bbox_inches="tight"
        )

        print(f"Saved rolling Sharpe figure: {output_file}")

        plt.show()

    def run(self):

        df = self.load_backtest()

        self.plot_cumulative_return(df)

        self.plot_drawdown(df)

        self.plot_rolling_sharpe(df)


if __name__ == "__main__":

    visualizer = RollingBacktestVisualizer()

    visualizer.run()
