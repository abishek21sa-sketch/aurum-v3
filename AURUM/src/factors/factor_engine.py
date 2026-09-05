from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List
import json


RESULTS_DIR = Path("results/factors")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class InstitutionalFactorEngine:
    def __init__(self) -> None:
        self.factor_definitions = [
            {
                "factor": "value",
                "description": "Assets that appear inexpensive relative to fundamentals.",
                "economic_logic": "Value strategies seek compensation for owning underpriced or neglected assets.",
                "expected_behavior": "Can outperform during reflation, recovery, and mean-reversion regimes.",
                "risk": "Can underperform during growth-led markets or value traps.",
            },
            {
                "factor": "momentum",
                "description": "Assets with strong recent relative performance.",
                "economic_logic": "Momentum captures persistence in trends and investor underreaction.",
                "expected_behavior": "Can outperform in strong trending markets.",
                "risk": "Can reverse sharply during regime shifts.",
            },
            {
                "factor": "quality",
                "description": "Assets with strong balance sheets, profitability, and stability.",
                "economic_logic": "Quality seeks durable fundamentals and resilience.",
                "expected_behavior": "Can outperform during stress and late-cycle environments.",
                "risk": "Can lag during speculative rallies.",
            },
            {
                "factor": "growth",
                "description": "Assets with high expected earnings or revenue growth.",
                "economic_logic": "Growth captures long-duration earnings expectations.",
                "expected_behavior": "Can outperform when rates are stable or falling and risk appetite is strong.",
                "risk": "Sensitive to rising rates and valuation compression.",
            },
            {
                "factor": "carry",
                "description": "Assets that provide positive yield, roll-down, or income.",
                "economic_logic": "Carry earns return from holding assets with positive expected income.",
                "expected_behavior": "Can perform well in calm, stable regimes.",
                "risk": "Can suffer during volatility spikes and funding stress.",
            },
            {
                "factor": "low_volatility",
                "description": "Assets with lower realized volatility and defensive characteristics.",
                "economic_logic": "Low volatility seeks smoother returns and downside protection.",
                "expected_behavior": "Can outperform during defensive or stressed regimes.",
                "risk": "Can lag during aggressive risk-on rallies.",
            },
        ]

        self.factor_asset_map = {
            "value": ["DIA", "EFA", "EEM", "DBC"],
            "momentum": ["QQQ", "SPY", "BTC-USD", "ETH-USD"],
            "quality": ["SPY", "DIA", "GLD"],
            "growth": ["QQQ", "IWM", "BTC-USD", "ETH-USD"],
            "carry": ["SHY", "IEF", "USDCAD", "DBC"],
            "low_volatility": ["TLT", "IEF", "SHY", "GLD", "VIX"],
        }

        self.regime_factor_preferences = {
            "risk_on": ["momentum", "growth"],
            "normal": ["quality", "momentum", "carry"],
            "inflationary": ["value", "carry"],
            "defensive": ["quality", "low_volatility"],
            "crisis": ["low_volatility", "quality"],
        }

    def definitions(self) -> Dict:
        return {
            "timestamp": utc_now(),
            "engine": "institutional_factor_engine",
            "factor_count": len(self.factor_definitions),
            "factors": self.factor_definitions,
        }

    def attribution_report(self) -> Dict:
        rows = []

        for factor, assets in self.factor_asset_map.items():
            rows.append(
                {
                    "factor": factor,
                    "asset_count": len(assets),
                    "assets": assets,
                    "interpretation": f"{factor} exposure is represented by {len(assets)} assets in the current universe.",
                }
            )

        return {
            "timestamp": utc_now(),
            "engine": "institutional_factor_engine",
            "factor_attribution": rows,
        }

    def rotation_signal(self, regime: str = "normal") -> Dict:
        preferred = self.regime_factor_preferences.get(regime, ["quality", "momentum"])

        avoid = []
        if regime in {"defensive", "crisis"}:
            avoid = ["growth", "momentum"]
        elif regime == "inflationary":
            avoid = ["growth", "long_duration"]
        elif regime == "risk_on":
            avoid = ["low_volatility"]

        return {
            "timestamp": utc_now(),
            "engine": "institutional_factor_engine",
            "regime": regime,
            "preferred_factors": preferred,
            "avoid_factors": avoid,
            "factor_posture": self._factor_posture(preferred, avoid),
            "interpretation": (
                f"In a {regime} regime, AURUM prefers {', '.join(preferred)} "
                f"and monitors risks from {', '.join(avoid) if avoid else 'no major avoided factors'}."
            ),
        }

    def _factor_posture(self, preferred: List[str], avoid: List[str]) -> str:
        if "low_volatility" in preferred:
            return "defensive_factor_posture"
        if "growth" in preferred or "momentum" in preferred:
            return "pro_risk_factor_posture"
        if "carry" in preferred:
            return "income_oriented_factor_posture"
        return "balanced_factor_posture"

    def run(self, regime: str = "normal") -> Dict:
        definitions = self.definitions()
        attribution = self.attribution_report()
        rotation = self.rotation_signal(regime=regime)

        (RESULTS_DIR / "factor_definitions.json").write_text(
            json.dumps(definitions, indent=2),
            encoding="utf-8",
        )

        (RESULTS_DIR / "factor_attribution_report.json").write_text(
            json.dumps(attribution, indent=2),
            encoding="utf-8",
        )

        (RESULTS_DIR / "factor_rotation_signal.json").write_text(
            json.dumps(rotation, indent=2),
            encoding="utf-8",
        )

        return {
            "definitions": definitions,
            "attribution": attribution,
            "rotation": rotation,
        }


def main() -> None:
    result = InstitutionalFactorEngine().run(regime="normal")
    rotation = result["rotation"]

    print("=" * 80)
    print("AURUM PHASE 6B.3 INSTITUTIONAL FACTOR PLATFORM")
    print("=" * 80)
    print(f"Factors:            {result['definitions']['factor_count']}")
    print(f"Regime:             {rotation['regime']}")
    print(f"Preferred Factors:  {', '.join(rotation['preferred_factors'])}")
    print(f"Avoid Factors:      {', '.join(rotation['avoid_factors']) if rotation['avoid_factors'] else 'None'}")
    print(f"Posture:            {rotation['factor_posture']}")
    print("-" * 80)
    print(rotation["interpretation"])
    print("=" * 80)


if __name__ == "__main__":
    main()