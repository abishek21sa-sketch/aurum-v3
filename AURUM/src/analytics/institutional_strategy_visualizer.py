from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


class InstitutionalStrategyVisualizer:
    def __init__(
        self,
        comparison_path="data/analytics/allocation_strategy_comparison.csv",
        meta_weights_path="data/optimization/meta_strategy_weights.csv",
        output_dir="results/figures",
    ):
        self.comparison_path = Path(comparison_path)
        self.meta_weights_path = Path(meta_weights_path)
        self.output_dir = Path(output_dir)

    def load_data(self):
        comparison = pd.read_csv(self.comparison_path)
        meta_weights = pd.read_csv(self.meta_weights_path)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        return comparison, meta_weights

    def plot_strategy_sharpe(self, comparison):
        df = comparison.sort_values("sharpe_like", ascending=True)

        plt.figure(figsize=(10, 6))
        plt.barh(df["strategy"], df["sharpe_like"])
        plt.xlabel("Sharpe-like Ratio")
        plt.title("Strategy Risk-Adjusted Performance")
        plt.tight_layout()

        path = self.output_dir / "strategy_sharpe_comparison.png"
        plt.savefig(path, dpi=300)
        plt.close()

        return path

    def plot_return_vs_drawdown(self, comparison):
        plt.figure(figsize=(9, 6))
        plt.scatter(
            comparison["max_drawdown"].abs(),
            comparison["net_total_return"],
            s=100,
        )

        for _, row in comparison.iterrows():
            plt.annotate(
                row["strategy"],
                (
                    abs(row["max_drawdown"]),
                    row["net_total_return"],
                ),
                fontsize=9,
                xytext=(5, 5),
                textcoords="offset points",
            )

        plt.xlabel("Absolute Max Drawdown")
        plt.ylabel("Net Total Return")
        plt.title("Return vs Drawdown by Strategy")
        plt.tight_layout()

        path = self.output_dir / "strategy_return_vs_drawdown.png"
        plt.savefig(path, dpi=300)
        plt.close()

        return path

    def plot_meta_weights(self, meta_weights):
        df = meta_weights.sort_values("meta_weight", ascending=True)

        plt.figure(figsize=(10, 6))
        plt.barh(df["strategy"], df["meta_weight"])
        plt.xlabel("Meta Strategy Weight")
        plt.title("Meta Strategy Allocation")
        plt.tight_layout()

        path = self.output_dir / "meta_strategy_allocation.png"
        plt.savefig(path, dpi=300)
        plt.close()

        return path

    def run(self):
        comparison, meta_weights = self.load_data()

        paths = [
            self.plot_strategy_sharpe(comparison),
            self.plot_return_vs_drawdown(comparison),
            self.plot_meta_weights(meta_weights),
        ]

        print("INSTITUTIONAL STRATEGY VISUALIZATIONS COMPLETE")
        print("=" * 70)

        for path in paths:
            print(f"Saved figure: {path}")

        return paths


if __name__ == "__main__":
    visualizer = InstitutionalStrategyVisualizer()
    visualizer.run()