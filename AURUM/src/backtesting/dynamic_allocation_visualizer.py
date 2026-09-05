import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


class DynamicAllocationVisualizer:

    def __init__(self):

        self.input_path = Path("data/backtesting")
        self.output_path = Path("results/figures")

    def load_backtests(self):

        dynamic = pd.read_csv(
            self.input_path / "dynamic_allocation_backtest.csv"
        )

        hard_regime = pd.read_csv(
            self.input_path / "regime_aware_backtest.csv"
        )

        dynamic["Date"] = pd.to_datetime(dynamic["Date"])
        hard_regime["Date"] = pd.to_datetime(hard_regime["Date"])

        return dynamic, hard_regime

    def plot_cumulative_returns(self, dynamic, hard_regime):

        plt.figure(figsize=(12, 6))

        plt.plot(
            dynamic["Date"],
            dynamic["cumulative_return"],
            label="Probabilistic Dynamic Allocation"
        )

        plt.plot(
            hard_regime["Date"],
            hard_regime["cumulative_return"],
            label="Hard Regime Switch"
        )

        plt.title("Dynamic Allocation vs Hard Regime Switch", fontsize=16)
        plt.xlabel("Date")
        plt.ylabel("Cumulative Return")
        plt.legend()
        plt.grid(True)

        self.output_path.mkdir(parents=True, exist_ok=True)

        output_file = self.output_path / "dynamic_vs_hard_regime_return.png"

        plt.savefig(output_file, dpi=300, bbox_inches="tight")

        print(f"Saved cumulative return figure: {output_file}")

        plt.show()

    def plot_dynamic_drawdown(self, dynamic):

        plt.figure(figsize=(12, 6))

        plt.plot(
            dynamic["Date"],
            dynamic["drawdown"]
        )

        plt.title("Dynamic Probabilistic Allocation Drawdown", fontsize=16)
        plt.xlabel("Date")
        plt.ylabel("Drawdown")
        plt.grid(True)

        output_file = self.output_path / "dynamic_allocation_drawdown.png"

        plt.savefig(output_file, dpi=300, bbox_inches="tight")

        print(f"Saved drawdown figure: {output_file}")

        plt.show()

    def plot_dynamic_rolling_sharpe(self, dynamic):

        plt.figure(figsize=(12, 6))

        plt.plot(
            dynamic["Date"],
            dynamic["rolling_sharpe"]
        )

        plt.title("Dynamic Probabilistic Allocation Rolling Sharpe", fontsize=16)
        plt.xlabel("Date")
        plt.ylabel("Rolling Sharpe")
        plt.grid(True)

        output_file = self.output_path / "dynamic_allocation_rolling_sharpe.png"

        plt.savefig(output_file, dpi=300, bbox_inches="tight")

        print(f"Saved rolling Sharpe figure: {output_file}")

        plt.show()

    def run(self):

        dynamic, hard_regime = self.load_backtests()

        self.plot_cumulative_returns(
            dynamic,
            hard_regime
        )

        self.plot_dynamic_drawdown(dynamic)

        self.plot_dynamic_rolling_sharpe(dynamic)


if __name__ == "__main__":

    visualizer = DynamicAllocationVisualizer()

    visualizer.run()
