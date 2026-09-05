import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


class RegimeTransitionVisualizer:

    def __init__(self):

        self.input_path = Path("data/regimes")
        self.output_path = Path("results/figures")

    def load_transition_matrix(self):

        return pd.read_csv(
            self.input_path / "regime_transition_matrix.csv",
            index_col=0
        )

    def plot_transition_matrix(self, matrix):

        plt.figure(figsize=(8, 6))

        plt.imshow(
            matrix,
            aspect="auto"
        )

        plt.colorbar(label="Transition Probability")

        plt.xticks(
            range(len(matrix.columns)),
            matrix.columns,
            rotation=30
        )

        plt.yticks(
            range(len(matrix.index)),
            matrix.index
        )

        plt.title("Market Regime Transition Matrix", fontsize=16)

        self.output_path.mkdir(parents=True, exist_ok=True)

        output_file = self.output_path / "regime_transition_matrix.png"

        plt.savefig(output_file, dpi=300, bbox_inches="tight")

        print(f"Saved transition matrix figure: {output_file}")

        plt.show()

    def run(self):

        matrix = self.load_transition_matrix()

        self.plot_transition_matrix(matrix)


if __name__ == "__main__":

    visualizer = RegimeTransitionVisualizer()

    visualizer.run()
