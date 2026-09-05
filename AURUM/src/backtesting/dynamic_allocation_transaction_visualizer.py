import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


class DynamicAllocationTransactionVisualizer:

    def __init__(self):

        self.input_path = Path("data/backtesting")
        self.output_path = Path("results/figures")

    def load_backtests(self):

        gross = pd.read_csv(
            self.input_path / "dynamic_allocation_backtest.csv"
        )

        net = pd.read_csv(
            self.input_path / "dynamic_allocation_transaction_cost.csv"
        )

        gross["Date"] = pd.to_datetime(gross["Date"])
        net["Date"] = pd.to_datetime(net["Date"])

        return gross, net

    def plot_gross_vs_net(self, gross, net):

        plt.figure(figsize=(12, 6))

        plt.plot(
            gross["Date"],
            gross["cumulative_return"],
            label="Gross Dynamic Allocation"
        )

        plt.plot(
            net["Date"],
            net["net_cumulative_return"],
            label="Net Dynamic Allocation"
        )

        plt.title("Dynamic Allocation: Gross vs Net Return", fontsize=16)
        plt.xlabel("Date")
        plt.ylabel("Cumulative Return")
        plt.legend()
        plt.grid(True)

        self.output_path.mkdir(parents=True, exist_ok=True)

        output_file = self.output_path / "dynamic_allocation_gross_vs_net.png"

        plt.savefig(output_file, dpi=300, bbox_inches="tight")

        print(f"Saved gross vs net figure: {output_file}")

        plt.show()

    def plot_transaction_costs(self, net):

        plt.figure(figsize=(12, 6))

        plt.plot(
            net["Date"],
            net["transaction_cost"]
        )

        plt.title("Dynamic Allocation Transaction Costs", fontsize=16)
        plt.xlabel("Date")
        plt.ylabel("Transaction Cost")
        plt.grid(True)

        output_file = self.output_path / "dynamic_allocation_transaction_costs.png"

        plt.savefig(output_file, dpi=300, bbox_inches="tight")

        print(f"Saved transaction cost figure: {output_file}")

        plt.show()

    def plot_net_drawdown(self, net):

        plt.figure(figsize=(12, 6))

        plt.plot(
            net["Date"],
            net["net_drawdown"]
        )

        plt.title("Dynamic Allocation Net Drawdown", fontsize=16)
        plt.xlabel("Date")
        plt.ylabel("Net Drawdown")
        plt.grid(True)

        output_file = self.output_path / "dynamic_allocation_net_drawdown.png"

        plt.savefig(output_file, dpi=300, bbox_inches="tight")

        print(f"Saved net drawdown figure: {output_file}")

        plt.show()

    def run(self):

        gross, net = self.load_backtests()

        self.plot_gross_vs_net(gross, net)
        self.plot_transaction_costs(net)
        self.plot_net_drawdown(net)


if __name__ == "__main__":

    visualizer = DynamicAllocationTransactionVisualizer()

    visualizer.run()
