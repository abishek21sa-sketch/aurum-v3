import pandas as pd
from pathlib import Path


class RegimeAwareReport:

    def __init__(self):

        self.optimization_path = Path("data/optimization")
        self.output_path = Path("results/reports")

    def load_outputs(self):

        weights = pd.read_csv(
            self.optimization_path / "regime_aware_weights.csv"
        )

        metrics = pd.read_csv(
            self.optimization_path / "regime_aware_metrics.csv"
        )

        return weights, metrics

    def build_report(self, weights, metrics):

        report = """
REGIME-AWARE OPTIMIZATION REPORT
================================

Optimization Objective:
Build separate minimum-variance portfolios for each detected market regime.

Regime Metrics:
"""

        report += metrics.to_string(index=False)

        report += """

Regime Portfolio Weights:
"""

        for regime in sorted(weights["regime"].unique()):

            regime_weights = weights[
                weights["regime"] == regime
            ].sort_values(
                "weight",
                ascending=False
            )

            report += f"""

{regime.upper()} REGIME:
{regime_weights[["asset", "weight"]].to_string(index=False)}
"""

        report += """

Interpretation:
The regime-aware optimizer produces different defensive portfolios depending on the detected market state. This allows the allocation engine to adapt to changing covariance and volatility structures instead of using one static portfolio for all environments.

The crisis and high-volatility regimes should be interpreted carefully when their observation counts are small. As more market history is added, these regime-conditioned estimates will become more stable.
"""

        return report

    def save_report(self, report):

        self.output_path.mkdir(parents=True, exist_ok=True)

        output_file = self.output_path / "regime_aware_optimization_report.txt"

        with open(output_file, "w") as file:
            file.write(report)

        print(report)
        print(f"\nSaved report: {output_file}")

    def run(self):

        weights, metrics = self.load_outputs()

        report = self.build_report(weights, metrics)

        self.save_report(report)


if __name__ == "__main__":

    report = RegimeAwareReport()

    report.run()
