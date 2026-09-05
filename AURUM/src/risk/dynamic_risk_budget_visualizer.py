import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


class DynamicRiskBudgetVisualizer:

    def __init__(self):

        self.input_path = Path("data/risk")
        self.output_path = Path("results/figures")

    def load_budget(self):

        return pd.read_csv(
            self.input_path / "dynamic_risk_budget.csv"
        )

    def plot_scaled_weights(self, budget):

        budget = budget.sort_values(
            "scaled_weight",
            ascending=False
        )

        plt.figure(figsize=(10, 6))

        plt.bar(
            budget["asset"],
            budget["scaled_weight"]
        )

        plt.title("Dynamic Risk Budget Allocation", fontsize=16)
        plt.xlabel("Asset")
        plt.ylabel("Scaled Portfolio Weight")
        plt.xticks(rotation=45)
        plt.grid(axis="y")

        self.output_path.mkdir(parents=True, exist_ok=True)

        output_file = self.output_path / "dynamic_risk_budget_allocation.png"

        plt.savefig(output_file, dpi=300, bbox_inches="tight")

        print(f"Saved risk budget allocation figure: {output_file}")

        plt.show()

    def run(self):

        budget = self.load_budget()

        self.plot_scaled_weights(budget)


if __name__ == "__main__":

    visualizer = DynamicRiskBudgetVisualizer()

    visualizer.run()
