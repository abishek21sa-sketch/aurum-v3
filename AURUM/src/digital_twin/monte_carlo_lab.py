# src/digital_twin/monte_carlo_lab.py

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


RETURN_MATRIX_PATH = Path("data/market_matrix/market_return_matrix.csv")
WEIGHTS_CANDIDATES = [
    Path("data/optimization/meta_strategy_weights.csv"),
    Path("data/institutional/portfolio_weights.csv"),
    Path("data/optimization/risk_parity_weights.csv"),
    Path("data/optimization/min_variance_weights.csv"),
]

OUTPUT_DIR = Path("results/digital_twin/monte_carlo_lab")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class MonteCarloSummary:
    simulations: int
    horizon_days: int
    expected_cumulative_return: float
    median_cumulative_return: float
    worst_cumulative_return: float
    best_cumulative_return: float
    expected_annualized_volatility: float
    expected_max_drawdown: float
    var_95: float
    cvar_95: float
    probability_of_loss: float
    probability_drawdown_gt_10: float
    probability_drawdown_gt_20: float
    probability_drawdown_gt_30: float
    survival_status: str


class MonteCarloLab:
    def __init__(
        self,
        simulations: int = 10_000,
        horizon_days: int = 252,
        random_seed: int = 42,
    ) -> None:
        self.simulations = simulations
        self.horizon_days = horizon_days
        self.random_seed = random_seed
        np.random.seed(self.random_seed)

    def load_return_matrix(self) -> pd.DataFrame:
        if not RETURN_MATRIX_PATH.exists():
            raise FileNotFoundError(f"Missing return matrix: {RETURN_MATRIX_PATH}")

        df = pd.read_csv(RETURN_MATRIX_PATH)

        date_col = None
        for candidate in ["date", "Date", "timestamp", "Datetime", "datetime"]:
            if candidate in df.columns:
                date_col = candidate
                break

        if date_col:
            df[date_col] = pd.to_datetime(df[date_col])
            df = df.set_index(date_col).sort_index()

        numeric = df.select_dtypes(include=[np.number])

        if numeric.empty:
            raise ValueError("Return matrix has no numeric columns.")

        numeric = numeric.replace([np.inf, -np.inf], np.nan).dropna(how="all")
        numeric = numeric.fillna(0.0)

        return numeric

    def load_weights(self, assets: List[str]) -> Dict[str, float]:
        for path in WEIGHTS_CANDIDATES:
            if path.exists():
                weights = self.read_weight_file(path, assets)
                if weights:
                    print(f"[INFO] Using weights file: {path}")
                    return weights

        print("[WARN] No usable weights file found. Using equal weights.")
        equal = 1.0 / len(assets)
        return {asset: equal for asset in assets}

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
            if asset in assets:
                weights[asset] = float(row[weight_col])

        total = sum(abs(v) for v in weights.values())

        if total == 0:
            return {}

        return {asset: weight / total for asset, weight in weights.items()}

    def estimate_distribution(
        self,
        returns: pd.DataFrame,
        weights: Dict[str, float],
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        common_assets = [asset for asset in weights if asset in returns.columns]

        if not common_assets:
            raise ValueError("No overlap between portfolio weights and return matrix.")

        selected_returns = returns[common_assets]
        weight_vector = np.array([weights[asset] for asset in common_assets])

        mean_vector = selected_returns.mean().values
        covariance_matrix = selected_returns.cov().values

        return mean_vector, covariance_matrix, common_assets

    def simulate_paths(
        self,
        mean_vector: np.ndarray,
        covariance_matrix: np.ndarray,
        weights: Dict[str, float],
        assets: List[str],
    ) -> Tuple[np.ndarray, np.ndarray]:
        weight_vector = np.array([weights[asset] for asset in assets])

        simulated_asset_returns = np.random.multivariate_normal(
            mean=mean_vector,
            cov=covariance_matrix,
            size=(self.simulations, self.horizon_days),
        )

        simulated_portfolio_returns = simulated_asset_returns @ weight_vector

        equity_paths = np.cumprod(1.0 + simulated_portfolio_returns, axis=1)

        return simulated_portfolio_returns, equity_paths

    def max_drawdowns(self, equity_paths: np.ndarray) -> np.ndarray:
        running_max = np.maximum.accumulate(equity_paths, axis=1)
        drawdowns = equity_paths / running_max - 1.0
        return drawdowns.min(axis=1)

    def summarize(
        self,
        simulated_returns: np.ndarray,
        equity_paths: np.ndarray,
    ) -> MonteCarloSummary:
        cumulative_returns = equity_paths[:, -1] - 1.0
        max_drawdowns = self.max_drawdowns(equity_paths)

        annualized_vols = simulated_returns.std(axis=1) * np.sqrt(252)

        var_95 = float(np.quantile(cumulative_returns, 0.05))
        cvar_95 = float(cumulative_returns[cumulative_returns <= var_95].mean())

        probability_of_loss = float(np.mean(cumulative_returns < 0))
        probability_dd_10 = float(np.mean(max_drawdowns <= -0.10))
        probability_dd_20 = float(np.mean(max_drawdowns <= -0.20))
        probability_dd_30 = float(np.mean(max_drawdowns <= -0.30))

        expected_dd = float(np.mean(max_drawdowns))

        if probability_dd_30 > 0.10:
            survival_status = "FRAGILE"
        elif probability_dd_20 > 0.10:
            survival_status = "STRESSED"
        else:
            survival_status = "ROBUST"

        return MonteCarloSummary(
            simulations=self.simulations,
            horizon_days=self.horizon_days,
            expected_cumulative_return=float(np.mean(cumulative_returns)),
            median_cumulative_return=float(np.median(cumulative_returns)),
            worst_cumulative_return=float(np.min(cumulative_returns)),
            best_cumulative_return=float(np.max(cumulative_returns)),
            expected_annualized_volatility=float(np.mean(annualized_vols)),
            expected_max_drawdown=expected_dd,
            var_95=var_95,
            cvar_95=cvar_95,
            probability_of_loss=probability_of_loss,
            probability_drawdown_gt_10=probability_dd_10,
            probability_drawdown_gt_20=probability_dd_20,
            probability_drawdown_gt_30=probability_dd_30,
            survival_status=survival_status,
        )

    def write_outputs(
        self,
        summary: MonteCarloSummary,
        weights: Dict[str, float],
        assets: List[str],
        simulated_returns: np.ndarray,
        equity_paths: np.ndarray,
    ) -> None:
        summary_path = OUTPUT_DIR / "monte_carlo_summary.json"
        weights_path = OUTPUT_DIR / "monte_carlo_weights.json"
        paths_path = OUTPUT_DIR / "monte_carlo_equity_paths_sample.csv"
        returns_path = OUTPUT_DIR / "monte_carlo_terminal_returns.csv"
        txt_path = OUTPUT_DIR / "monte_carlo_report.txt"

        summary_path.write_text(
            json.dumps(asdict(summary), indent=2),
            encoding="utf-8",
        )

        weights_path.write_text(
            json.dumps(weights, indent=2),
            encoding="utf-8",
        )

        sample_paths = pd.DataFrame(equity_paths[:100])
        sample_paths.to_csv(paths_path, index=False)

        terminal_returns = pd.DataFrame(
            {
                "simulation_id": range(self.simulations),
                "terminal_return": equity_paths[:, -1] - 1.0,
                "max_drawdown": self.max_drawdowns(equity_paths),
            }
        )
        terminal_returns.to_csv(returns_path, index=False)

        lines = [
            "=" * 80,
            "AURUM MONTE CARLO DIGITAL TWIN LAB",
            "=" * 80,
            f"Simulations: {summary.simulations}",
            f"Horizon Days: {summary.horizon_days}",
            "",
            "Portfolio Assets Used:",
        ]

        for asset in assets:
            lines.append(f"  {asset}: {weights[asset]:.4f}")

        lines.extend(
            [
                "",
                "Simulation Results:",
                f"Expected Cumulative Return: {summary.expected_cumulative_return:.4f}",
                f"Median Cumulative Return: {summary.median_cumulative_return:.4f}",
                f"Worst Cumulative Return: {summary.worst_cumulative_return:.4f}",
                f"Best Cumulative Return: {summary.best_cumulative_return:.4f}",
                f"Expected Annualized Volatility: {summary.expected_annualized_volatility:.4f}",
                f"Expected Max Drawdown: {summary.expected_max_drawdown:.4f}",
                f"VaR 95: {summary.var_95:.4f}",
                f"CVaR 95: {summary.cvar_95:.4f}",
                f"Probability of Loss: {summary.probability_of_loss:.4f}",
                f"Probability Drawdown > 10%: {summary.probability_drawdown_gt_10:.4f}",
                f"Probability Drawdown > 20%: {summary.probability_drawdown_gt_20:.4f}",
                f"Probability Drawdown > 30%: {summary.probability_drawdown_gt_30:.4f}",
                f"Survival Status: {summary.survival_status}",
            ]
        )

        txt_path.write_text("\n".join(lines), encoding="utf-8")

    def run(self) -> MonteCarloSummary:
        returns = self.load_return_matrix()
        weights = self.load_weights(list(returns.columns))

        mean_vector, covariance_matrix, assets = self.estimate_distribution(
            returns=returns,
            weights=weights,
        )

        simulated_returns, equity_paths = self.simulate_paths(
            mean_vector=mean_vector,
            covariance_matrix=covariance_matrix,
            weights=weights,
            assets=assets,
        )

        summary = self.summarize(
            simulated_returns=simulated_returns,
            equity_paths=equity_paths,
        )

        self.write_outputs(
            summary=summary,
            weights=weights,
            assets=assets,
            simulated_returns=simulated_returns,
            equity_paths=equity_paths,
        )

        return summary

    def print_summary(self, summary: MonteCarloSummary) -> None:
        print("=" * 80)
        print("AURUM MONTE CARLO DIGITAL TWIN LAB")
        print("=" * 80)
        print(f"Simulations: {summary.simulations}")
        print(f"Horizon Days: {summary.horizon_days}")
        print("-" * 80)
        print(f"Expected Cumulative Return: {summary.expected_cumulative_return:.4f}")
        print(f"Median Cumulative Return: {summary.median_cumulative_return:.4f}")
        print(f"Worst Cumulative Return: {summary.worst_cumulative_return:.4f}")
        print(f"Best Cumulative Return: {summary.best_cumulative_return:.4f}")
        print(f"Expected Annualized Volatility: {summary.expected_annualized_volatility:.4f}")
        print(f"Expected Max Drawdown: {summary.expected_max_drawdown:.4f}")
        print(f"VaR 95: {summary.var_95:.4f}")
        print(f"CVaR 95: {summary.cvar_95:.4f}")
        print(f"Probability of Loss: {summary.probability_of_loss:.4f}")
        print(f"Probability Drawdown > 10%: {summary.probability_drawdown_gt_10:.4f}")
        print(f"Probability Drawdown > 20%: {summary.probability_drawdown_gt_20:.4f}")
        print(f"Probability Drawdown > 30%: {summary.probability_drawdown_gt_30:.4f}")
        print(f"Survival Status: {summary.survival_status}")


def main() -> None:
    lab = MonteCarloLab(
        simulations=10_000,
        horizon_days=252,
        random_seed=42,
    )
    summary = lab.run()
    lab.print_summary(summary)


if __name__ == "__main__":
    main()