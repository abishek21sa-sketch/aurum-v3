import pandas as pd
import numpy as np
from pathlib import Path


class RiskContributionAnalysis:

    def __init__(self):

        self.matrix_path = Path("data/market_matrix")
        self.optimization_path = Path("data/optimization")
        self.output_path = Path("results/reports")

    def load_data(self):

        returns = pd.read_csv(
            self.matrix_path / "market_return_matrix.csv"
        )

        weights = pd.read_csv(
            self.optimization_path / "min_variance_weights.csv"
        )

        asset_cols = [
            col for col in returns.columns
            if col != "Date"
        ]

        R = returns[asset_cols].dropna()

        return R, weights

    def compute_risk_contributions(self, returns, weights):

        cov_matrix = returns.cov()

        weight_vector = weights.set_index("asset").loc[
            cov_matrix.columns,
            "weight"
        ].values

        portfolio_variance = (
            weight_vector.T @ cov_matrix.values @ weight_vector
        )

        marginal_risk = cov_matrix.values @ weight_vector

        total_risk_contribution = weight_vector * marginal_risk

        percent_risk_contribution = (
            total_risk_contribution / portfolio_variance
        )

        risk_df = pd.DataFrame(
            {
                "asset": cov_matrix.columns,
                "weight": weight_vector,
                "marginal_risk": marginal_risk,
                "total_risk_contribution": total_risk_contribution,
                "percent_risk_contribution": percent_risk_contribution
            }
        )

        return risk_df, portfolio_variance

    def save_outputs(self, risk_df, portfolio_variance):

        self.output_path.mkdir(
            parents=True,
            exist_ok=True
        )

        output_file = (
            self.output_path /
            "risk_contribution_report.csv"
        )

        risk_df.to_csv(output_file, index=False)

        print("\nRISK CONTRIBUTION ANALYSIS")
        print("=" * 60)

        print(f"\nPortfolio Variance: {portfolio_variance:.10f}")

        print("\nRisk Contributions:")
        print(
            risk_df.sort_values(
                "percent_risk_contribution",
                ascending=False
            ).to_string(index=False)
        )

        print(f"\nSaved report: {output_file}")

    def run(self):

        returns, weights = self.load_data()

        risk_df, portfolio_variance = self.compute_risk_contributions(
            returns,
            weights
        )

        self.save_outputs(risk_df, portfolio_variance)


if __name__ == "__main__":

    analysis = RiskContributionAnalysis()

    analysis.run()
