from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class HypothesisGenerator:
    def generate(self, alpha_review: Dict) -> Dict:
        top_alpha = alpha_review.get("top_alpha", {})
        weak_alphas = alpha_review.get("weak_alphas", [])

        hypotheses: List[Dict] = []

        if top_alpha:
            hypotheses.append(
                {
                    "hypothesis_id": "HYP_MOMENTUM_REGIME_001",
                    "source": top_alpha.get("alpha_id", "unknown"),
                    "theme": "regime_conditional_momentum",
                    "hypothesis": (
                        "Cross-asset momentum may perform better when filtered by regime "
                        "and volatility state."
                    ),
                    "test_design": (
                        "Compare raw momentum against regime-filtered momentum across "
                        "risk-on, normal, defensive, and crisis states."
                    ),
                    "priority": "high",
                }
            )

        hypotheses.append(
            {
                "hypothesis_id": "HYP_VOL_DEFENSE_001",
                "source": "ALPHA_VOL_001",
                "theme": "volatility_defensive_overlay",
                "hypothesis": (
                    "Volatility spikes may improve portfolio outcomes when used as a "
                    "defensive overlay rather than a standalone signal."
                ),
                "test_design": (
                    "Backtest VIX-triggered defensive allocation overlays on top of "
                    "existing factor and alpha portfolios."
                ),
                "priority": "high",
            }
        )

        hypotheses.append(
            {
                "hypothesis_id": "HYP_RATES_GROWTH_001",
                "source": "ALPHA_RATES_001",
                "theme": "rates_growth_sensitivity",
                "hypothesis": (
                    "Growth equity exposure should be dynamically reduced when rate "
                    "pressure and volatility rise together."
                ),
                "test_design": (
                    "Test QQQ and crypto exposure under combined rate-pressure and "
                    "volatility-stress filters."
                ),
                "priority": "medium",
            }
        )

        if weak_alphas:
            hypotheses.append(
                {
                    "hypothesis_id": "HYP_WEAK_ALPHA_REPAIR_001",
                    "source": "weak_alpha_review",
                    "theme": "alpha_repair",
                    "hypothesis": (
                        "Weak alpha candidates may improve if combined with confirmation "
                        "signals from cross-asset dependencies."
                    ),
                    "test_design": (
                        "Re-test bottom-ranked alphas with confirmation filters from "
                        "rates, USD, commodities, and volatility."
                    ),
                    "priority": "medium",
                }
            )

        return {
            "timestamp": utc_now(),
            "hypothesis_count": len(hypotheses),
            "hypotheses": hypotheses,
        }