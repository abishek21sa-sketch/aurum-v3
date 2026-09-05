import pandas as pd
from pathlib import Path


class MeanVarianceReport:

    def __init__(self):

        self.optimization_path = Path("data/optimization")
        self.output_path = Path("results/reports")

    def load_outputs(self):

        weights = pd.read_csv(
            self.optimization_path / "mean_variance_weights.csv"
        )

        summary = pd.read_csv(
            self.optimization_path / "mean_variance_summary.csv"
        )

        return weights, summary

    def get_metric(self, summary, metric_name):

        return summary.loc[
            summary["metric"] == metric_name,
            "value"
        ].iloc[0]

    def build_report(self, weights, summary):

        portfolio_variance = self.get_metric(summary, "portfolio_variance")
        portfolio_volatility = self.get_metric(summary, "portfolio_volatility")
        expected_return = self.get_metric(summary, "expected_return")
        sharpe_ratio = self.get_metric(summary, "sharpe_ratio")
        risk_aversion = self.get_metric(summary, "risk_aversion")
        objective_value = self.get_metric(summary, "objective_value")

        weights_sorted = weights.sort_values(
            "weight",
            ascending=False
        )

        report = f"""
MEAN-VARIANCE OPTIMIZATION REPORT
=================================

Optimization Objective:
Maximize expected return while penalizing portfolio variance.

Mathematical Form:
minimize: - expected_return + risk_aversion * portfolio_variance

Constraints:
- Long-only weights
- Fully invested portfolio
- Weight bounds: 0 to 1 per asset

Portfolio Metrics:
- Portfolio Variance: {portfolio_variance:.10f}
- Portfolio Volatility: {portfolio_volatility:.6f}
- Expected Return: {expected_return:.6f}
- Sharpe Ratio: {sharpe_ratio:.6f}
- Risk Aversion: {risk_aversion:.2f}
- Objective Value: {objective_value:.10f}

Weights:
{weights_sorted.to_string(index=False)}

Interpretation:
The mean-variance optimizer balances expected return against portfolio variance. Unlike the minimum variance portfolio, this model actively rewards assets with higher estimated returns. The risk_aversion parameter controls how aggressively the optimizer penalizes risk.

A lower risk_aversion value produces a more return-seeking portfolio. A higher risk_aversion value produces a more defensive portfolio.
"""

        return report

    def save_report(self, report):

        self.output_path.mkdir(parents=True, exist_ok=True)

        output_file = self.output_path / "mean_variance_optimization_report.txt"

        with open(output_file, "w") as file:
            file.write(report)

        print(report)
        print(f"\nSaved report: {output_file}")

    def run(self):

        weights, summary = self.load_outputs()

        report = self.build_report(weights, summary)

        self.save_report(report)


if __name__ == "__main__":

    report = MeanVarianceReport()

    report.run()
