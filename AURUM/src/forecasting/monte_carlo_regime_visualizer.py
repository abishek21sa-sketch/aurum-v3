import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


class MonteCarloRegimeVisualizer:

    def __init__(self):
        self.input_path = Path("data/forecasting")
        self.output_path = Path("results/figures")

    def load_paths(self):
        return pd.read_csv(
            self.input_path / "monte_carlo_regime_paths.csv"
        )

    def plot_sample_paths(self, paths, n_paths=50):
        plt.figure(figsize=(12, 6))

        sample_ids = paths["path_id"].drop_duplicates().head(n_paths)

        for path_id in sample_ids:
            path = paths[paths["path_id"] == path_id]
            plt.plot(
                path["day"],
                path["cumulative_return"],
                alpha=0.3
            )

        plt.title("Monte Carlo Regime Simulation Paths", fontsize=16)
        plt.xlabel("Day")
        plt.ylabel("Cumulative Return")
        plt.grid(True)

        self.output_path.mkdir(parents=True, exist_ok=True)

        output_file = self.output_path / "monte_carlo_regime_paths.png"

        plt.savefig(output_file, dpi=300, bbox_inches="tight")
        print(f"Saved Monte Carlo paths figure: {output_file}")

        plt.show()

    def plot_terminal_distribution(self, paths):
        terminal = paths.groupby("path_id").tail(1)

        plt.figure(figsize=(10, 6))

        plt.hist(
            terminal["cumulative_return"],
            bins=40
        )

        plt.title("60-Day Terminal Return Distribution", fontsize=16)
        plt.xlabel("Terminal Cumulative Return")
        plt.ylabel("Frequency")
        plt.grid(axis="y")

        output_file = self.output_path / "monte_carlo_terminal_distribution.png"

        plt.savefig(output_file, dpi=300, bbox_inches="tight")
        print(f"Saved terminal distribution figure: {output_file}")

        plt.show()

    def run(self):
        paths = self.load_paths()

        self.plot_sample_paths(paths)
        self.plot_terminal_distribution(paths)


if __name__ == "__main__":
    visualizer = MonteCarloRegimeVisualizer()
    visualizer.run()
