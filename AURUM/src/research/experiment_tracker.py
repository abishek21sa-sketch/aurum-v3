from pathlib import Path
import json
import logging
from datetime import datetime, timezone

import pandas as pd


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


class ExperimentTracker:
    """
    Lightweight experiment tracker for AURUM.

    Tracks:
    - model configuration
    - walk-forward metrics
    - alpha validation metrics
    - tail risk metrics
    - hedging diagnostics
    - timestamped experiment registry
    """

    def __init__(self):
        self.validation_dir = Path("data/validation")
        self.risk_dir = Path("data/risk")
        self.forecasting_dir = Path("data/forecasting")
        self.regime_dir = Path("data/regimes")

        self.output_dir = Path("data/research")
        self.registry_path = self.output_dir / "experiment_registry.csv"
        self.latest_json_path = self.output_dir / "latest_experiment_summary.json"

    def load_metric_file(self, path: Path):
        if path.exists():
            return pd.read_csv(path)

        logger.warning("Missing metric file: %s", path)
        return pd.DataFrame()

    def collect_metrics(self):
        logger.info("Collecting experiment metrics.")

        walk_forward = self.load_metric_file(
            self.validation_dir / "walk_forward_report.csv"
        )

        alpha_validation = self.load_metric_file(
            self.validation_dir / "alpha_validation_report.csv"
        )

        tail_risk = self.load_metric_file(
            self.risk_dir / "tail_risk_report.csv"
        )

        hedging = self.load_metric_file(
            self.risk_dir / "dynamic_hedging_summary.csv"
        )

        signal_decay = self.load_metric_file(
            self.forecasting_dir / "signal_decay_summary.csv"
        )

        regime_summary = self.load_metric_file(
            self.regime_dir / "calibrated_regime_summary.csv"
        )

        metrics = {}

        if not walk_forward.empty:
            row = walk_forward.iloc[0]
            metrics["walk_forward_sharpe_like"] = row.get("walk_forward_sharpe_like")
            metrics["walk_forward_max_drawdown"] = row.get("max_drawdown")
            metrics["walk_forward_avg_realized_ic"] = row.get("avg_realized_ic")
            metrics["walk_forward_prediction_days"] = row.get("prediction_days")

        if not alpha_validation.empty:
            row = alpha_validation.iloc[0]
            metrics["alpha_hit_ratio"] = row.get("hit_ratio")
            metrics["alpha_long_short_sharpe_like"] = row.get("long_short_sharpe_like")
            metrics["alpha_max_drawdown"] = row.get("max_drawdown")
            metrics["alpha_avg_turnover"] = row.get("avg_top_book_turnover")

        if not tail_risk.empty:
            overall = tail_risk[tail_risk["segment"] == "overall"]
            if not overall.empty:
                row = overall.iloc[0]
                metrics["portfolio_var_95"] = row.get("var_95")
                metrics["portfolio_cvar_95"] = row.get("cvar_95_expected_shortfall")
                metrics["portfolio_tail_max_drawdown"] = row.get("max_drawdown")

        if not hedging.empty:
            metrics["hedging_avg_equity_exposure"] = hedging.get(
                "avg_equity_exposure", pd.Series(dtype=float)
            ).mean()
            metrics["hedging_avg_hedge_intensity"] = hedging.get(
                "avg_hedge_intensity", pd.Series(dtype=float)
            ).mean()

        if not signal_decay.empty:
            best_horizon = signal_decay.sort_values(
                "avg_rank_ic", ascending=False
            ).head(1)

            if not best_horizon.empty:
                row = best_horizon.iloc[0]
                metrics["best_signal_horizon_days"] = row.get("horizon_days")
                metrics["best_signal_rank_ic"] = row.get("avg_rank_ic")
                metrics["best_signal_spread"] = row.get("avg_top_bottom_spread")

        if not regime_summary.empty:
            metrics["avg_calibrated_confidence"] = regime_summary.get(
                "avg_calibrated_confidence", pd.Series(dtype=float)
            ).mean()
            metrics["avg_calibrated_max_probability"] = regime_summary.get(
                "avg_calibrated_max_probability", pd.Series(dtype=float)
            ).mean()

        self.metrics = metrics

        logger.info("Collected metrics: %s", self.metrics)

    def build_experiment_record(self):
        logger.info("Building experiment record.")

        timestamp = datetime.now(timezone.utc).isoformat()

        self.record = {
            "experiment_id": f"aurum_quant_phase2_{timestamp}",
            "timestamp_utc": timestamp,
            "phase": "quant_research_phase2",
            "macro_engine_version": "v2",
            "hmm_engine_version": "v2",
            "bayesian_updater_version": "v2",
            "calibration_version": "v2",
            "tail_risk_engine_version": "v2",
            "dynamic_hedging_engine_version": "v2",
            "correlation_breakdown_version": "v2",
            "alpha_engine_version": "v2",
            "ensemble_forecast_version": "v2",
            "signal_decay_version": "v2",
            "walk_forward_framework_version": "v1",
        }

        self.record.update(self.metrics)

        logger.info("Experiment record built.")

    def update_registry(self):
        logger.info("Updating experiment registry.")

        self.output_dir.mkdir(parents=True, exist_ok=True)

        new_row = pd.DataFrame([self.record])

        if self.registry_path.exists():
            registry = pd.read_csv(self.registry_path)
            registry = pd.concat([registry, new_row], ignore_index=True)
        else:
            registry = new_row

        registry.to_csv(self.registry_path, index=False)

        with open(self.latest_json_path, "w", encoding="utf-8") as file:
            json.dump(self.record, file, indent=4)

        self.registry = registry

        logger.info("Saved experiment registry to: %s", self.registry_path)
        logger.info("Saved latest experiment summary to: %s", self.latest_json_path)

    def run(self):
        logger.info("Starting Experiment Tracker.")

        self.collect_metrics()
        self.build_experiment_record()
        self.update_registry()

        logger.info("Experiment Tracker completed successfully.")


if __name__ == "__main__":
    tracker = ExperimentTracker()
    tracker.run()