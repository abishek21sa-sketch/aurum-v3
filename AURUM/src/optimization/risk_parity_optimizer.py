import pandas as pd
import numpy as np
from pathlib import Path
from scipy.optimize import minimize


class RiskParityOptimizer:

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

    def compute_risk_contributions(self, weights, cov_matrix):

        portfolio_variance = weights.T @ cov_matrix @ weights

        marginal_risk = cov_matrix @ weights

        total_risk_contribution = weights * marginal_risk

        percent_risk_contribution = (
            total_risk_contribution / portfolio_variance
        )

        return percent_risk_contribution

    def optimize_risk_parity(self, returns):

        asset_cols = list(returns.columns)

        cov_matrix = returns.cov().values

        n_assets = len(asset_cols)

        target_risk = np.ones(n_assets) / n_assets

        def risk_parity_objective(weights):

            risk_contribution = self.compute_risk_contributions(
                weights,
                cov_matrix
            )

            return np.sum(
                (risk_contribution - target_risk) ** 2
            )

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
            risk_parity_objective,
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

        final_risk_contribution = self.compute_risk_contributions(
            result.x,
            cov_matrix
        )

        weights = pd.DataFrame(
            {
                "asset": asset_cols,
                "weight": result.x,
                "risk_contribution": final_risk_contribution
            }
        )

        portfolio_variance = result.x.T @ cov_matrix @ result.x
        portfolio_volatility = np.sqrt(portfolio_variance)
        expected_return = result.x @ returns.mean().values

        sharpe_ratio = (
            expected_return / portfolio_volatility
            if portfolio_volatility > 0
            else 0
        )

        metrics = {
            "portfolio_variance": portfolio_variance,
            "portfolio_volatility": portfolio_volatility,
            "expected_return": expected_return,
            "sharpe_ratio": sharpe_ratio,
            "risk_parity_objective": result.fun
        }

        return weights, metrics

    def save_outputs(self, weights, metrics):

        self.output_path.mkdir(
            parents=True,
            exist_ok=True
        )

        weights.to_csv(
            self.output_path / "risk_parity_weights.csv",
            index=False
        )

        summary = pd.DataFrame(
            {
                "metric": list(metrics.keys()),
                "value": list(metrics.values())
            }
        )

        summary.to_csv(
            self.output_path / "risk_parity_summary.csv",
            index=False
        )

        print("\nRISK PARITY PORTFOLIO")
        print("=" * 60)

        print("\nWeights and Risk Contributions:")
        print(weights.to_string(index=False))

        print("\nRISK PARITY METRICS")
        for metric, value in metrics.items():
            print(f"{metric}: {value}")

    def run_pipeline(self):

        print("=" * 60)
        print("RISK PARITY OPTIMIZATION ENGINE")
        print("=" * 60)

        returns = self.load_return_matrix()

        weights, metrics = self.optimize_risk_parity(
            returns
        )

        self.save_outputs(weights, metrics)


if __name__ == "__main__":

    optimizer = RiskParityOptimizer()

    optimizer.run_pipeline()
