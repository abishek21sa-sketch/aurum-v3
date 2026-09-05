import pandas as pd
from pathlib import Path


class MonteCarloReport:

    def __init__(self):

        self.optimization_path = Path("data/optimization")
        self.output_path = Path("results/reports")

    def load_simulations(self):

        return pd.read_csv(
            self.optimization_path / "monte_carlo_portfolios.csv"
        )

    def build_report(self, simulations):

        best_sharpe = simulations.loc[
            simulations["sharpe_ratio"].idxmax()
        ]

        min_volatility = simulations.loc[
            simulations["volatility"].idxmin()
        ]

        max_return = simulations.loc[
            simulations["expected_return"].idxmax()
        ]

        report = f"""
MONTE CARLO PORTFOLIO SIMULATION REPORT
=======================================

Simulation Summary:
- Number of simulated portfolios: {len(simulations)}

Best Sharpe Portfolio:
- Expected Return: {best_sharpe["expected_return"]:.6f}
- Volatility: {best_sharpe["volatility"]:.6f}
- Variance: {best_sharpe["variance"]:.10f}
- Sharpe Ratio: {best_sharpe["sharpe_ratio"]:.6f}

Minimum Volatility Simulated Portfolio:
- Expected Return: {min_volatility["expected_return"]:.6f}
- Volatility: {min_volatility["volatility"]:.6f}
- Variance: {min_volatility["variance"]:.10f}
- Sharpe Ratio: {min_volatility["sharpe_ratio"]:.6f}

Maximum Return Simulated Portfolio:
- Expected Return: {max_return["expected_return"]:.6f}
- Volatility: {max_return["volatility"]:.6f}
- Variance: {max_return["variance"]:.10f}
- Sharpe Ratio: {max_return["sharpe_ratio"]:.6f}

Interpretation:
The Monte Carlo simulation randomly samples feasible long-only, fully invested portfolios. This gives a stochastic view of the attainable risk-return space.

The best simulated Sharpe portfolio is useful as a benchmark against the mathematically optimized maximum Sharpe portfolio. If the optimizer consistently outperforms the Monte Carlo benchmark, the optimization engine is behaving correctly.
"""

        return report

    def save_report(self, report):

        self.output_path.mkdir(parents=True, exist_ok=True)

        output_file = self.output_path / "monte_carlo_report.txt"

        with open(output_file, "w") as file:
            file.write(report)

        print(report)
        print(f"\nSaved report: {output_file}")

    def run(self):

        simulations = self.load_simulations()

        report = self.build_report(simulations)

        self.save_report(report)


if __name__ == "__main__":

    report = MonteCarloReport()

    report.run()
