# src/digital_twin/contagion_engine.py

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

OUTPUT_DIR = Path("results/digital_twin/contagion_engine")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class ContagionResult:
    source_asset: str
    initial_shock: float
    total_portfolio_impact: float
    direct_portfolio_impact: float
    propagated_portfolio_impact: float
    most_impacted_asset: str
    most_impacted_asset_return: float
    network_stress_level: str
    governance_action: str


class ContagionEngine:
    def __init__(
        self,
        initial_shock: float = -0.20,
        propagation_strength: float = 0.65,
        correlation_threshold: float = 0.25,
    ) -> None:
        self.initial_shock = initial_shock
        self.propagation_strength = propagation_strength
        self.correlation_threshold = correlation_threshold

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
        numeric = numeric.replace([np.inf, -np.inf], np.nan).dropna(how="all")
        numeric = numeric.fillna(0.0)

        if numeric.empty:
            raise ValueError("No numeric return columns found.")

        return numeric

    def load_weights(self, assets: List[str]) -> Dict[str, float]:
        for path in WEIGHTS_CANDIDATES:
            if path.exists():
                weights = self.read_weight_file(path, assets)
                if weights:
                    print(f"[INFO] Using weights file: {path}")
                    return weights

        print("[WARN] No usable weights found. Using equal weights.")
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

    def build_network(self, returns: pd.DataFrame) -> pd.DataFrame:
        corr = returns.corr().fillna(0.0)

        adjacency = corr.copy()

        for row in adjacency.index:
            for col in adjacency.columns:
                if row == col:
                    adjacency.loc[row, col] = 0.0
                elif abs(adjacency.loc[row, col]) < self.correlation_threshold:
                    adjacency.loc[row, col] = 0.0

        return adjacency

    def propagate_shock(
        self,
        source_asset: str,
        adjacency: pd.DataFrame,
    ) -> Dict[str, float]:
        assets = list(adjacency.columns)

        shock_vector = {asset: 0.0 for asset in assets}
        shock_vector[source_asset] = self.initial_shock

        for target in assets:
            if target == source_asset:
                continue

            connection = adjacency.loc[source_asset, target]

            if connection == 0:
                continue

            propagated = self.initial_shock * abs(connection) * self.propagation_strength
            shock_vector[target] += propagated

        second_round = shock_vector.copy()

        for intermediate in assets:
            if intermediate == source_asset:
                continue

            intermediate_shock = shock_vector[intermediate]

            if intermediate_shock == 0:
                continue

            for target in assets:
                if target in {source_asset, intermediate}:
                    continue

                connection = adjacency.loc[intermediate, target]

                if connection == 0:
                    continue

                second_round[target] += (
                    intermediate_shock
                    * abs(connection)
                    * self.propagation_strength
                    * 0.50
                )

        return second_round

    def classify_stress(self, impact: float) -> str:
        if impact <= -0.25:
            return "SYSTEMIC_FAILURE_RISK"
        if impact <= -0.15:
            return "HIGH_CONTAGION_STRESS"
        if impact <= -0.05:
            return "MODERATE_CONTAGION_STRESS"
        return "CONTAINED"

    def governance_action(self, impact: float) -> str:
        if impact <= -0.25:
            return "FORCE_DE_RISK_ESCALATE_AND_FREEZE_NEW_RISK"
        if impact <= -0.15:
            return "CUT_EXPOSURE_AND_TRIGGER_CONTAGION_REVIEW"
        if impact <= -0.05:
            return "TIGHTEN_LIMITS_AND_MONITOR_NETWORK"
        return "NO_ACTION_REQUIRED"

    def evaluate_source(
        self,
        source_asset: str,
        adjacency: pd.DataFrame,
        weights: Dict[str, float],
    ) -> ContagionResult:
        shock_vector = self.propagate_shock(
            source_asset=source_asset,
            adjacency=adjacency,
        )

        total_impact = 0.0
        direct_impact = 0.0
        propagated_impact = 0.0

        for asset, shock in shock_vector.items():
            weight = weights.get(asset, 0.0)
            contribution = weight * shock
            total_impact += contribution

            if asset == source_asset:
                direct_impact += contribution
            else:
                propagated_impact += contribution

        most_impacted_asset = min(shock_vector, key=shock_vector.get)
        most_impacted_asset_return = shock_vector[most_impacted_asset]

        return ContagionResult(
            source_asset=source_asset,
            initial_shock=self.initial_shock,
            total_portfolio_impact=total_impact,
            direct_portfolio_impact=direct_impact,
            propagated_portfolio_impact=propagated_impact,
            most_impacted_asset=most_impacted_asset,
            most_impacted_asset_return=most_impacted_asset_return,
            network_stress_level=self.classify_stress(total_impact),
            governance_action=self.governance_action(total_impact),
        )

    def run(self) -> List[ContagionResult]:
        returns = self.load_return_matrix()
        assets = list(returns.columns)

        weights = self.load_weights(assets)
        adjacency = self.build_network(returns)

        results = [
            self.evaluate_source(
                source_asset=asset,
                adjacency=adjacency,
                weights=weights,
            )
            for asset in assets
        ]

        self.write_outputs(results, weights, adjacency)
        return results

    def write_outputs(
        self,
        results: List[ContagionResult],
        weights: Dict[str, float],
        adjacency: pd.DataFrame,
    ) -> None:
        records = [asdict(result) for result in results]

        json_path = OUTPUT_DIR / "contagion_results.json"
        csv_path = OUTPUT_DIR / "contagion_results.csv"
        network_path = OUTPUT_DIR / "market_network_adjacency.csv"
        weights_path = OUTPUT_DIR / "contagion_weights.json"
        txt_path = OUTPUT_DIR / "contagion_report.txt"

        json_path.write_text(json.dumps(records, indent=2), encoding="utf-8")
        pd.DataFrame(records).to_csv(csv_path, index=False)
        adjacency.to_csv(network_path)
        weights_path.write_text(json.dumps(weights, indent=2), encoding="utf-8")

        sorted_results = sorted(results, key=lambda x: x.total_portfolio_impact)
        worst = sorted_results[0]

        lines = [
            "=" * 80,
            "AURUM MARKET CONTAGION ENGINE",
            "=" * 80,
            "",
            f"Initial Shock Per Source Asset: {self.initial_shock:.2%}",
            f"Propagation Strength: {self.propagation_strength:.2f}",
            f"Correlation Threshold: {self.correlation_threshold:.2f}",
            "",
            "Worst Contagion Source:",
            f"  Asset: {worst.source_asset}",
            f"  Total Portfolio Impact: {worst.total_portfolio_impact:.4f}",
            f"  Direct Impact: {worst.direct_portfolio_impact:.4f}",
            f"  Propagated Impact: {worst.propagated_portfolio_impact:.4f}",
            f"  Stress Level: {worst.network_stress_level}",
            f"  Governance Action: {worst.governance_action}",
            "",
            "-" * 80,
        ]

        for result in sorted_results:
            lines.extend(
                [
                    f"Source Asset: {result.source_asset}",
                    f"Total Portfolio Impact: {result.total_portfolio_impact:.4f}",
                    f"Direct Portfolio Impact: {result.direct_portfolio_impact:.4f}",
                    f"Propagated Portfolio Impact: {result.propagated_portfolio_impact:.4f}",
                    f"Most Impacted Asset: {result.most_impacted_asset}",
                    f"Most Impacted Asset Return: {result.most_impacted_asset_return:.4f}",
                    f"Network Stress Level: {result.network_stress_level}",
                    f"Governance Action: {result.governance_action}",
                    "-" * 80,
                ]
            )

        txt_path.write_text("\n".join(lines), encoding="utf-8")

    def print_results(self, results: List[ContagionResult]) -> None:
        print("=" * 80)
        print("AURUM MARKET CONTAGION ENGINE")
        print("=" * 80)

        sorted_results = sorted(results, key=lambda x: x.total_portfolio_impact)

        for result in sorted_results:
            print(
                f"{result.source_asset:<12} "
                f"total={result.total_portfolio_impact:>8.4f} "
                f"direct={result.direct_portfolio_impact:>8.4f} "
                f"propagated={result.propagated_portfolio_impact:>8.4f} "
                f"stress={result.network_stress_level}"
            )

        worst = sorted_results[0]

        print("-" * 80)
        print(f"Worst Contagion Source: {worst.source_asset}")
        print(f"Total Portfolio Impact: {worst.total_portfolio_impact:.4f}")
        print(f"Governance Action: {worst.governance_action}")


def main() -> None:
    engine = ContagionEngine(
        initial_shock=-0.20,
        propagation_strength=0.65,
        correlation_threshold=0.25,
    )
    results = engine.run()
    engine.print_results(results)


if __name__ == "__main__":
    main()