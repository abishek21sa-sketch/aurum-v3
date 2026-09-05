from pathlib import Path
import json
import logging

import pandas as pd


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)

SPY_PATH = Path("data/processed/SPY_processed.csv")

class RiskDashboardBuilder:
    """
    AURUM Risk Dashboard Builder.

    Consolidates:
    - Portfolio Risk
    - Tail Risk
    - Exposure Analytics
    - Correlation Analytics
    - Factor Analytics

    into a single institutional dashboard payload.
    """

    def __init__(self):
        self.risk_dir = Path("results/risk")

        self.portfolio_risk_path = (
            self.risk_dir / "portfolio_risk_report.csv"
        )

        self.tail_risk_path = (
            self.risk_dir / "tail_risk_report.csv"
        )

        self.exposure_path = (
            self.risk_dir / "exposure_report.csv"
        )

        self.correlation_path = (
            self.risk_dir / "correlation_report.csv"
        )

        self.factor_path = (
            self.risk_dir / "factor_concentration_report.csv"
        )

        self.dashboard_path = (
            self.risk_dir / "risk_dashboard.json"
        )

    def load_report(self, path: Path):
        if not path.exists():
            logger.warning("Missing report: %s", path)
            return []

        try:
            df = pd.read_csv(path)
            return df.to_dict(orient="records")

        except Exception as exc:
            logger.exception(
                "Failed reading report %s",
                path,
            )
            return [{"error": str(exc)}]

    def build_dashboard(self):
        logger.info("Building institutional risk dashboard.")

        dashboard = {
            "dashboard_type": "AURUM Institutional Risk Dashboard",
            "version": "3A",
            "portfolio_risk": self.load_report(
                self.portfolio_risk_path
            ),
            "tail_risk": self.load_report(
                self.tail_risk_path
            ),
            "exposure_analytics": self.load_report(
                self.exposure_path
            ),
            "correlation_analytics": self.load_report(
                self.correlation_path
            ),
            "factor_analytics": self.load_report(
                self.factor_path
            ),
        }

        return dashboard

    def save_dashboard(self, dashboard):
        self.risk_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        with open(
            self.dashboard_path,
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                dashboard,
                f,
                indent=4,
                default=str,
            )

        logger.info(
            "Saved risk dashboard to: %s",
            self.dashboard_path,
        )

    def load_spy_returns() -> pd.DataFrame:
        if not SPY_PATH.exists():
            raise FileNotFoundError(f"Missing SPY benchmark file: {SPY_PATH}")

        spy = pd.read_csv(SPY_PATH)
        spy["Date"] = pd.to_datetime(spy["Date"])

        if "daily_return" in spy.columns:
            return_col = "daily_return"
        elif "Return" in spy.columns:
            return_col = "Return"
        elif "return" in spy.columns:
            return_col = "return"
        else:
            raise ValueError(f"No SPY return column found in {SPY_PATH}")

        return spy[["Date", return_col]].rename(
            columns={return_col: "spy_return"}
        )

    def run(self):
        logger.info(
            "Starting Risk Dashboard Builder."
        )

        dashboard = self.build_dashboard()
        self.save_dashboard(dashboard)

        logger.info(
            "Risk Dashboard Builder completed successfully."
        )


if __name__ == "__main__":
    builder = RiskDashboardBuilder()
    builder.run()