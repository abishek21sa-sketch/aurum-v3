from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List


RESULTS_DIR = Path("results/research")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class StrategyProfile:
    strategy_id: str
    name: str
    category: str
    description: str
    expected_behavior: str
    risk_profile: str
    turnover_profile: str
    regime_fit: List[str]


class StrategyRegistry:
    def __init__(self) -> None:
        self.strategies: Dict[str, StrategyProfile] = {}

    def register_default_strategies(self) -> None:
        defaults = [
            StrategyProfile(
                strategy_id="rolling_min_variance",
                name="Rolling Minimum Variance",
                category="Risk-Based",
                description="Minimizes portfolio variance using rolling covariance estimates.",
                expected_behavior="Stable in volatile or defensive regimes.",
                risk_profile="Low volatility, lower drawdown.",
                turnover_profile="Medium",
                regime_fit=["defensive", "high_volatility", "normal"],
            ),
            StrategyProfile(
                strategy_id="risk_parity",
                name="Risk Parity",
                category="Risk-Based",
                description="Allocates capital so each asset contributes similar portfolio risk.",
                expected_behavior="Diversified performance across regimes.",
                risk_profile="Balanced",
                turnover_profile="Medium",
                regime_fit=["normal", "defensive", "inflation"],
            ),
            StrategyProfile(
                strategy_id="cvar_optimized",
                name="CVaR Optimized",
                category="Tail-Risk",
                description="Optimizes portfolio under conditional value-at-risk constraints.",
                expected_behavior="Better downside protection during crash scenarios.",
                risk_profile="Tail-risk controlled.",
                turnover_profile="Medium",
                regime_fit=["crash", "liquidity_stress", "high_volatility"],
            ),
            StrategyProfile(
                strategy_id="regime_aware",
                name="Regime-Aware Allocation",
                category="Adaptive",
                description="Adjusts exposures based on detected market regime.",
                expected_behavior="Adapts between growth, defensive, and crisis states.",
                risk_profile="Dynamic",
                turnover_profile="High",
                regime_fit=["bull", "normal", "defensive", "crash"],
            ),
            StrategyProfile(
                strategy_id="black_litterman",
                name="Black-Litterman",
                category="Bayesian",
                description="Combines market equilibrium with subjective or model-driven views.",
                expected_behavior="Strong when views are directionally correct.",
                risk_profile="Moderate to high depending on views.",
                turnover_profile="Low",
                regime_fit=["normal", "bull", "macro_transition"],
            ),
            StrategyProfile(
                strategy_id="bayesian_robust",
                name="Bayesian Robust",
                category="Robust Optimization",
                description="Uses uncertainty-aware portfolio construction.",
                expected_behavior="More stable under parameter uncertainty.",
                risk_profile="Robust",
                turnover_profile="Low to medium",
                regime_fit=["uncertain", "normal", "defensive"],
            ),
            StrategyProfile(
                strategy_id="meta_strategy",
                name="Meta Strategy Allocator",
                category="Ensemble",
                description="Combines multiple strategies using performance and robustness weights.",
                expected_behavior="Best all-weather institutional strategy candidate.",
                risk_profile="Balanced and adaptive.",
                turnover_profile="Medium",
                regime_fit=["all"],
            ),
        ]

        for strategy in defaults:
            self.strategies[strategy.strategy_id] = strategy

    def to_dict(self) -> Dict[str, dict]:
        return {sid: asdict(profile) for sid, profile in self.strategies.items()}

    def save(self, path: Path | None = None) -> Path:
        if path is None:
            path = RESULTS_DIR / "strategy_registry.json"

        with path.open("w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

        return path


def build_strategy_registry() -> Path:
    registry = StrategyRegistry()
    registry.register_default_strategies()
    return registry.save()


if __name__ == "__main__":
    output_path = build_strategy_registry()
    print("=" * 80)
    print("AURUM STRATEGY REGISTRY")
    print("=" * 80)
    print(f"Saved: {output_path}")