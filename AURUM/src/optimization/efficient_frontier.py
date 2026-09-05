import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.optimize import minimize


class EfficientFrontier:

    def __init__(self):

        self.matrix_path = Path("data/market_matrix")
        self.output_path = Path("data/optimization")
        self.figure_path = Path("results/figures")

    def load_return_matrix(self):

        df = pd.read_csv(
            self.matrix_path / "market_return_matrix.csv"
        )

        asset_cols = [
            col for col in df.columns
            if col != "Date"
        ]

        return df[asset_cols].dropna()

    def portfolio_metrics(self, weights, mean_returns, cov_matrix):

        portfolio_return = weights @ mean_returns
        portfolio_variance = weights.T @ cov_matrix @ weights
        portfolio_volatility = np.sqrt(portfolio_variance)

        return portfolio_return, portfolio_volatility

    def minimize_volatility_for_target_return(
        self,
        target_return,
        mean_returns,
        cov_matrix,
        n_assets
    ):

        def portfolio_variance(weights):

            return weights.T @ cov_matrix @ weights

        constraints = (
            {
                "type": "eq",
                "fun": lambda weights: np.sum(weights) - 1
            },
            {
                "type": "eq",
                "fun": lambda weights: weights @ mean_returns - target_return
            },
        )

        bounds = tuple(
            (0, 1) for _ in range(n_assets)
        )

        initial_weights = np.ones(n_assets) / n_assets

        result = minimize(
            portfolio_variance,
            initial_weights,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={
                "ftol": 1e-12,
                "maxiter": 1000,
                "disp": False
            }
        )

        return result

    def compute_frontier(self, returns, n_points=50):

        asset_cols = list(returns.columns)

        mean_returns = returns.mean().values
        cov_matrix = returns.cov().values

        n_assets = len(asset_cols)

        min_target = mean_returns.min()
        max_target = mean_returns.max()

        target_returns = np.linspace(
            min_target,
            max_target,
            n_points
        )

        frontier_records = []

        weights_records = []

        for target_return in target_returns:

            result = self.minimize_volatility_for_target_return(
                target_return,
                mean_returns,
                cov_matrix,
                n_assets
            )

            if result.success:

                portfolio_return, portfolio_volatility = self.portfolio_metrics(
                    result.x,
                    mean_returns,
                    cov_matrix
                )

                sharpe_ratio = (
                    portfolio_return / portfolio_volatility
                    if portfolio_volatility > 0
                    else 0
                )

                frontier_records.append(
                    {
                        "target_return": target_return,
                        "expected_return": portfolio_return,
                        "volatility": portfolio_volatility,
                        "variance": portfolio_volatility ** 2,
                        "sharpe_ratio": sharpe_ratio
                    }
                )

                weight_record = {
                    "target_return": target_return
                }

                for asset, weight in zip(asset_cols, result.x):
                    weight_record[asset] = weight

                weights_records.append(weight_record)

        frontier_df = pd.DataFrame(frontier_records)
        weights_df = pd.DataFrame(weights_records)

        return frontier_df, weights_df

    def save_outputs(self, frontier_df, weights_df):

        self.output_path.mkdir(
            parents=True,
            exist_ok=True
        )

        frontier_file = (
            self.output_path /
            "efficient_frontier.csv"
        )

        weights_file = (
            self.output_path /
            "efficient_frontier_weights.csv"
        )

        frontier_df.to_csv(frontier_file, index=False)
        weights_df.to_csv(weights_file, index=False)

        print("\nEFFICIENT FRONTIER")
        print("=" * 60)

        print(frontier_df.head().to_string(index=False))

        print(f"\nSaved frontier: {frontier_file}")
        print(f"Saved weights: {weights_file}")

    def plot_frontier(self, frontier_df):

        self.figure_path.mkdir(
            parents=True,
            exist_ok=True
        )

        plt.figure(figsize=(10, 6))

        plt.plot(
            frontier_df["volatility"],
            frontier_df["expected_return"],
            marker="o"
        )

        plt.title("Efficient Frontier", fontsize=16)
        plt.xlabel("Portfolio Volatility")
        plt.ylabel("Expected Return")
        plt.grid(True)

        output_file = (
            self.figure_path /
            "efficient_frontier.png"
        )

        plt.savefig(
            output_file,
            dpi=300,
            bbox_inches="tight"
        )

        print(f"Saved figure: {output_file}")

        plt.show()

    def run_pipeline(self):

        print("=" * 60)
        print("EFFICIENT FRONTIER ENGINE")
        print("=" * 60)

        returns = self.load_return_matrix()

        frontier_df, weights_df = self.compute_frontier(
            returns,
            n_points=50
        )

        self.save_outputs(frontier_df, weights_df)

        self.plot_frontier(frontier_df)


if __name__ == "__main__":

    frontier = EfficientFrontier()

    frontier.run_pipeline()
