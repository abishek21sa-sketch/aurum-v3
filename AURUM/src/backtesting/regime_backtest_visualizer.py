import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


class RegimeBacktestVisualizer:

    def __init__(self):

        self.input_path = Path("data/backtesting")
        self.output_path = Path("results/figures")

    def load_backtest(self):

        df = pd.read_csv(
            self.input_path / "regime_aware_backtest.csv"
        )

        df["Date"] = pd.to_datetime(df["Date"])

        return df

    def plot_cumulative_return(self, df):

        plt.figure(figsize=(12, 6))

        plt.plot(
            df["Date"],
            df["cumulative_return"]
        )

        plt.title("Regime-Aware Backtest: Cumulative Return", fontsize=16)
        plt.xlabel("Date")
        plt.ylabel("Cumulative Return")
        plt.grid(True)

        self.output_path.mkdir(parents=True, exist_ok=True)

        output_file = self.output_path / "regime_aware_cumulative_return.png"

        plt.savefig(output_file, dpi=300, bbox_inches="tight")

        print(f"Saved cumulative return figure: {output_file}")

        plt.show()

    def plot_drawdown(self, df):

        plt.figure(figsize=(12, 6))

        plt.plot(
            df["Date"],
            df["drawdown"]
        )

        plt.title("Regime-Aware Backtest: Drawdown", fontsize=16)
        plt.xlabel("Date")
        plt.ylabel("Drawdown")
        plt.grid(True)

        output_file = self.output_path / "regime_aware_drawdown.png"

        plt.savefig(output_file, dpi=300, bbox_inches="tight")

        print(f"Saved drawdown figure: {output_file}")

        plt.show()

    def plot_returns_by_regime(self, df):

        regime_returns = (
            df.groupby("regime")["portfolio_return"]
            .mean()
            .sort_values(ascending=False)
        )

        plt.figure(figsize=(10, 6))

        plt.bar(
            regime_returns.index,
            regime_returns.values
        )

        plt.title("Average Portfolio Return by Regime", fontsize=16)
        plt.xlabel("Regime")
        plt.ylabel("Average Daily Portfolio Return")
        plt.xticks(rotation=30)
        plt.grid(axis="y")

        output_file = self.output_path / "regime_aware_returns_by_regime.png"

        plt.savefig(output_file, dpi=300, bbox_inches="tight")

        print(f"Saved regime return figure: {output_file}")

        plt.show()

    def run(self):

        df = self.load_backtest()

        self.plot_cumulative_return(df)
        self.plot_drawdown(df)
        self.plot_returns_by_regime(df)


if __name__ == "__main__":

    visualizer = RegimeBacktestVisualizer()

    visualizer.run()
