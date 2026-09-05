import pandas as pd
import numpy as np
from pathlib import Path
from scipy.optimize import minimize


class RegimeAwareOptimizer:

    def __init__(self):

        self.matrix_path = Path("data/market_matrix")
        self.regime_path = Path("data/regimes")
        self.output_path = Path("data/optimization")

    def load_data(self):

        returns = pd.read_csv(
            self.matrix_path / "market_return_matrix.csv"
        )

        regimes = pd.read_csv(
            self.regime_path / "market_regimes.csv"
        )

        returns["Date"] = pd.to_datetime(returns["Date"])
        regimes["Date"] = pd.to_datetime(regimes["Date"])

        merged = returns.merge(
            regimes[["Date", "regime"]],
            on="Date",
            how="inner"
        )

        return merged

    def optimize_min_variance(self, regime_returns):

        asset_cols = [
            col for col in regime_returns.columns
            if col not in ["Date", "regime"]
        ]

        R = regime_returns[asset_cols].dropna()

        cov_matrix = R.cov().values
        mean_returns = R.mean().values

        n_assets = len(asset_cols)

        def portfolio_variance(weights):

            return weights.T @ cov_matrix @ weights

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

        portfolio_return = result.x @ mean_returns
        portfolio_variance_value = result.x.T @ cov_matrix @ result.x
        portfolio_volatility = np.sqrt(portfolio_variance_value)

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
            "expected_return": portfolio_return,
            "portfolio_variance": portfolio_variance_value,
            "portfolio_volatility": portfolio_volatility,
            "sharpe_ratio": sharpe_ratio
        }

        return weights, metrics

    def run_regime_optimization(self, merged):

        regimes = sorted(merged["regime"].unique())

        all_weights = []
        all_metrics = []

        for regime in regimes:

            regime_returns = merged[
                merged["regime"] == regime
            ]

            if len(regime_returns) < 10:
                continue

            weights, metrics = self.optimize_min_variance(
                regime_returns
            )

            weights["regime"] = regime

            metric_record = {
                "regime": regime,
                "n_observations": len(regime_returns)
            }

            metric_record.update(metrics)

            all_weights.append(weights)
            all_metrics.append(metric_record)

        weights_df = pd.concat(
            all_weights,
            ignore_index=True
        )

        metrics_df = pd.DataFrame(all_metrics)

        return weights_df, metrics_df

    def save_outputs(self, weights_df, metrics_df):

        self.output_path.mkdir(
            parents=True,
            exist_ok=True
        )

        weights_file = (
            self.output_path /
            "regime_aware_weights.csv"
        )

        metrics_file = (
            self.output_path /
            "regime_aware_metrics.csv"
        )

        weights_df.to_csv(weights_file, index=False)
        metrics_df.to_csv(metrics_file, index=False)

        print("\nREGIME-AWARE OPTIMIZATION")
        print("=" * 60)

        print("\nMetrics by Regime:")
        print(metrics_df.to_string(index=False))

        print("\nWeights by Regime:")
        print(
            weights_df.sort_values(
                ["regime", "weight"],
                ascending=[True, False]
            ).to_string(index=False)
        )

        print(f"\nSaved weights: {weights_file}")
        print(f"Saved metrics: {metrics_file}")

    def run_pipeline(self):

        print("=" * 60)
        print("REGIME-AWARE OPTIMIZATION ENGINE")
        print("=" * 60)

        merged = self.load_data()

        weights_df, metrics_df = self.run_regime_optimization(
            merged
        )

        self.save_outputs(
            weights_df,
            metrics_df
        )


if __name__ == "__main__":

    optimizer = RegimeAwareOptimizer()

    optimizer.run_pipeline()
