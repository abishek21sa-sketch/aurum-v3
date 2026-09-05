from pathlib import Path
import logging
import subprocess
import sys
import time
import json
from datetime import datetime, timezone


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


class ResearchPipelineOrchestrator:
    """
    Institutional Research Pipeline Orchestrator for AURUM.

    Runs the full research-to-portfolio stack in dependency order:
    - macro features
    - regime inference
    - Bayesian calibration
    - risk analytics
    - alpha research
    - forecasting
    - validation
    - institutional portfolio construction
    - backtesting
    - experiment tracking
    - report generation
    """

    def __init__(self):
        self.output_dir = Path("data/infrastructure")
        self.run_log_path = self.output_dir / "research_pipeline_run_log.json"

        self.pipeline_steps = [
            {
                "name": "Macro Feature Engine",
                "module": "src.macro.macro_feature_engine",
                "critical": True,
            },
            {
                "name": "Hidden Markov Regime Engine",
                "module": "src.regimes.hidden_markov_regime_engine",
                "critical": True,
            },
            {
                "name": "Bayesian Regime Updater",
                "module": "src.regimes.bayesian_regime_updater",
                "critical": True,
            },
            {
                "name": "Regime Confidence Calibrator",
                "module": "src.regimes.regime_confidence_calibrator",
                "critical": True,
            },
            {
                "name": "Tail Risk Engine",
                "module": "src.risk.tail_risk_engine",
                "critical": True,
            },
            {
                "name": "Dynamic Hedging Engine",
                "module": "src.risk.dynamic_hedging_engine",
                "critical": True,
            },
            {
                "name": "Correlation Breakdown Detector",
                "module": "src.risk.correlation_breakdown_detector",
                "critical": True,
            },
            {
                "name": "Cross-Sectional Alpha Engine",
                "module": "src.signals.cross_sectional_alpha_engine",
                "critical": True,
            },
            {
                "name": "Ensemble Forecast Engine",
                "module": "src.forecasting.ensemble_forecast_engine",
                "critical": True,
            },
            {
                "name": "Signal Decay Analyzer",
                "module": "src.forecasting.signal_decay_analyzer",
                "critical": True,
            },
            {
                "name": "Alpha Validation Engine",
                "module": "src.validation.alpha_validation_engine",
                "critical": True,
            },
            {
                "name": "Walk-Forward Framework",
                "module": "src.validation.walk_forward_framework",
                "critical": True,
            },
            {
                "name": "Transaction Cost Engine",
                "module": "src.validation.transaction_cost_engine",
                "critical": True,
            },
            {
                "name": "Portfolio Construction Engine",
                "module": "src.institutional.portfolio_construction_engine",
                "critical": True,
            },
            {
                "name": "Portfolio Backtest Engine",
                "module": "src.institutional.portfolio_backtest_engine",
                "critical": True,
            },
            {
                "name": "Experiment Tracker",
                "module": "src.research.experiment_tracker",
                "critical": True,
            },
            {
                "name": "Research Report Generator",
                "module": "src.research.research_report_generator",
                "critical": True,
            },
        ]

    def run_step(self, step):
        logger.info("=" * 80)
        logger.info("RUNNING STEP: %s", step["name"])
        logger.info("MODULE: %s", step["module"])

        start = time.perf_counter()

        result = subprocess.run(
            [sys.executable, "-m", step["module"]],
            capture_output=True,
            text=True,
        )

        elapsed = time.perf_counter() - start

        step_record = {
            "name": step["name"],
            "module": step["module"],
            "critical": step["critical"],
            "status": "PASS" if result.returncode == 0 else "FAIL",
            "returncode": result.returncode,
            "runtime_seconds": round(elapsed, 4),
            "stdout_tail": result.stdout[-3000:],
            "stderr_tail": result.stderr[-3000:],
        }

        if result.returncode == 0:
            logger.info("STEP PASSED: %s | %.2fs", step["name"], elapsed)
        else:
            logger.error("STEP FAILED: %s | %.2fs", step["name"], elapsed)
            logger.error("STDERR:\n%s", result.stderr[-3000:])

        return step_record

    def run_pipeline(self):
        logger.info("Starting AURUM institutional research pipeline.")

        self.output_dir.mkdir(parents=True, exist_ok=True)

        run_record = {
            "pipeline_name": "aurum_institutional_research_pipeline",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "steps": [],
            "overall_status": "PASS",
        }

        start = time.perf_counter()

        for step in self.pipeline_steps:
            step_record = self.run_step(step)
            run_record["steps"].append(step_record)

            if step_record["status"] == "FAIL":
                run_record["overall_status"] = "FAIL"

                if step["critical"]:
                    logger.error(
                        "Critical step failed. Stopping pipeline at: %s",
                        step["name"],
                    )
                    break

        total_elapsed = time.perf_counter() - start
        run_record["total_runtime_seconds"] = round(total_elapsed, 4)

        with open(self.run_log_path, "w", encoding="utf-8") as file:
            json.dump(run_record, file, indent=4)

        logger.info("=" * 80)
        logger.info("Pipeline status: %s", run_record["overall_status"])
        logger.info("Total runtime: %.2fs", total_elapsed)
        logger.info("Saved run log to: %s", self.run_log_path)

        if run_record["overall_status"] != "PASS":
            raise SystemExit(1)

    def run(self):
        self.run_pipeline()


if __name__ == "__main__":
    orchestrator = ResearchPipelineOrchestrator()
    orchestrator.run()