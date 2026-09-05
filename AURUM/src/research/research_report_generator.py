from pathlib import Path
import logging
from datetime import datetime

import pandas as pd


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


class ResearchReportGenerator:
    def __init__(self):
        self.research_dir = Path("data/research")
        self.validation_dir = Path("data/validation")
        self.risk_dir = Path("data/risk")
        self.forecasting_dir = Path("data/forecasting")
        self.signal_dir = Path("data/signals")
        self.institutional_dir = Path("data/institutional")

        self.output_dir = Path("results/research")
        self.report_path = self.output_dir / "institutional_quant_research_report.txt"

    def load_csv(self, path):
        if path.exists():
            return pd.read_csv(path)
        logger.warning("Missing file: %s", path)
        return pd.DataFrame()

    def load_inputs(self):
        logger.info("Loading research datasets.")

        self.experiment_registry = self.load_csv(self.research_dir / "experiment_registry.csv")
        self.walk_forward = self.load_csv(self.validation_dir / "walk_forward_report.csv")
        self.alpha_validation = self.load_csv(self.validation_dir / "alpha_validation_report.csv")
        self.transaction_costs = self.load_csv(self.validation_dir / "transaction_cost_summary.csv")

        self.tail_risk = self.load_csv(self.risk_dir / "tail_risk_report.csv")
        self.hedging_summary = self.load_csv(self.risk_dir / "dynamic_hedging_summary.csv")
        self.correlation_summary = self.load_csv(self.risk_dir / "correlation_breakdown_summary.csv")

        self.signal_decay = self.load_csv(self.forecasting_dir / "signal_decay_summary.csv")
        self.alpha_summary = self.load_csv(self.signal_dir / "cross_sectional_alpha_summary.csv")
        self.ensemble_summary = self.load_csv(self.forecasting_dir / "ensemble_forecast_summary.csv")

        self.portfolio_construction = self.load_csv(
            self.institutional_dir / "portfolio_construction_summary.csv"
        )
        self.portfolio_backtest = self.load_csv(
            self.institutional_dir / "portfolio_backtest_summary.csv"
        )
        self.portfolio_exposure = self.load_csv(
            self.institutional_dir / "portfolio_exposure_summary.csv"
        )

        logger.info("Loaded research datasets.")

    def build_report(self):
        logger.info("Building institutional research report.")

        wf = self.walk_forward.iloc[0]
        overall_tail = self.tail_risk[self.tail_risk["segment"] == "overall"].iloc[0]
        best_alpha = self.alpha_summary.sort_values("avg_regime_adjusted_alpha", ascending=False).iloc[0]
        weakest_alpha = self.alpha_summary.sort_values("avg_regime_adjusted_alpha").iloc[0]
        best_forecast = self.ensemble_summary.sort_values("avg_final_expected_return_signal", ascending=False).iloc[0]
        worst_forecast = self.ensemble_summary.sort_values("avg_final_expected_return_signal").iloc[0]
        best_decay = self.signal_decay.sort_values("avg_rank_ic", ascending=False).iloc[0]
        tc = self.transaction_costs.iloc[0]
        pb = self.portfolio_backtest.iloc[0]

        lines = []

        lines.append("AURUM INSTITUTIONAL QUANT SYSTEM REPORT")
        lines.append("=" * 80)
        lines.append("")
        lines.append(f"Generated: {datetime.now()}")
        lines.append("")

        lines.append("EXECUTIVE SUMMARY")
        lines.append("-" * 80)
        lines.append(
            "AURUM is an institutional quantitative research and portfolio construction "
            "system integrating macro regime intelligence, probabilistic forecasting, "
            "tail-risk analytics, dynamic hedging, alpha validation, transaction-cost "
            "modeling, and constrained portfolio allocation."
        )
        lines.append("")

        lines.append("CORE SYSTEM CAPABILITIES")
        lines.append("-" * 80)
        lines.append("- Macro feature engine")
        lines.append("- Hidden Markov regime modeling")
        lines.append("- Bayesian regime probability updating")
        lines.append("- Confidence calibration")
        lines.append("- CVaR / Expected Shortfall analytics")
        lines.append("- Dynamic hedging and volatility targeting")
        lines.append("- Correlation breakdown detection")
        lines.append("- Cross-sectional alpha modeling")
        lines.append("- Ensemble forecasting")
        lines.append("- Signal decay analytics")
        lines.append("- Alpha validation")
        lines.append("- Walk-forward testing")
        lines.append("- Transaction-cost modeling")
        lines.append("- Institutional portfolio construction")
        lines.append("- Portfolio backtesting")
        lines.append("- Experiment tracking")
        lines.append("")

        lines.append("WALK-FORWARD VALIDATION")
        lines.append("-" * 80)
        lines.append(f"Prediction Days: {int(wf['prediction_days'])}")
        lines.append(f"Walk-Forward Sharpe-Like: {wf['walk_forward_sharpe_like']:.4f}")
        lines.append(f"Average Realized IC: {wf['avg_realized_ic']:.4f}")
        lines.append(f"Maximum Drawdown: {wf['max_drawdown']:.4f}")
        lines.append("")

        lines.append("TAIL RISK ANALYTICS")
        lines.append("-" * 80)
        lines.append(f"Portfolio VaR 95: {overall_tail['var_95']:.4f}")
        lines.append(f"Portfolio CVaR 95: {overall_tail['cvar_95_expected_shortfall']:.4f}")
        lines.append(f"Portfolio Max Drawdown: {overall_tail['max_drawdown']:.4f}")
        lines.append(f"Portfolio Volatility: {overall_tail['volatility']:.4f}")
        lines.append("")

        lines.append("DYNAMIC HEDGING SYSTEM")
        lines.append("-" * 80)
        for _, row in self.hedging_summary.iterrows():
            lines.append(
                f"{row['hedging_regime_label']} | "
                f"Equity={row['avg_equity_exposure']:.3f} | "
                f"Hedge Intensity={row['avg_hedge_intensity']:.3f}"
            )
        lines.append("")

        lines.append("ALPHA RESEARCH")
        lines.append("-" * 80)
        lines.append(
            f"Strongest Regime-Adjusted Alpha: {best_alpha['asset']} "
            f"({best_alpha['avg_regime_adjusted_alpha']:.4f})"
        )
        lines.append(
            f"Weakest Regime-Adjusted Alpha: {weakest_alpha['asset']} "
            f"({weakest_alpha['avg_regime_adjusted_alpha']:.4f})"
        )
        lines.append("")

        lines.append("ENSEMBLE FORECASTING")
        lines.append("-" * 80)
        lines.append(
            f"Highest Forecast Asset: {best_forecast['asset']} "
            f"({best_forecast['avg_final_expected_return_signal']:.4f})"
        )
        lines.append(
            f"Lowest Forecast Asset: {worst_forecast['asset']} "
            f"({worst_forecast['avg_final_expected_return_signal']:.4f})"
        )
        lines.append("")

        lines.append("SIGNAL DECAY ANALYSIS")
        lines.append("-" * 80)
        lines.append(f"Best Horizon: {int(best_decay['horizon_days'])} Days")
        lines.append(f"Average Rank IC: {best_decay['avg_rank_ic']:.4f}")
        lines.append(f"Average Top-Bottom Spread: {best_decay['avg_top_bottom_spread']:.4f}")
        lines.append("")

        lines.append("TRANSACTION COST ANALYSIS")
        lines.append("-" * 80)
        lines.append(f"Transaction Cost Assumption: {tc['transaction_cost_bps']:.1f} bps")
        lines.append(f"Gross Sharpe-Like: {tc['gross_sharpe_like']:.4f}")
        lines.append(f"Net Sharpe-Like: {tc['net_sharpe_like']:.4f}")
        lines.append(f"Gross Terminal Equity: {tc['gross_terminal_equity']:.4f}")
        lines.append(f"Net Terminal Equity: {tc['net_terminal_equity']:.4f}")
        lines.append(f"Total Cost Drag: {tc['total_cost_drag']:.4f}")
        lines.append("")

        lines.append("INSTITUTIONAL PORTFOLIO BACKTEST")
        lines.append("-" * 80)
        lines.append(f"Gross Avg Daily Return: {pb['gross_avg_daily_return']:.6f}")
        lines.append(f"Net Avg Daily Return: {pb['net_avg_daily_return']:.6f}")
        lines.append(f"Gross Sharpe-Like: {pb['gross_sharpe_like']:.4f}")
        lines.append(f"Net Sharpe-Like: {pb['net_sharpe_like']:.4f}")
        lines.append(f"Gross Max Drawdown: {pb['gross_max_drawdown']:.4f}")
        lines.append(f"Net Max Drawdown: {pb['net_max_drawdown']:.4f}")
        lines.append(f"Average Turnover: {pb['avg_turnover']:.4f}")
        lines.append(f"Average Cash Weight: {pb['avg_cash_weight']:.4f}")
        lines.append(f"Gross Terminal Equity: {pb['gross_terminal_equity']:.4f}")
        lines.append(f"Net Terminal Equity: {pb['net_terminal_equity']:.4f}")
        lines.append("")

        lines.append("PORTFOLIO CONSTRUCTION SUMMARY")
        lines.append("-" * 80)
        for _, row in self.portfolio_construction.iterrows():
            lines.append(
                f"{row['asset']} | Avg Weight={row['avg_weight']:.3f} | "
                f"Max Weight={row['max_weight']:.3f}"
            )
        lines.append("")

        lines.append("DEPLOYABILITY ASSESSMENT")
        lines.append("-" * 80)
        lines.append(
            "The infrastructure is execution-aware and institutionally structured. "
            "The portfolio allocator enforces hard exposure caps, allows cash as a "
            "risk-control state, and evaluates net performance after transaction costs."
        )
        lines.append("")
        lines.append(
            "Current results indicate that risk management and allocation controls are "
            "functioning, but the current alpha layer is not yet strong enough for live "
            "capital deployment after transaction costs."
        )
        lines.append("")
        lines.append(
            "System status: institutional research and portfolio infrastructure complete; "
            "alpha improvement remains the primary future research priority."
        )
        lines.append("")

        lines.append("FUTURE WORK")
        lines.append("-" * 80)
        lines.append("- Transaction-cost-aware optimizer")
        lines.append("- Stronger alpha factors and signal orthogonalization")
        lines.append("- True macro data integration from external sources")
        lines.append("- Adaptive covariance estimation")
        lines.append("- Execution simulation and order-level slippage model")
        lines.append("- Dashboard integration for institutional monitoring")
        lines.append("")

        lines.append("=" * 80)

        self.report_text = "\n".join(lines)

    def save_report(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)

        with open(self.report_path, "w", encoding="utf-8") as file:
            file.write(self.report_text)

        logger.info("Saved report to: %s", self.report_path)

    def run(self):
        logger.info("Starting Research Report Generator.")
        self.load_inputs()
        self.build_report()
        self.save_report()
        logger.info("Research Report Generator completed successfully.")


if __name__ == "__main__":
    generator = ResearchReportGenerator()
    generator.run()