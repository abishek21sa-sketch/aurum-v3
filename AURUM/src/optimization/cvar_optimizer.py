import pandas as pd
import numpy as np
from pathlib import Path
from scipy.optimize import minimize


class CVaROptimizer:

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

    def compute_cvar(self, portfolio_returns, alpha=0.95):

        losses = -portfolio_returns

        var_threshold = np.quantile(
            losses,
            alpha
        )

        tail_losses = losses[
            losses >= var_threshold
        ]

        cvar = tail_losses.mean()

        return cvar, var_threshold

    def optimize_cvar(self, returns, alpha=0.95):

        asset_cols = list(returns.columns)

        returns_matrix = returns.values

        n_assets = len(asset_cols)

        def cvar_objective(weights):

            portfolio_returns = returns_matrix @ weights

            cvar, _ = self.compute_cvar(
                portfolio_returns,
                alpha=alpha
            )

            return cvar

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
            cvar_objective,
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

        portfolio_returns = returns_matrix @ result.x

        cvar, var_threshold = self.compute_cvar(
            portfolio_returns,
            alpha=alpha
        )

        expected_return = portfolio_returns.mean()
        volatility = portfolio_returns.std()
        variance = volatility ** 2

        sharpe_ratio = (
            expected_return / volatility
            if volatility > 0
            else 0
        )

        weights = pd.DataFrame(
            {
                "asset": asset_cols,
                "weight": result.x
            }
        )

        metrics = {
            "expected_return": expected_return,
            "volatility": volatility,
            "variance": variance,
            "var_95": var_threshold,
            "cvar_95": cvar,
            "sharpe_ratio": sharpe_ratio,
            "alpha": alpha,
            "objective_value": result.fun
        }

        return weights, metrics

    def save_outputs(self, weights, metrics):

        self.output_path.mkdir(
            parents=True,
            exist_ok=True
        )

        weights_file = (
            self.output_path /
            "cvar_weights.csv"
        )

        summary_file = (
            self.output_path /
            "cvar_summary.csv"
        )

        weights.to_csv(
            weights_file,
            index=False
        )

        summary = pd.DataFrame(
            {
                "metric": list(metrics.keys()),
                "value": list(metrics.values())
            }
        )

        summary.to_csv(
            summary_file,
            index=False
        )

        print("\nCVaR OPTIMIZED PORTFOLIO")
        print("=" * 60)

        print("\nWeights:")
        print(
            weights.sort_values(
                "weight",
                ascending=False
            ).to_string(index=False)
        )

        print("\nCVaR METRICS")
        for metric, value in metrics.items():
            print(f"{metric}: {value}")

        print(f"\nSaved weights: {weights_file}")
        print(f"Saved summary: {summary_file}")

    def run_pipeline(self):

        print("=" * 60)
        print("CVaR OPTIMIZATION ENGINE")
        print("=" * 60)

        returns = self.load_return_matrix()

        weights, metrics = self.optimize_cvar(
            returns,
            alpha=0.95
        )

        self.save_outputs(
            weights,
            metrics
        )


if __name__ == "__main__":

    optimizer = CVaROptimizer()

    optimizer.run_pipeline()
