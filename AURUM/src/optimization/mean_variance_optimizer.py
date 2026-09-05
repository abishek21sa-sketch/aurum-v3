import pandas as pd
import numpy as np
from pathlib import Path
from scipy.optimize import minimize


class MeanVarianceOptimizer:

    def __init__(self):

        self.matrix_path = Path("data/market_matrix")
        self.output_path = Path("data/optimization")

    def load_return_matrix(self):

        df = pd.read_csv(
            self.matrix_path / "market_return_matrix.csv"
        )

        asset_cols = [
            col for col in df.columns
            if col != "Date"
        ]

        return df[asset_cols].dropna()

    def optimize_mean_variance(self, returns, risk_aversion=5.0):

        asset_cols = list(returns.columns)

        mean_returns = returns.mean().values
        cov_matrix = returns.cov().values

        n_assets = len(asset_cols)

        def objective(weights):

            portfolio_return = weights @ mean_returns
            portfolio_variance = weights.T @ cov_matrix @ weights

            return -portfolio_return + risk_aversion * portfolio_variance

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
            objective,
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

        portfolio_return = result.x @ mean_returns
        portfolio_variance = result.x.T @ cov_matrix @ result.x
        portfolio_volatility = np.sqrt(portfolio_variance)

        sharpe_ratio = (
            portfolio_return / portfolio_volatility
            if portfolio_volatility > 0
            else 0
        )

        weights = pd.DataFrame(
            {
                "asset": asset_cols,
                "weight": result.x
            }
        )

        metrics = {
            "portfolio_variance": portfolio_variance,
            "portfolio_volatility": portfolio_volatility,
            "expected_return": portfolio_return,
            "sharpe_ratio": sharpe_ratio,
            "risk_aversion": risk_aversion,
            "objective_value": result.fun
        }

        return weights, metrics

    def save_outputs(self, weights, metrics):

        self.output_path.mkdir(
            parents=True,
            exist_ok=True
        )

        weights.to_csv(
            self.output_path / "mean_variance_weights.csv",
            index=False
        )

        summary = pd.DataFrame(
            {
                "metric": list(metrics.keys()),
                "value": list(metrics.values())
            }
        )

        summary.to_csv(
            self.output_path / "mean_variance_summary.csv",
            index=False
        )

        print("\nMEAN-VARIANCE PORTFOLIO")
        print("=" * 60)

        print("\nWeights:")
        print(
            weights.sort_values(
                "weight",
                ascending=False
            ).to_string(index=False)
        )

        print("\nMEAN-VARIANCE METRICS")
        for metric, value in metrics.items():
            print(f"{metric}: {value}")

    def run_pipeline(self):

        print("=" * 60)
        print("MEAN-VARIANCE OPTIMIZATION ENGINE")
        print("=" * 60)

        returns = self.load_return_matrix()

        weights, metrics = self.optimize_mean_variance(
            returns,
            risk_aversion=5.0
        )

        self.save_outputs(weights, metrics)


if __name__ == "__main__":

    optimizer = MeanVarianceOptimizer()

    optimizer.run_pipeline()
