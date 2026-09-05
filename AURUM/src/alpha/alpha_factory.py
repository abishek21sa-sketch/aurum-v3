from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List
import json


RESULTS_DIR = Path("results/alpha")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AlphaFactory:
    def __init__(self) -> None:
        self.alpha_ideas = [
            {
                "alpha_id": "ALPHA_MOMENTUM_001",
                "name": "Cross-Asset Momentum",
                "category": "momentum",
                "description": "Rank assets by recent trend strength and favor persistent winners.",
                "universe": ["SPY", "QQQ", "IWM", "EFA", "EEM", "BTC-USD", "ETH-USD"],
                "hypothesis": "Assets with strong recent relative performance continue to outperform over short horizons.",
            },
            {
                "alpha_id": "ALPHA_RATES_001",
                "name": "Rates Pressure Equity Risk",
                "category": "macro",
                "description": "Reduce growth equity exposure when rates pressure rises.",
                "universe": ["QQQ", "TLT", "IEF", "US10Y", "US2Y"],
                "hypothesis": "Rising rates pressure long-duration growth assets.",
            },
            {
                "alpha_id": "ALPHA_VOL_001",
                "name": "Volatility Risk-Off Signal",
                "category": "risk",
                "description": "Shift defensive when volatility rises sharply.",
                "universe": ["VIX", "SPY", "QQQ", "TLT", "GLD"],
                "hypothesis": "Volatility spikes reduce risk appetite and favor defensive assets.",
            },
            {
                "alpha_id": "ALPHA_COMMODITY_001",
                "name": "Commodity Inflation Rotation",
                "category": "inflation",
                "description": "Favor commodities and value assets during commodity strength.",
                "universe": ["DBC", "GLD", "SLV", "WTI", "COPPER", "DIA", "EEM"],
                "hypothesis": "Commodity strength can signal inflationary pressure and support real assets.",
            },
            {
                "alpha_id": "ALPHA_FX_001",
                "name": "Dollar Strength Stress Signal",
                "category": "fx_macro",
                "description": "Identify stress in commodities and EM assets during dollar strength.",
                "universe": ["EURUSD", "USDJPY", "USDCAD", "EEM", "DBC", "GLD"],
                "hypothesis": "Strong USD tightens global financial conditions and pressures EM and commodities.",
            },
            {
                "alpha_id": "ALPHA_QUALITY_001",
                "name": "Quality Defensive Rotation",
                "category": "quality",
                "description": "Favor quality and low-volatility assets when risk conditions deteriorate.",
                "universe": ["SPY", "DIA", "GLD", "TLT", "IEF", "SHY"],
                "hypothesis": "Quality and defensive assets outperform during stress regimes.",
            },
        ]

    def simulate_backtest_metrics(self, alpha: Dict) -> Dict:
        base_metrics = {
            "momentum": {
                "sharpe": 1.35,
                "cvar": 0.115,
                "max_drawdown": 0.145,
                "consistency": 0.72,
            },
            "macro": {
                "sharpe": 1.18,
                "cvar": 0.102,
                "max_drawdown": 0.130,
                "consistency": 0.68,
            },
            "risk": {
                "sharpe": 1.05,
                "cvar": 0.075,
                "max_drawdown": 0.090,
                "consistency": 0.76,
            },
            "inflation": {
                "sharpe": 0.98,
                "cvar": 0.120,
                "max_drawdown": 0.155,
                "consistency": 0.61,
            },
            "fx_macro": {
                "sharpe": 0.92,
                "cvar": 0.105,
                "max_drawdown": 0.135,
                "consistency": 0.59,
            },
            "quality": {
                "sharpe": 1.12,
                "cvar": 0.080,
                "max_drawdown": 0.100,
                "consistency": 0.74,
            },
        }

        return base_metrics.get(
            alpha["category"],
            {
                "sharpe": 0.80,
                "cvar": 0.140,
                "max_drawdown": 0.180,
                "consistency": 0.50,
            },
        )

    def score_alpha(self, metrics: Dict) -> float:
        sharpe_score = min(metrics["sharpe"] / 2.0, 1.0) * 40
        cvar_score = max(1.0 - metrics["cvar"], 0.0) * 20
        drawdown_score = max(1.0 - metrics["max_drawdown"], 0.0) * 20
        consistency_score = metrics["consistency"] * 20

        return round(
            sharpe_score + cvar_score + drawdown_score + consistency_score,
            2,
        )

    def generate_registry(self) -> Dict:
        registry = []

        for alpha in self.alpha_ideas:
            metrics = self.simulate_backtest_metrics(alpha)
            score = self.score_alpha(metrics)

            registry.append(
                {
                    **alpha,
                    "status": "research_candidate",
                    "metrics": metrics,
                    "alpha_score": score,
                }
            )

        return {
            "timestamp": utc_now(),
            "factory": "aurum_alpha_research_factory",
            "alpha_count": len(registry),
            "alphas": registry,
        }

    def scorecard(self, registry: Dict) -> Dict:
        rows = []

        for alpha in registry["alphas"]:
            rows.append(
                {
                    "alpha_id": alpha["alpha_id"],
                    "name": alpha["name"],
                    "category": alpha["category"],
                    "alpha_score": alpha["alpha_score"],
                    "sharpe": alpha["metrics"]["sharpe"],
                    "cvar": alpha["metrics"]["cvar"],
                    "max_drawdown": alpha["metrics"]["max_drawdown"],
                    "consistency": alpha["metrics"]["consistency"],
                    "status": alpha["status"],
                }
            )

        return {
            "timestamp": utc_now(),
            "scorecard": sorted(rows, key=lambda x: x["alpha_score"], reverse=True),
        }

    def rankings(self, scorecard: Dict) -> Dict:
        ranked = scorecard["scorecard"]

        return {
            "timestamp": utc_now(),
            "top_alpha_count": min(5, len(ranked)),
            "top_alphas": ranked[:5],
            "best_alpha": ranked[0] if ranked else None,
            "institutional_interpretation": (
                "AURUM now has an alpha factory that can register, score, and rank "
                "research ideas using institutional performance and risk metrics."
            ),
        }

    def run(self) -> Dict:
        registry = self.generate_registry()
        scorecard = self.scorecard(registry)
        rankings = self.rankings(scorecard)

        (RESULTS_DIR / "alpha_registry.json").write_text(
            json.dumps(registry, indent=2),
            encoding="utf-8",
        )

        (RESULTS_DIR / "alpha_scorecard.json").write_text(
            json.dumps(scorecard, indent=2),
            encoding="utf-8",
        )

        (RESULTS_DIR / "top_alpha_rankings.json").write_text(
            json.dumps(rankings, indent=2),
            encoding="utf-8",
        )

        return {
            "registry": registry,
            "scorecard": scorecard,
            "rankings": rankings,
        }


def main() -> None:
    result = AlphaFactory().run()
    rankings = result["rankings"]

    print("=" * 80)
    print("AURUM PHASE 6B.4 ALPHA RESEARCH FACTORY")
    print("=" * 80)
    print(f"Alpha Ideas: {result['registry']['alpha_count']}")

    best = rankings["best_alpha"]
    if best:
        print(f"Best Alpha:  {best['alpha_id']} | {best['name']}")
        print(f"Score:       {best['alpha_score']}")

    print("-" * 80)
    print(rankings["institutional_interpretation"])
    print("=" * 80)


if __name__ == "__main__":
    main()