import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


class TransactionCostVisualizer:

    def __init__(self):

        self.input_path = Path("data/backtesting")
        self.output_path = Path("results/figures")

    def load_backtest(self):

        df = pd.read_csv(
            self.input_path / "transaction_cost_backtest.csv"
        )

        df["Date"] = pd.to_datetime(df["Date"])

        return df

    def plot_gross_vs_net(self, df):

        plt.figure(figsize=(12, 6))

        plt.plot(df["Date"], df["gross_cumulative_return"], label="Gross")
        plt.plot(df["Date"], df["net_cumulative_return"], label="Net")

        plt.title("Gross vs Net Cumulative Return", fontsize=16)
        plt.xlabel("Date")
        plt.ylabel("Cumulative Return")
        plt.legend()
        plt.grid(True)

        self.output_path.mkdir(parents=True, exist_ok=True)

        output_file = self.output_path / "gross_vs_net_cumulative_return.png"

        plt.savefig(output_file, dpi=300, bbox_inches="tight")

        print(f"Saved gross vs net figure: {output_file}")

        plt.show()

    def plot_turnover(self, df):

        turnover_df = df[df["turnover"] > 0]

        plt.figure(figsize=(12, 6))

        plt.bar(turnover_df["Date"], turnover_df["turnover"])

        plt.title("Portfolio Turnover at Rebalance Dates", fontsize=16)
        plt.xlabel("Date")
        plt.ylabel("Turnover")
        plt.grid(axis="y")

        output_file = self.output_path / "rebalance_turnover.png"

        plt.savefig(output_file, dpi=300, bbox_inches="tight")

        print(f"Saved turnover figure: {output_file}")

        plt.show()

    def plot_net_drawdown(self, df):

        plt.figure(figsize=(12, 6))

        plt.plot(df["Date"], df["net_drawdown"])

        plt.title("Net Portfolio Drawdown", fontsize=16)
        plt.xlabel("Date")
        plt.ylabel("Drawdown")
        plt.grid(True)

        output_file = self.output_path / "net_drawdown_transaction_cost.png"

        plt.savefig(output_file, dpi=300, bbox_inches="tight")

        print(f"Saved drawdown figure: {output_file}")

        plt.show()

    def run(self):

        df = self.load_backtest()

        self.plot_gross_vs_net(df)
        self.plot_turnover(df)
        self.plot_net_drawdown(df)


if __name__ == "__main__":

    visualizer = TransactionCostVisualizer()

    visualizer.run()
