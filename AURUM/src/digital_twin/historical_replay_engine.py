# src/digital_twin/historical_replay_engine.py

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd


PRICE_MATRIX_PATH = Path("data/digital_twin/historical_price_matrix.csv")

WEIGHTS_CANDIDATES = [
    Path("data/optimization/meta_strategy_weights.csv"),
    Path("data/institutional/portfolio_weights.csv"),
    Path("data/optimization/risk_parity_weights.csv"),
    Path("data/optimization/min_variance_weights.csv"),
]

OUTPUT_DIR = Path("results/digital_twin/historical_replay")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


CRISIS_WINDOWS = {
    "2008_financial_crisis": {
        "start": "2008-09-01",
        "end": "2009-03-31",
        "description": "Global financial crisis and equity credit collapse.",
    },
    "covid_crash": {
        "start": "2020-02-15",
        "end": "2020-04-30",
        "description": "COVID liquidity shock and rapid market selloff.",
    },
    "inflation_2022": {
        "start": "2022-01-01",
        "end": "2022-12-31",
        "description": "Inflation shock, rates repricing, equity and bond drawdown.",
    },
    "banking_crisis_2023": {
        "start": "2023-03-01",
        "end": "2023-05-31",
        "description": "Regional banking stress and financial sector contagion.",
    },
    "available_full_history": {
        "start": "1900-01-01",
        "end": "2100-01-01",
        "description": "Replay across all available historical market data.",
    },
}


@dataclass
class ReplayResult:
    scenario: str
    start_date: str
    end_date: str
    description: str
    observations: int
    cumulative_return: float
    annualized_volatility: float
    max_drawdown: float
    worst_day_return: float
    best_day_return: float
    var_95: float
    cvar_95: float
    survival_status: str
    governance_action: str


class HistoricalReplayEngine:
    def load_price_matrix(self) -> pd.DataFrame:
        if not PRICE_MATRIX_PATH.exists():
            raise FileNotFoundError(
                f"Missing historical price matrix: {PRICE_MATRIX_PATH}. "
                "Run python -m src.digital_twin.historical_market_archive_builder first."
            )

        prices = pd.read_csv(PRICE_MATRIX_PATH)

        if "date" not in prices.columns:
            raise ValueError("Historical price matrix must contain a date column.")

        prices["date"] = pd.to_datetime(prices["date"])
        prices = prices.set_index("date").sort_index()

        numeric = prices.select_dtypes(include=[np.number])
        numeric = numeric.replace([np.inf, -np.inf], np.nan)

        return numeric

    def compute_returns(self, prices: pd.DataFrame) -> pd.DataFrame:
        returns = prices.pct_change()
        returns = returns.replace([np.inf, -np.inf], np.nan)
        return returns.dropna(how="all").fillna(0.0)

    def read_weight_file(self, path: Path, assets: List[str]) -> Dict[str, float]:
        try:
            df = pd.read_csv(path)
        except Exception:
            return {}

        lower_cols = {col.lower(): col for col in df.columns}

        asset_col = None
        weight_col = None

        for candidate in ["asset", "ticker", "symbol"]:
            if candidate in lower_cols:
                asset_col = lower_cols[candidate]
                break

        for candidate in ["weight", "weights", "allocation"]:
            if candidate in lower_cols:
                weight_col = lower_cols[candidate]
                break

        if asset_col is None or weight_col is None:
            return {}

        weights = {}

        for _, row in df.iterrows():
            asset = str(row[asset_col])
            weight = float(row[weight_col])

            if asset in assets:
                weights[asset] = weight

        total = sum(abs(v) for v in weights.values())

        if total == 0:
            return {}

        return {asset: weight / total for asset, weight in weights.items()}

    def load_portfolio_weights(self, assets: List[str]) -> Dict[str, float]:
        for path in WEIGHTS_CANDIDATES:
            if path.exists():
                weights = self.read_weight_file(path, assets)

                if weights:
                    print(f"[INFO] Using weights file: {path}")
                    return weights

        print("[WARN] No usable weights found. Using equal weights.")
        equal = 1.0 / len(assets)
        return {asset: equal for asset in assets}

    def portfolio_returns(
        self,
        returns: pd.DataFrame,
        weights: Dict[str, float],
    ) -> pd.Series:
        common_assets = [asset for asset in weights if asset in returns.columns]

        if not common_assets:
            raise ValueError("No overlap between portfolio weights and returns.")

        weight_vector = np.array([weights[asset] for asset in common_assets])
        portfolio = returns[common_assets].dot(weight_vector)

        return portfolio

    def max_drawdown(self, returns: pd.Series) -> float:
        cumulative = (1.0 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = cumulative / running_max - 1.0
        return float(drawdown.min())

    def cvar(self, returns: pd.Series, alpha: float = 0.95) -> float:
        var = returns.quantile(1 - alpha)
        tail = returns[returns <= var]

        if tail.empty:
            return float(var)

        return float(tail.mean())

    def survival_status(self, max_drawdown: float) -> str:
        if max_drawdown <= -0.30:
            return "FAILED"
        if max_drawdown <= -0.15:
            return "STRESSED"
        return "SURVIVED"

    def governance_action(self, max_drawdown: float, var_95: float) -> str:
        if max_drawdown <= -0.30:
            return "FORCE_DE_RISK_AND_ESCALATE_TO_INVESTMENT_COMMITTEE"
        if max_drawdown <= -0.15:
            return "REDUCE_RISK_AND_TRIGGER_GOVERNANCE_REVIEW"
        if var_95 <= -0.03:
            return "TIGHTEN_LIMITS_AND_MONITOR"
        return "NO_ACTION_REQUIRED"

    def replay_window(
        self,
        name: str,
        config: Dict[str, str],
        portfolio_daily_returns: pd.Series,
    ) -> ReplayResult:
        window = portfolio_daily_returns.loc[
            config["start"] : config["end"]
        ].dropna()

        if window.empty:
            return ReplayResult(
                scenario=name,
                start_date=config["start"],
                end_date=config["end"],
                description=config["description"],
                observations=0,
                cumulative_return=0.0,
                annualized_volatility=0.0,
                max_drawdown=0.0,
                worst_day_return=0.0,
                best_day_return=0.0,
                var_95=0.0,
                cvar_95=0.0,
                survival_status="NO_DATA",
                governance_action="NO_DATA_AVAILABLE",
            )

        cumulative_return = float((1.0 + window).prod() - 1.0)
        annualized_volatility = float(window.std() * np.sqrt(252))
        max_dd = self.max_drawdown(window)
        worst_day = float(window.min())
        best_day = float(window.max())
        var_95 = float(window.quantile(0.05))
        cvar_95 = self.cvar(window, alpha=0.95)

        return ReplayResult(
            scenario=name,
            start_date=config["start"],
            end_date=config["end"],
            description=config["description"],
            observations=int(window.shape[0]),
            cumulative_return=cumulative_return,
            annualized_volatility=annualized_volatility,
            max_drawdown=max_dd,
            worst_day_return=worst_day,
            best_day_return=best_day,
            var_95=var_95,
            cvar_95=cvar_95,
            survival_status=self.survival_status(max_dd),
            governance_action=self.governance_action(max_dd, var_95),
        )

    def run(self) -> List[ReplayResult]:
        prices = self.load_price_matrix()
        returns = self.compute_returns(prices)

        weights = self.load_portfolio_weights(list(returns.columns))
        portfolio_daily_returns = self.portfolio_returns(
            returns=returns,
            weights=weights,
        )

        results = []

        for name, config in CRISIS_WINDOWS.items():
            result = self.replay_window(
                name=name,
                config=config,
                portfolio_daily_returns=portfolio_daily_returns,
            )
            results.append(result)

        self.write_outputs(results, weights)
        return results

    def write_outputs(
        self,
        results: List[ReplayResult],
        weights: Dict[str, float],
    ) -> None:
        records = [asdict(result) for result in results]

        json_path = OUTPUT_DIR / "historical_replay_results.json"
        csv_path = OUTPUT_DIR / "historical_replay_results.csv"
        txt_path = OUTPUT_DIR / "historical_replay_report.txt"
        weights_path = OUTPUT_DIR / "replay_portfolio_weights.json"

        json_path.write_text(json.dumps(records, indent=2), encoding="utf-8")
        weights_path.write_text(json.dumps(weights, indent=2), encoding="utf-8")
        pd.DataFrame(records).to_csv(csv_path, index=False)

        lines = [
            "=" * 80,
            "AURUM HISTORICAL REPLAY ENGINE",
            "=" * 80,
            "",
            f"Historical Price Matrix: {PRICE_MATRIX_PATH}",
            "",
            "Portfolio Weights Used:",
        ]

        for asset, weight in weights.items():
            lines.append(f"  {asset}: {weight:.4f}")

        lines.extend(["", "-" * 80])

        for result in results:
            lines.extend(
                [
                    f"Scenario: {result.scenario}",
                    f"Window: {result.start_date} to {result.end_date}",
                    f"Description: {result.description}",
                    f"Observations: {result.observations}",
                    f"Cumulative Return: {result.cumulative_return:.4f}",
                    f"Annualized Volatility: {result.annualized_volatility:.4f}",
                    f"Max Drawdown: {result.max_drawdown:.4f}",
                    f"Worst Day Return: {result.worst_day_return:.4f}",
                    f"Best Day Return: {result.best_day_return:.4f}",
                    f"VaR 95: {result.var_95:.4f}",
                    f"CVaR 95: {result.cvar_95:.4f}",
                    f"Survival Status: {result.survival_status}",
                    f"Governance Action: {result.governance_action}",
                    "-" * 80,
                ]
            )

        txt_path.write_text("\n".join(lines), encoding="utf-8")

    def print_results(self, results: List[ReplayResult]) -> None:
        print("=" * 80)
        print("AURUM HISTORICAL REPLAY ENGINE")
        print("=" * 80)

        for result in results:
            print(f"\nScenario: {result.scenario}")
            print(f"Window: {result.start_date} to {result.end_date}")
            print(f"Observations: {result.observations}")
            print(f"Cumulative Return: {result.cumulative_return:.4f}")
            print(f"Annualized Volatility: {result.annualized_volatility:.4f}")
            print(f"Max Drawdown: {result.max_drawdown:.4f}")
            print(f"VaR 95: {result.var_95:.4f}")
            print(f"CVaR 95: {result.cvar_95:.4f}")
            print(f"Survival Status: {result.survival_status}")
            print(f"Governance Action: {result.governance_action}")


def main() -> None:
    engine = HistoricalReplayEngine()
    results = engine.run()
    engine.print_results(results)


if __name__ == "__main__":
    main()