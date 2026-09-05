# src/scenarios/scenario_library.py

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List


OUTPUT_DIR = Path("results/scenarios")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class Scenario:
    scenario_id: str
    category: str
    name: str
    description: str
    shocks: Dict[str, float]
    severity: str


class ScenarioLibrary:
    def __init__(self) -> None:
        self.scenarios = self.build_library()

    def build_library(self) -> List[Scenario]:

        return [

            # =====================================================
            # EQUITY SHOCKS
            # =====================================================

            Scenario(
                scenario_id="SPY_MINUS_15",
                category="equity",
                name="Equity Correction",
                description="Broad equity selloff.",
                shocks={
                    "SPY": -0.15,
                    "QQQ": -0.18,
                    "DIA": -0.12,
                },
                severity="moderate",
            ),

            Scenario(
                scenario_id="SPY_MINUS_30",
                category="equity",
                name="Equity Crash",
                description="Major equity market crash.",
                shocks={
                    "SPY": -0.30,
                    "QQQ": -0.35,
                    "DIA": -0.28,
                },
                severity="severe",
            ),

            # =====================================================
            # RATES
            # =====================================================

            Scenario(
                scenario_id="FED_PLUS_100_BPS",
                category="rates",
                name="Fed +100bps",
                description="Unexpected rate hike.",
                shocks={
                    "TLT": -0.12,
                    "SPY": -0.06,
                    "QQQ": -0.09,
                },
                severity="moderate",
            ),

            Scenario(
                scenario_id="FED_PLUS_200_BPS",
                category="rates",
                name="Aggressive Rate Shock",
                description="Large policy tightening shock.",
                shocks={
                    "TLT": -0.22,
                    "SPY": -0.15,
                    "QQQ": -0.20,
                },
                severity="severe",
            ),

            # =====================================================
            # CRYPTO
            # =====================================================

            Scenario(
                scenario_id="CRYPTO_CRASH",
                category="crypto",
                name="Crypto Crash",
                description="Digital asset collapse.",
                shocks={
                    "BTC-USD": -0.45,
                    "ETH-USD": -0.55,
                },
                severity="severe",
            ),

            # =====================================================
            # AI BUBBLE
            # =====================================================

            Scenario(
                scenario_id="AI_BUBBLE_BURST",
                category="technology",
                name="AI Bubble Burst",
                description="High-growth technology repricing.",
                shocks={
                    "QQQ": -0.25,
                    "SPY": -0.12,
                },
                severity="severe",
            ),

            # =====================================================
            # COMMODITIES
            # =====================================================

            Scenario(
                scenario_id="OIL_PLUS_40",
                category="commodity",
                name="Oil Shock",
                description="Oil prices surge 40%.",
                shocks={
                    "SPY": -0.08,
                    "QQQ": -0.10,
                    "GLD": 0.05,
                },
                severity="moderate",
            ),

            Scenario(
                scenario_id="GOLD_FLIGHT_TO_SAFETY",
                category="commodity",
                name="Flight To Safety",
                description="Risk-off movement into gold.",
                shocks={
                    "GLD": 0.15,
                    "SPY": -0.10,
                    "QQQ": -0.12,
                },
                severity="moderate",
            ),

            # =====================================================
            # LIQUIDITY
            # =====================================================

            Scenario(
                scenario_id="LIQUIDITY_CRISIS",
                category="liquidity",
                name="Liquidity Crisis",
                description="Volume collapse and widening spreads.",
                shocks={
                    "SPY": -0.20,
                    "QQQ": -0.25,
                    "DIA": -0.18,
                    "TLT": 0.05,
                    "GLD": 0.08,
                },
                severity="extreme",
            ),

            # =====================================================
            # VOLATILITY
            # =====================================================

            Scenario(
                scenario_id="VOLATILITY_SPIKE",
                category="volatility",
                name="Volatility Spike",
                description="Risk-off volatility shock.",
                shocks={
                    "VIX": 1.00,
                    "SPY": -0.12,
                    "QQQ": -0.15,
                },
                severity="moderate",
            ),

            # =====================================================
            # SYSTEMIC
            # =====================================================

            Scenario(
                scenario_id="GLOBAL_CONTAGION",
                category="systemic",
                name="Global Contagion Event",
                description="Cross-asset risk event.",
                shocks={
                    "SPY": -0.35,
                    "QQQ": -0.40,
                    "DIA": -0.30,
                    "BTC-USD": -0.50,
                    "ETH-USD": -0.60,
                    "TLT": 0.08,
                    "GLD": 0.12,
                },
                severity="extreme",
            ),
        ]

    def save(self) -> None:

        scenarios = [asdict(x) for x in self.scenarios]

        json_path = OUTPUT_DIR / "scenario_library.json"
        csv_path = OUTPUT_DIR / "scenario_library.csv"

        json_path.write_text(
            json.dumps(scenarios, indent=2),
            encoding="utf-8",
        )

        import pandas as pd

        pd.DataFrame(scenarios).to_csv(csv_path, index=False)

        return json_path, csv_path

    def print_summary(self) -> None:

        print("=" * 80)
        print("AURUM SCENARIO LIBRARY")
        print("=" * 80)

        print(f"Total Scenarios: {len(self.scenarios)}")

        categories = {}

        for scenario in self.scenarios:
            categories.setdefault(
                scenario.category,
                0,
            )
            categories[scenario.category] += 1

        print("\nCategory Breakdown")

        for category, count in categories.items():
            print(f"  {category:<15} {count}")

        print("\nScenario IDs")

        for scenario in self.scenarios:
            print(f"  {scenario.scenario_id}")

    def run(self) -> None:
        self.save()
        self.print_summary()


def main() -> None:
    ScenarioLibrary().run()


if __name__ == "__main__":
    main()