import pandas as pd
from pathlib import Path


class CVaRReport:

    def __init__(self):

        self.optimization_path = Path("data/optimization")
        self.output_path = Path("results/reports")

    def load_outputs(self):

        weights = pd.read_csv(
            self.optimization_path / "cvar_weights.csv"
        )

        summary = pd.read_csv(
            self.optimization_path / "cvar_summary.csv"
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
        var_95 = self.get_metric(summary, "var_95")
        cvar_95 = self.get_metric(summary, "cvar_95")
        sharpe_ratio = self.get_metric(summary, "sharpe_ratio")
        alpha = self.get_metric(summary, "alpha")
        objective_value = self.get_metric(summary, "objective_value")

        weights_sorted = weights.sort_values(
            "weight",
            ascending=False
        )

        report = f"""
CVaR OPTIMIZATION REPORT
========================

Optimization Objective:
Minimize Conditional Value at Risk at the {alpha:.0%} confidence level.

Risk Interpretation:
- VaR estimates the loss threshold at the selected tail confidence level.
- CVaR estimates the average loss beyond that threshold.
- CVaR is therefore more conservative than variance because it directly focuses on downside tail losses.

Portfolio Metrics:
- Expected Return: {expected_return:.6f}
- Volatility: {volatility:.6f}
- Variance: {variance:.10f}
- VaR 95%: {var_95:.6f}
- CVaR 95%: {cvar_95:.6f}
- Sharpe Ratio: {sharpe_ratio:.6f}
- Objective Value: {objective_value:.6f}

Weights:
{weights_sorted.to_string(index=False)}

Interpretation:
The CVaR optimizer constructs a portfolio that reduces expected loss in the worst tail of the return distribution. Unlike minimum variance optimization, this model does not merely reduce average dispersion. It specifically penalizes severe downside outcomes.

This portfolio is useful as a defensive institutional allocation model when the objective is tail-risk control rather than maximum return or maximum Sharpe ratio.
"""

        return report

    def save_report(self, report):

        self.output_path.mkdir(parents=True, exist_ok=True)

        output_file = self.output_path / "cvar_optimization_report.txt"

        with open(output_file, "w") as file:
            file.write(report)

        print(report)
        print(f"\nSaved report: {output_file}")

    def run(self):

        weights, summary = self.load_outputs()

        report = self.build_report(weights, summary)

        self.save_report(report)


if __name__ == "__main__":

    report = CVaRReport()

    report.run()
