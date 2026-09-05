import pandas as pd
from pathlib import Path


class OptimizationReport:

    def __init__(self):

        self.optimization_path = Path("data/optimization")
        self.output_path = Path("results/reports")

    def load_outputs(self):

        weights = pd.read_csv(
            self.optimization_path / "min_variance_weights.csv"
        )

        summary = pd.read_csv(
            self.optimization_path / "optimization_summary.csv"
        )

        return weights, summary

    def get_metric(self, summary, metric_name):

        return summary.loc[
            summary["metric"] == metric_name,
            "value"
        ].iloc[0]

    def build_report(self, weights, summary):

        portfolio_variance = self.get_metric(
            summary,
            "portfolio_variance"
        )

        portfolio_volatility = self.get_metric(
            summary,
            "portfolio_volatility"
        )

        expected_return = self.get_metric(
            summary,
            "expected_return"
        )

        sharpe_ratio = self.get_metric(
            summary,
            "sharpe_ratio"
        )

        weights_sorted = weights.sort_values(
            "weight",
            ascending=False
        )

        report = f"""
PORTFOLIO OPTIMIZATION REPORT
=============================

Optimization Objective:
Minimum Variance Portfolio

Constraints:
- Long-only weights
- Fully invested portfolio
- Weight bounds: 0 to 1 per asset

Portfolio Metrics:
- Portfolio Variance: {portfolio_variance:.10f}
- Portfolio Volatility: {portfolio_volatility:.6f}
- Expected Return: {expected_return:.6f}
- Sharpe Ratio: {sharpe_ratio:.6f}

Top Allocations:
{weights_sorted.to_string(index=False)}

Interpretation:
The optimizer constructs the lowest-variance portfolio under long-only and fully invested constraints. The solution allocates more weight to assets that reduce total covariance risk across the selected universe. Assets with high standalone volatility, high covariance contribution, or weak diversification value may receive lower or zero allocation.

The expected return and Sharpe ratio are diagnostic metrics only in this version. The optimization objective is still purely minimum variance, not return maximization.
"""

        return report

    def save_report(self, report):

        self.output_path.mkdir(parents=True, exist_ok=True)

        output_file = self.output_path / "portfolio_optimization_report.txt"

        with open(output_file, "w") as file:
            file.write(report)

        print(report)
        print(f"\nSaved report: {output_file}")

    def run(self):

        weights, summary = self.load_outputs()

        report = self.build_report(weights, summary)

        self.save_report(report)


if __name__ == "__main__":

    report = OptimizationReport()

    report.run()
