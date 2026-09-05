import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


class CorrelationAnalysis:

    def __init__(self):

        self.matrix_path = Path("data/market_matrix")
        self.output_path = Path("results/figures")

    def load_returns(self):

        df = pd.read_csv(
            self.matrix_path / "market_return_matrix.csv"
        )

        asset_cols = [
            col for col in df.columns
            if col != "Date"
        ]

        return df[asset_cols]

    def compute_correlation_matrix(self, returns):

        return returns.corr()

    def save_correlation_matrix(self, corr_matrix):

        output_file = (
            self.output_path /
            "correlation_matrix.csv"
        )

        self.output_path.mkdir(
            parents=True,
            exist_ok=True
        )

        corr_matrix.to_csv(output_file)

        print("\nCORRELATION MATRIX")
        print(corr_matrix.round(4))

        print(f"\nSaved matrix: {output_file}")

    def plot_heatmap(self, corr_matrix):

        plt.figure(figsize=(10, 8))

        plt.imshow(
            corr_matrix,
            interpolation="nearest",
            aspect="auto"
        )

        plt.colorbar(label="Correlation")

        plt.xticks(
            range(len(corr_matrix.columns)),
            corr_matrix.columns,
            rotation=45
        )

        plt.yticks(
            range(len(corr_matrix.columns)),
            corr_matrix.columns
        )

        plt.title(
            "Asset Correlation Matrix",
            fontsize=16
        )

        output_file = (
            self.output_path /
            "correlation_heatmap.png"
        )

        plt.savefig(
            output_file,
            dpi=300,
            bbox_inches="tight"
        )

        print(f"\nSaved figure: {output_file}")

        plt.show()

    def run(self):

        returns = self.load_returns()

        corr_matrix = self.compute_correlation_matrix(
            returns
        )

        self.save_correlation_matrix(corr_matrix)

        self.plot_heatmap(corr_matrix)


if __name__ == "__main__":

    analysis = CorrelationAnalysis()

    analysis.run()
