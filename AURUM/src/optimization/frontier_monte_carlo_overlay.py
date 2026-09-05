import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


class FrontierMonteCarloOverlay:

    def __init__(self):

        self.optimization_path = Path("data/optimization")
        self.figure_path = Path("results/figures")

    def load_data(self):

        frontier = pd.read_csv(
            self.optimization_path / "efficient_frontier.csv"
        )

        monte_carlo = pd.read_csv(
            self.optimization_path / "monte_carlo_portfolios.csv"
        )

        return frontier, monte_carlo

    def plot_overlay(self, frontier, monte_carlo):

        self.figure_path.mkdir(
            parents=True,
            exist_ok=True
        )

        plt.figure(figsize=(12, 7))

        scatter = plt.scatter(
            monte_carlo["volatility"],
            monte_carlo["expected_return"],
            c=monte_carlo["sharpe_ratio"],
            s=8,
            alpha=0.4
        )

        plt.colorbar(scatter, label="Sharpe Ratio")

        plt.plot(
            frontier["volatility"],
            frontier["expected_return"],
            linewidth=3,
            marker="o"
        )

        max_sharpe = frontier.loc[
            frontier["sharpe_ratio"].idxmax()
        ]

        plt.scatter(
            max_sharpe["volatility"],
            max_sharpe["expected_return"],
            s=200
        )

        plt.annotate(
            "Max Sharpe",
            (
                max_sharpe["volatility"],
                max_sharpe["expected_return"]
            ),
            textcoords="offset points",
            xytext=(10, 10)
        )

        min_vol = frontier.loc[
            frontier["volatility"].idxmin()
        ]

        plt.scatter(
            min_vol["volatility"],
            min_vol["expected_return"],
            s=200
        )

        plt.annotate(
            "Min Volatility",
            (
                min_vol["volatility"],
                min_vol["expected_return"]
            ),
            textcoords="offset points",
            xytext=(10, -15)
        )

        plt.title(
            "Efficient Frontier vs Monte Carlo Portfolios",
            fontsize=16
        )

        plt.xlabel("Portfolio Volatility")
        plt.ylabel("Expected Return")

        plt.grid(True)

        output_file = (
            self.figure_path /
            "frontier_monte_carlo_overlay.png"
        )

        plt.savefig(
            output_file,
            dpi=300,
            bbox_inches="tight"
        )

        print(f"Saved figure: {output_file}")

        plt.show()

    def run(self):

        frontier, monte_carlo = self.load_data()

        self.plot_overlay(
            frontier,
            monte_carlo
        )


if __name__ == "__main__":

    overlay = FrontierMonteCarloOverlay()

    overlay.run()
