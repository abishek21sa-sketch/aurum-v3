import pandas as pd
from pathlib import Path


class EfficientFrontierReport:

    def __init__(self):

        self.optimization_path = Path("data/optimization")
        self.output_path = Path("results/reports")

    def load_frontier(self):

        return pd.read_csv(
            self.optimization_path / "efficient_frontier.csv"
        )

    def build_report(self, frontier_df):

        min_vol_portfolio = frontier_df.loc[
            frontier_df["volatility"].idxmin()
        ]

        max_sharpe_portfolio = frontier_df.loc[
            frontier_df["sharpe_ratio"].idxmax()
        ]

        max_return_portfolio = frontier_df.loc[
            frontier_df["expected_return"].idxmax()
        ]

        report = f"""
EFFICIENT FRONTIER REPORT
=========================

Frontier Summary:
- Number of feasible frontier portfolios: {len(frontier_df)}

Minimum Volatility Portfolio:
- Expected Return: {min_vol_portfolio["expected_return"]:.6f}
- Volatility: {min_vol_portfolio["volatility"]:.6f}
- Sharpe Ratio: {min_vol_portfolio["sharpe_ratio"]:.6f}

Maximum Sharpe Portfolio:
- Expected Return: {max_sharpe_portfolio["expected_return"]:.6f}
- Volatility: {max_sharpe_portfolio["volatility"]:.6f}
- Sharpe Ratio: {max_sharpe_portfolio["sharpe_ratio"]:.6f}

Maximum Return Portfolio:
- Expected Return: {max_return_portfolio["expected_return"]:.6f}
- Volatility: {max_return_portfolio["volatility"]:.6f}
- Sharpe Ratio: {max_return_portfolio["sharpe_ratio"]:.6f}

Interpretation:
The efficient frontier traces the best attainable portfolio return for each level of portfolio risk under the current long-only, fully invested constraint set.

The lower-left region represents defensive allocations with lower volatility. The upper-right region represents return-seeking allocations with higher risk. The maximum Sharpe portfolio gives the best return per unit of volatility among the sampled frontier portfolios.
"""

        return report

    def save_report(self, report):

        self.output_path.mkdir(parents=True, exist_ok=True)

        output_file = self.output_path / "efficient_frontier_report.txt"

        with open(output_file, "w") as file:
            file.write(report)

        print(report)
        print(f"\nSaved report: {output_file}")

    def run(self):

        frontier_df = self.load_frontier()

        report = self.build_report(frontier_df)

        self.save_report(report)


if __name__ == "__main__":

    report = EfficientFrontierReport()

    report.run()
