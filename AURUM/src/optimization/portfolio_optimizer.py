import pandas as pd
import numpy as np
from pathlib import Path
from scipy.optimize import minimize


class PortfolioOptimizer:

    def __init__(self):

        self.matrix_path = Path("data/market_matrix")
        self.output_path = Path("data/optimization")

    def load_return_matrix(self):

        df = pd.read_csv(
            self.matrix_path / "market_return_matrix.csv"
        )

        df["Date"] = pd.to_datetime(df["Date"])

        return df

    def optimize_min_variance(self, returns):

        asset_cols = [
            col for col in returns.columns
            if col != "Date"
        ]

        R = returns[asset_cols].dropna()

        cov_matrix = R.cov().values
        mean_returns = R.mean().values

        n_assets = len(asset_cols)

        def portfolio_variance(weights):

            return weights.T @ cov_matrix @ weights

        def portfolio_return(weights):

            return weights @ mean_returns

        constraints = (
            {
                "type": "eq",
                "fun": lambda weights: np.sum(weights) - 1
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

        if not result.success:
            raise RuntimeError(result.message)

        optimal_return = portfolio_return(result.x)

        optimal_volatility = np.sqrt(result.fun)

        sharpe_ratio = (
            optimal_return / optimal_volatility
            if optimal_volatility > 0
            else 0
        )

        weights = pd.DataFrame(
            {
                "asset": asset_cols,
                "weight": result.x
            }
        )

        metrics = {
            "portfolio_variance": result.fun,
            "portfolio_volatility": optimal_volatility,
            "expected_return": optimal_return,
            "sharpe_ratio": sharpe_ratio
        }

        return weights, metrics

    def save_outputs(self, weights, metrics):

        self.output_path.mkdir(
            parents=True,
            exist_ok=True
        )

        weights.to_csv(
            self.output_path / "min_variance_weights.csv",
            index=False
        )

        summary = pd.DataFrame(
            {
                "metric": list(metrics.keys()),
                "value": list(metrics.values())
            }
        )

        summary.to_csv(
            self.output_path / "optimization_summary.csv",
            index=False
        )

        print("\nOPTIMAL MIN-VARIANCE WEIGHTS")
        print(weights)

        print("\nOPTIMIZATION METRICS")

        for metric, value in metrics.items():

            print(f"{metric}: {value}")

    def run_pipeline(self):

        print("=" * 60)
        print("PORTFOLIO OPTIMIZATION ENGINE")
        print("=" * 60)

        returns = self.load_return_matrix()

        weights, metrics = self.optimize_min_variance(
            returns
        )

        self.save_outputs(weights, metrics)


if __name__ == "__main__":

    optimizer = PortfolioOptimizer()

    optimizer.run_pipeline()
