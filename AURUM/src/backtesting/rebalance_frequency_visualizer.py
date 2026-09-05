import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


class RebalanceFrequencyVisualizer:

    def __init__(self):

        self.input_path = Path("data/backtesting")
        self.output_path = Path("results/figures")

    def load_results(self):

        return pd.read_csv(
            self.input_path / "rebalance_frequency_sensitivity.csv"
        )

    def plot_return_sensitivity(self, df):

        plt.figure(figsize=(10, 6))

        plt.plot(
            df["rebalance_frequency_days"],
            df["net_total_return"],
            marker="o"
        )

        plt.title("Net Return vs Rebalance Frequency", fontsize=16)
        plt.xlabel("Rebalance Frequency Days")
        plt.ylabel("Net Total Return")
        plt.grid(True)

        self.output_path.mkdir(parents=True, exist_ok=True)

        output_file = self.output_path / "rebalance_frequency_return.png"

        plt.savefig(output_file, dpi=300, bbox_inches="tight")

        print(f"Saved return sensitivity figure: {output_file}")

        plt.show()

    def plot_drawdown_sensitivity(self, df):

        plt.figure(figsize=(10, 6))

        plt.plot(
            df["rebalance_frequency_days"],
            df["max_net_drawdown"],
            marker="o"
        )

        plt.title("Max Drawdown vs Rebalance Frequency", fontsize=16)
        plt.xlabel("Rebalance Frequency Days")
        plt.ylabel("Max Net Drawdown")
        plt.grid(True)

        output_file = self.output_path / "rebalance_frequency_drawdown.png"

        plt.savefig(output_file, dpi=300, bbox_inches="tight")

        print(f"Saved drawdown sensitivity figure: {output_file}")

        plt.show()

    def plot_cost_sensitivity(self, df):

        plt.figure(figsize=(10, 6))

        plt.plot(
            df["rebalance_frequency_days"],
            df["total_transaction_cost"],
            marker="o"
        )

        plt.title("Transaction Cost vs Rebalance Frequency", fontsize=16)
        plt.xlabel("Rebalance Frequency Days")
        plt.ylabel("Total Transaction Cost")
        plt.grid(True)

        output_file = self.output_path / "rebalance_frequency_cost.png"

        plt.savefig(output_file, dpi=300, bbox_inches="tight")

        print(f"Saved cost sensitivity figure: {output_file}")

        plt.show()

    def run(self):

        df = self.load_results()

        self.plot_return_sensitivity(df)
        self.plot_drawdown_sensitivity(df)
        self.plot_cost_sensitivity(df)


if __name__ == "__main__":

    visualizer = RebalanceFrequencyVisualizer()

    visualizer.run()
