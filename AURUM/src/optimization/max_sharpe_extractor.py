import pandas as pd
from pathlib import Path


class MaxSharpeExtractor:

    def __init__(self):

        self.optimization_path = Path("data/optimization")
        self.output_path = Path("data/optimization")

    def load_frontier_outputs(self):

        frontier = pd.read_csv(
            self.optimization_path / "efficient_frontier.csv"
        )

        weights = pd.read_csv(
            self.optimization_path / "efficient_frontier_weights.csv"
        )

        return frontier, weights

    def extract_max_sharpe(self, frontier, weights):

        max_sharpe_row = frontier.loc[
            frontier["sharpe_ratio"].idxmax()
        ]

        target_return = max_sharpe_row["target_return"]

        weight_row = weights.loc[
            weights["target_return"] == target_return
        ].iloc[0]

        max_sharpe_weights = weight_row.drop(
            labels=["target_return"]
        ).reset_index()

        max_sharpe_weights.columns = [
            "asset",
            "weight"
        ]

        summary = pd.DataFrame(
            {
                "metric": max_sharpe_row.index,
                "value": max_sharpe_row.values
            }
        )

        return max_sharpe_weights, summary

    def save_outputs(self, max_sharpe_weights, summary):

        weights_file = (
            self.output_path /
            "max_sharpe_weights.csv"
        )

        summary_file = (
            self.output_path /
            "max_sharpe_summary.csv"
        )

        max_sharpe_weights.to_csv(
            weights_file,
            index=False
        )

        summary.to_csv(
            summary_file,
            index=False
        )

        print("\nMAX SHARPE PORTFOLIO")
        print("=" * 60)

        print("\nWeights:")
        print(
            max_sharpe_weights.sort_values(
                "weight",
                ascending=False
            ).to_string(index=False)
        )

        print("\nSummary:")
        print(summary.to_string(index=False))

        print(f"\nSaved weights: {weights_file}")
        print(f"Saved summary: {summary_file}")

    def run(self):

        frontier, weights = self.load_frontier_outputs()

        max_sharpe_weights, summary = self.extract_max_sharpe(
            frontier,
            weights
        )

        self.save_outputs(max_sharpe_weights, summary)


if __name__ == "__main__":

    extractor = MaxSharpeExtractor()

    extractor.run()
