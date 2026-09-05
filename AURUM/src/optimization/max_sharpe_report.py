import pandas as pd
from pathlib import Path


class MaxSharpeReport:

    def __init__(self):

        self.optimization_path = Path("data/optimization")
        self.output_path = Path("results/reports")

    def load_outputs(self):

        weights = pd.read_csv(
            self.optimization_path / "max_sharpe_weights.csv"
        )

        summary = pd.read_csv(
            self.optimization_path / "max_sharpe_summary.csv"
        )

        return weights, summary

    def get_metric(self, summary, metric_name):

        return summary.loc[
            summary["metric"] == metric_name,
            "value"
        ].iloc[0]

    def build_report(self, weights, summary):

        expected_return = self.get_metric(summary, "expected_return")
        volatility = self.get_metric(summary, "volatility")
        variance = self.get_metric(summary, "variance")
        sharpe_ratio = self.get_metric(summary, "sharpe_ratio")

        weights_sorted = weights.sort_values(
            "weight",
            ascending=False
        )

        report = f"""
MAXIMUM SHARPE PORTFOLIO REPORT
===============================

Optimization Objective:
Select the efficient frontier portfolio with the highest Sharpe ratio.

Portfolio Metrics:
- Expected Return: {expected_return:.6f}
- Volatility: {volatility:.6f}
- Variance: {variance:.10f}
- Sharpe Ratio: {sharpe_ratio:.6f}

Weights:
{weights_sorted.to_string(index=False)}

Interpretation:
The maximum Sharpe portfolio gives the highest expected return per unit of volatility among the sampled efficient frontier portfolios.

This portfolio is more balanced than the aggressive mean-variance solution because it does not simply chase return. Instead, it rewards portfolios that improve risk-adjusted performance.
"""

        return report

    def save_report(self, report):

        self.output_path.mkdir(parents=True, exist_ok=True)

        output_file = self.output_path / "max_sharpe_report.txt"

        with open(output_file, "w") as file:
            file.write(report)

        print(report)
        print(f"\nSaved report: {output_file}")

    def run(self):

        weights, summary = self.load_outputs()

        report = self.build_report(weights, summary)

        self.save_report(report)


if __name__ == "__main__":

    report = MaxSharpeReport()

    report.run()
