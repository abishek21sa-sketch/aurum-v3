from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List
import json


RESULTS_DIR = Path("results/intelligence")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class CrossAssetIntelligenceEngine:
    def __init__(self) -> None:
        self.relationships = [
            {
                "source_asset_class": "rates",
                "target_asset_class": "equities",
                "relationship": "higher_rates_pressure_equity_valuations",
                "direction": "negative",
                "economic_logic": "Rising yields increase discount rates and can pressure growth-sensitive equities.",
                "sensitivity": "high",
            },
            {
                "source_asset_class": "rates",
                "target_asset_class": "growth_equities",
                "relationship": "front_end_rates_pressure_growth_assets",
                "direction": "negative",
                "economic_logic": "Higher short-term yields reduce the present value of long-duration growth cash flows.",
                "sensitivity": "high",
            },
            {
                "source_asset_class": "commodities",
                "target_asset_class": "inflation",
                "relationship": "oil_and_commodity_prices_raise_inflation_pressure",
                "direction": "positive",
                "economic_logic": "Rising energy and raw material prices can increase inflation expectations.",
                "sensitivity": "medium",
            },
            {
                "source_asset_class": "fx",
                "target_asset_class": "commodities",
                "relationship": "strong_usd_pressures_commodities",
                "direction": "negative",
                "economic_logic": "A stronger dollar can pressure USD-denominated commodities.",
                "sensitivity": "medium",
            },
            {
                "source_asset_class": "volatility",
                "target_asset_class": "equities",
                "relationship": "higher_volatility_pressures_risk_assets",
                "direction": "negative",
                "economic_logic": "Rising volatility typically indicates risk aversion and can pressure equities.",
                "sensitivity": "high",
            },
            {
                "source_asset_class": "volatility",
                "target_asset_class": "crypto",
                "relationship": "higher_volatility_pressures_speculative_assets",
                "direction": "negative",
                "economic_logic": "Crypto often behaves like a high-beta liquidity-sensitive asset during stress.",
                "sensitivity": "high",
            },
            {
                "source_asset_class": "equities",
                "target_asset_class": "crypto",
                "relationship": "growth_risk_appetite_supports_crypto",
                "direction": "positive",
                "economic_logic": "Strong growth-equity appetite can support speculative risk assets.",
                "sensitivity": "medium",
            },
            {
                "source_asset_class": "rates",
                "target_asset_class": "gold",
                "relationship": "real_yields_pressure_gold",
                "direction": "negative",
                "economic_logic": "Higher real yields increase opportunity cost of holding gold.",
                "sensitivity": "medium",
            },
            {
                "source_asset_class": "fx",
                "target_asset_class": "emerging_markets",
                "relationship": "strong_usd_pressures_em_assets",
                "direction": "negative",
                "economic_logic": "A strong dollar can tighten financial conditions for emerging markets.",
                "sensitivity": "medium",
            },
            {
                "source_asset_class": "commodities",
                "target_asset_class": "commodity_fx",
                "relationship": "higher_oil_supports_commodity_currencies",
                "direction": "positive",
                "economic_logic": "Commodity-linked currencies can benefit when export commodities rise.",
                "sensitivity": "medium",
            },
        ]

    def dependency_report(self) -> Dict:
        return {
            "timestamp": utc_now(),
            "engine": "cross_asset_intelligence_engine",
            "relationship_count": len(self.relationships),
            "relationships": self.relationships,
        }

    def summary(self) -> Dict:
        by_source: Dict[str, int] = {}
        by_sensitivity: Dict[str, int] = {}
        negative = 0
        positive = 0

        for rel in self.relationships:
            by_source[rel["source_asset_class"]] = by_source.get(rel["source_asset_class"], 0) + 1
            by_sensitivity[rel["sensitivity"]] = by_sensitivity.get(rel["sensitivity"], 0) + 1

            if rel["direction"] == "negative":
                negative += 1
            elif rel["direction"] == "positive":
                positive += 1

        return {
            "timestamp": utc_now(),
            "engine": "cross_asset_intelligence_engine",
            "relationship_count": len(self.relationships),
            "source_asset_class_counts": by_source,
            "sensitivity_counts": by_sensitivity,
            "direction_counts": {
                "positive": positive,
                "negative": negative,
            },
            "institutional_interpretation": (
                "AURUM now has a structured cross-asset dependency map linking rates, "
                "equities, commodities, FX, volatility, crypto, gold, and emerging markets."
            ),
        }

    def run(self) -> Dict:
        report = self.dependency_report()
        summary = self.summary()

        (RESULTS_DIR / "cross_asset_dependency_report.json").write_text(
            json.dumps(report, indent=2),
            encoding="utf-8",
        )

        (RESULTS_DIR / "cross_asset_summary.json").write_text(
            json.dumps(summary, indent=2),
            encoding="utf-8",
        )

        return summary


def main() -> None:
    summary = CrossAssetIntelligenceEngine().run()

    print("=" * 80)
    print("AURUM PHASE 6B.2 CROSS-ASSET INTELLIGENCE ENGINE")
    print("=" * 80)
    print(f"Relationships: {summary['relationship_count']}")
    print(f"Sources:       {', '.join(sorted(summary['source_asset_class_counts'].keys()))}")
    print(f"Direction:     {summary['direction_counts']}")
    print(f"Sensitivity:   {summary['sensitivity_counts']}")
    print("-" * 80)
    print(summary["institutional_interpretation"])
    print("=" * 80)


if __name__ == "__main__":
    main()