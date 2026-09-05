# src/digital_twin/stress_testing_framework.py

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List

import pandas as pd


SCENARIO_LIBRARY_PATH = Path("results/scenarios/scenario_library.json")

WEIGHTS_CANDIDATES = [
    Path("data/optimization/meta_strategy_weights.csv"),
    Path("data/institutional/portfolio_weights.csv"),
    Path("data/optimization/risk_parity_weights.csv"),
    Path("data/optimization/min_variance_weights.csv"),
]

OUTPUT_DIR = Path("results/digital_twin/stress_testing")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class StressTestResult:
    scenario_id: str
    category: str
    name: str
    severity: str
    portfolio_impact: float
    impacted_assets: int
    gross_shock_exposure: float
    survival_status: str
    governance_action: str


class StressTestingFramework:
    def load_scenarios(self) -> List[Dict]:
        if not SCENARIO_LIBRARY_PATH.exists():
            raise FileNotFoundError(
                f"Missing scenario library: {SCENARIO_LIBRARY_PATH}. "
                "Run python -m src.scenarios.scenario_library first."
            )

        return json.loads(SCENARIO_LIBRARY_PATH.read_text(encoding="utf-8"))

    def load_weights(self) -> Dict[str, float]:
        for path in WEIGHTS_CANDIDATES:
            if path.exists():
                weights = self.read_weight_file(path)
                if weights:
                    print(f"[INFO] Using weights file: {path}")
                    return weights

        raise FileNotFoundError("No usable portfolio weights file found.")

    def read_weight_file(self, path: Path) -> Dict[str, float]:
        df = pd.read_csv(path)

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
            weights[asset] = weight

        total = sum(abs(v) for v in weights.values())

        if total == 0:
            return {}

        return {asset: weight / total for asset, weight in weights.items()}

    def classify_survival(self, impact: float) -> str:
        if impact <= -0.30:
            return "FAILED"
        if impact <= -0.15:
            return "SEVERELY_STRESSED"
        if impact <= -0.05:
            return "STRESSED"
        return "SURVIVED"

    def governance_action(self, impact: float) -> str:
        if impact <= -0.30:
            return "FORCE_DE_RISK_AND_ESCALATE"
        if impact <= -0.15:
            return "CUT_EXPOSURE_AND_TRIGGER_COMMITTEE_REVIEW"
        if impact <= -0.05:
            return "TIGHTEN_LIMITS_AND_MONITOR"
        return "NO_ACTION_REQUIRED"

    def evaluate_scenario(
        self,
        scenario: Dict,
        weights: Dict[str, float],
    ) -> StressTestResult:
        shocks = scenario.get("shocks", {})

        portfolio_impact = 0.0
        impacted_assets = 0
        gross_shock_exposure = 0.0

        for asset, shock in shocks.items():
            if asset in weights:
                weight = weights[asset]
                portfolio_impact += weight * float(shock)
                gross_shock_exposure += abs(weight * float(shock))
                impacted_assets += 1

        return StressTestResult(
            scenario_id=scenario["scenario_id"],
            category=scenario["category"],
            name=scenario["name"],
            severity=scenario["severity"],
            portfolio_impact=portfolio_impact,
            impacted_assets=impacted_assets,
            gross_shock_exposure=gross_shock_exposure,
            survival_status=self.classify_survival(portfolio_impact),
            governance_action=self.governance_action(portfolio_impact),
        )

    def run(self) -> List[StressTestResult]:
        scenarios = self.load_scenarios()
        weights = self.load_weights()

        results = [
            self.evaluate_scenario(
                scenario=scenario,
                weights=weights,
            )
            for scenario in scenarios
        ]

        self.write_outputs(results, weights)
        return results

    def write_outputs(
        self,
        results: List[StressTestResult],
        weights: Dict[str, float],
    ) -> None:
        records = [asdict(result) for result in results]

        json_path = OUTPUT_DIR / "stress_test_results.json"
        csv_path = OUTPUT_DIR / "stress_test_results.csv"
        txt_path = OUTPUT_DIR / "stress_test_report.txt"
        weights_path = OUTPUT_DIR / "stress_test_weights.json"

        json_path.write_text(json.dumps(records, indent=2), encoding="utf-8")
        weights_path.write_text(json.dumps(weights, indent=2), encoding="utf-8")
        pd.DataFrame(records).to_csv(csv_path, index=False)

        sorted_results = sorted(results, key=lambda x: x.portfolio_impact)

        worst = sorted_results[0]
        best = sorted_results[-1]

        lines = [
            "=" * 80,
            "AURUM DIGITAL TWIN STRESS TESTING FRAMEWORK",
            "=" * 80,
            "",
            "Portfolio Weights Used:",
        ]

        for asset, weight in weights.items():
            lines.append(f"  {asset}: {weight:.4f}")

        lines.extend(
            [
                "",
                "Summary:",
                f"Worst Scenario: {worst.scenario_id} impact={worst.portfolio_impact:.4f}",
                f"Best Scenario: {best.scenario_id} impact={best.portfolio_impact:.4f}",
                "",
                "-" * 80,
            ]
        )

        for result in sorted_results:
            lines.extend(
                [
                    f"Scenario: {result.scenario_id}",
                    f"Category: {result.category}",
                    f"Name: {result.name}",
                    f"Severity: {result.severity}",
                    f"Portfolio Impact: {result.portfolio_impact:.4f}",
                    f"Impacted Assets: {result.impacted_assets}",
                    f"Gross Shock Exposure: {result.gross_shock_exposure:.4f}",
                    f"Survival Status: {result.survival_status}",
                    f"Governance Action: {result.governance_action}",
                    "-" * 80,
                ]
            )

        txt_path.write_text("\n".join(lines), encoding="utf-8")

    def print_results(self, results: List[StressTestResult]) -> None:
        print("=" * 80)
        print("AURUM DIGITAL TWIN STRESS TESTING FRAMEWORK")
        print("=" * 80)

        sorted_results = sorted(results, key=lambda x: x.portfolio_impact)

        for result in sorted_results:
            print(
                f"{result.scenario_id:<25} "
                f"impact={result.portfolio_impact:>8.4f} "
                f"status={result.survival_status:<18} "
                f"action={result.governance_action}"
            )

        worst = sorted_results[0]
        best = sorted_results[-1]

        print("-" * 80)
        print(f"Worst Scenario: {worst.scenario_id} | impact={worst.portfolio_impact:.4f}")
        print(f"Best Scenario:  {best.scenario_id} | impact={best.portfolio_impact:.4f}")


def main() -> None:
    framework = StressTestingFramework()
    results = framework.run()
    framework.print_results(results)


if __name__ == "__main__":
    main()