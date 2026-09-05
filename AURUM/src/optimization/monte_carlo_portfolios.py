import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


class MonteCarloPortfolios:

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

    def simulate_portfolios(self, returns, n_simulations=10000):

        asset_cols = list(returns.columns)

        mean_returns = returns.mean().values
        cov_matrix = returns.cov().values

        records = []
        weights_records = []

        for i in range(n_simulations):

            weights = np.random.random(len(asset_cols))
            weights = weights / np.sum(weights)

            expected_return = weights @ mean_returns
            variance = weights.T @ cov_matrix @ weights
            volatility = np.sqrt(variance)

            sharpe_ratio = (
                expected_return / volatility
                if volatility > 0
                else 0
            )

            records.append(
                {
                    "simulation_id": i,
                    "expected_return": expected_return,
                    "volatility": volatility,
                    "variance": variance,
                    "sharpe_ratio": sharpe_ratio
                }
            )

            weight_record = {
                "simulation_id": i
            }

            for asset, weight in zip(asset_cols, weights):
                weight_record[asset] = weight

            weights_records.append(weight_record)

        simulations_df = pd.DataFrame(records)
        weights_df = pd.DataFrame(weights_records)

        return simulations_df, weights_df

    def save_outputs(self, simulations_df, weights_df):

        self.output_path.mkdir(
            parents=True,
            exist_ok=True
        )

        simulations_file = (
            self.output_path /
            "monte_carlo_portfolios.csv"
        )

        weights_file = (
            self.output_path /
            "monte_carlo_portfolio_weights.csv"
        )

        simulations_df.to_csv(simulations_file, index=False)
        weights_df.to_csv(weights_file, index=False)

        print("\nMONTE CARLO PORTFOLIO SIMULATION")
        print("=" * 60)

        print("\nSimulation Preview:")
        print(simulations_df.head().to_string(index=False))

        print("\nBest Sharpe Portfolio:")
        print(
            simulations_df.loc[
                simulations_df["sharpe_ratio"].idxmax()
            ].to_string()
        )

        print(f"\nSaved simulations: {simulations_file}")
        print(f"Saved weights: {weights_file}")

    def plot_simulations(self, simulations_df):

        self.figure_path.mkdir(
            parents=True,
            exist_ok=True
        )

        plt.figure(figsize=(10, 6))

        scatter = plt.scatter(
            simulations_df["volatility"],
            simulations_df["expected_return"],
            c=simulations_df["sharpe_ratio"],
            s=10,
            alpha=0.6
        )

        plt.colorbar(scatter, label="Sharpe Ratio")

        plt.title("Monte Carlo Portfolio Simulation", fontsize=16)
        plt.xlabel("Portfolio Volatility")
        plt.ylabel("Expected Return")
        plt.grid(True)

        output_file = (
            self.figure_path /
            "monte_carlo_portfolios.png"
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
        print("MONTE CARLO PORTFOLIO SIMULATION ENGINE")
        print("=" * 60)

        returns = self.load_return_matrix()

        simulations_df, weights_df = self.simulate_portfolios(
            returns,
            n_simulations=10000
        )

        self.save_outputs(simulations_df, weights_df)

        self.plot_simulations(simulations_df)


if __name__ == "__main__":

    simulator = MonteCarloPortfolios()

    simulator.run_pipeline()
