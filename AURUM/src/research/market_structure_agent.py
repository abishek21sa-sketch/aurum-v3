from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from src.research.base_research_agent import BaseResearchAgent


class MarketStructureAgent(BaseResearchAgent):
    """
    AURUM Market Structure Agent.

    Analyzes:
    - market breadth
    - volatility pressure
    - cross-asset correlations
    - liquidity stress
    - risk asset dispersion
    """

    agent_name = "market_structure_agent"

    def __init__(self) -> None:
        super().__init__()
        self.features_path = Path("data/features/macro_features.parquet")
        self.live_snapshot_path = Path("results/realtime/live_market_snapshot.json")

    def observe(self) -> Dict[str, Any]:
        observations: Dict[str, Any] = {
            "macro_features_available": self.features_path.exists(),
            "live_snapshot_available": self.live_snapshot_path.exists(),
            "latest_features": {},
            "live_snapshot": {},
            "feature_rows": 0,
            "feature_columns": [],
        }

        if self.features_path.exists():
            try:
                df = pd.read_parquet(self.features_path)

                if not df.empty:
                    latest = df.tail(1).to_dict(orient="records")[0]
                    observations["latest_features"] = latest
                    observations["feature_rows"] = len(df)
                    observations["feature_columns"] = list(df.columns)

            except Exception as exc:
                observations["macro_features_error"] = str(exc)

        if self.live_snapshot_path.exists():
            try:
                with self.live_snapshot_path.open("r", encoding="utf-8") as f:
                    observations["live_snapshot"] = json.load(f)

            except Exception as exc:
                observations["live_snapshot_error"] = str(exc)

        return observations

    def analyze(self) -> Dict[str, Any]:
        latest = self.observations.get("latest_features", {})

        momentum_breadth = self._safe_float(
            latest.get("momentum_breadth"), default=0.5
        )
        equity_bond_corr = self._safe_float(
            latest.get("equity_bond_corr_20d"), default=0.0
        )
        equity_gold_corr = self._safe_float(
            latest.get("equity_gold_corr_20d"), default=0.0
        )
        risk_asset_dispersion = self._safe_float(
            latest.get("risk_asset_dispersion_20d"), default=0.0
        )
        liquidity_stress_proxy = self._safe_float(
            latest.get("liquidity_stress_proxy"), default=1.0
        )
        vix_stress_ratio = self._safe_float(
            latest.get("vix_stress_ratio"), default=1.0
        )
        realized_vol_regime_score = self._safe_float(
            latest.get("realized_vol_regime_score"), default=0.5
        )
        volatility_regime_label = str(
            latest.get("volatility_regime_label", "unknown")
        )

        breadth_pressure = self._clip(1.0 - momentum_breadth)
        correlation_pressure = self._score_correlation_pressure(
            equity_bond_corr=equity_bond_corr,
            equity_gold_corr=equity_gold_corr,
        )
        dispersion_pressure = self._score_dispersion_pressure(
            risk_asset_dispersion
        )
        liquidity_pressure = self._score_liquidity_pressure(
            liquidity_stress_proxy
        )
        volatility_pressure = self._score_volatility_pressure(
            vix_stress_ratio=vix_stress_ratio,
            realized_vol_regime_score=realized_vol_regime_score,
        )

        market_structure_score = round(
            self._clip(
                0.25 * breadth_pressure
                + 0.25 * volatility_pressure
                + 0.20 * correlation_pressure
                + 0.20 * liquidity_pressure
                + 0.10 * dispersion_pressure
            ),
            4,
        )

        market_health = self._classify_market_health(market_structure_score)
        liquidity_score = round(self._clip(1.0 - liquidity_pressure), 4)
        volatility_outlook = self._classify_volatility_outlook(
            volatility_pressure, volatility_regime_label
        )
        correlation_regime = self._classify_correlation_regime(
            correlation_pressure,
            equity_bond_corr,
            equity_gold_corr,
        )

        return {
            "market_health": market_health,
            "market_structure_score": market_structure_score,
            "liquidity_score": liquidity_score,
            "volatility_outlook": volatility_outlook,
            "correlation_regime": correlation_regime,
            "breadth_pressure": round(breadth_pressure, 4),
            "volatility_pressure": round(volatility_pressure, 4),
            "correlation_pressure": round(correlation_pressure, 4),
            "liquidity_pressure": round(liquidity_pressure, 4),
            "dispersion_pressure": round(dispersion_pressure, 4),
            "momentum_breadth": round(momentum_breadth, 4),
            "equity_bond_corr_20d": round(equity_bond_corr, 4),
            "equity_gold_corr_20d": round(equity_gold_corr, 4),
            "risk_asset_dispersion_20d": round(risk_asset_dispersion, 4),
            "liquidity_stress_proxy": round(liquidity_stress_proxy, 4),
            "vix_stress_ratio": round(vix_stress_ratio, 4),
            "realized_vol_regime_score": round(realized_vol_regime_score, 4),
            "volatility_regime_label": volatility_regime_label,
            "market_structure_signal_quality": self._assess_signal_quality(),
        }

    def recommend(self) -> List[str]:
        score = float(self.analysis.get("market_structure_score", 0.5))
        health = str(self.analysis.get("market_health", "mixed"))
        liquidity_score = float(self.analysis.get("liquidity_score", 0.5))
        correlation_pressure = float(
            self.analysis.get("correlation_pressure", 0.5)
        )
        breadth_pressure = float(self.analysis.get("breadth_pressure", 0.5))

        recommendations: List[str] = []

        if score >= 0.75:
            recommendations.append(
                "Market structure is stressed; reduce aggressive exposure and prioritize liquidity."
            )
            recommendations.append(
                "Treat correlation and volatility signals as possible contagion warnings."
            )

        elif score >= 0.60:
            recommendations.append(
                "Market structure is fragile; avoid concentrated risk-taking."
            )
            recommendations.append(
                "Use defensive sizing until breadth and liquidity improve."
            )

        elif score >= 0.40:
            recommendations.append(
                "Market structure is mixed; maintain balanced exposure."
            )
            recommendations.append(
                "Let portfolio and risk agents confirm whether tactical changes are needed."
            )

        else:
            recommendations.append(
                "Market structure appears healthy enough for normal allocation behavior."
            )
            recommendations.append(
                "No immediate structure-driven de-risking is required."
            )

        if liquidity_score < 0.40:
            recommendations.append(
                "Liquidity score is weak; avoid large rebalance orders without execution controls."
            )

        if correlation_pressure >= 0.70:
            recommendations.append(
                "Cross-asset correlations are elevated; diversification benefit may be reduced."
            )

        if breadth_pressure >= 0.65:
            recommendations.append(
                "Market breadth is weak; monitor for narrow leadership risk."
            )

        recommendations.append(f"Current market health: {health}.")
        return recommendations

    def explain(self) -> str:
        health = self.analysis.get("market_health", "mixed")
        score = self.analysis.get("market_structure_score", 0.5)
        liquidity_score = self.analysis.get("liquidity_score", 0.5)
        vol_outlook = self.analysis.get("volatility_outlook", "unknown")
        corr_regime = self.analysis.get("correlation_regime", "unknown")
        breadth_pressure = self.analysis.get("breadth_pressure", 0.5)

        return (
            f"The Market Structure Agent classifies current market health as "
            f"{health} with a market structure score of {score}. Liquidity score "
            f"is {liquidity_score}, volatility outlook is {vol_outlook}, and "
            f"the correlation regime is {corr_regime}. Breadth pressure is "
            f"{breadth_pressure}, which measures how weak participation is across "
            f"risk assets."
        )

    def _assess_signal_quality(self) -> str:
        latest = self.observations.get("latest_features", {})

        required_fields = [
            "momentum_breadth",
            "equity_bond_corr_20d",
            "equity_gold_corr_20d",
            "risk_asset_dispersion_20d",
            "liquidity_stress_proxy",
            "vix_stress_ratio",
            "realized_vol_regime_score",
            "volatility_regime_label",
        ]

        available = sum(1 for field in required_fields if field in latest)

        if available == len(required_fields):
            return "high"
        if available >= 5:
            return "medium"
        return "low"

    @staticmethod
    def _score_correlation_pressure(
        equity_bond_corr: float,
        equity_gold_corr: float,
    ) -> float:
        equity_bond_pressure = max(0.0, equity_bond_corr)
        equity_gold_pressure = max(0.0, equity_gold_corr)

        return MarketStructureAgent._clip(
            0.60 * equity_bond_pressure + 0.40 * equity_gold_pressure
        )

    @staticmethod
    def _score_dispersion_pressure(risk_asset_dispersion: float) -> float:
        return MarketStructureAgent._clip(risk_asset_dispersion / 0.05)

    @staticmethod
    def _score_liquidity_pressure(liquidity_stress_proxy: float) -> float:
        return MarketStructureAgent._clip((liquidity_stress_proxy - 0.85) / 0.50)

    @staticmethod
    def _score_volatility_pressure(
        vix_stress_ratio: float,
        realized_vol_regime_score: float,
    ) -> float:
        vix_pressure = MarketStructureAgent._clip((vix_stress_ratio - 0.80) / 0.70)
        realized_pressure = MarketStructureAgent._clip(realized_vol_regime_score)

        return MarketStructureAgent._clip(
            0.45 * vix_pressure + 0.55 * realized_pressure
        )

    @staticmethod
    def _classify_market_health(score: float) -> str:
        if score >= 0.75:
            return "stressed"
        if score >= 0.60:
            return "fragile"
        if score >= 0.40:
            return "mixed"
        return "healthy"

    @staticmethod
    def _classify_volatility_outlook(
        volatility_pressure: float,
        volatility_regime_label: str,
    ) -> str:
        label = volatility_regime_label.lower()

        if volatility_pressure >= 0.75:
            return "elevated"

        if volatility_pressure >= 0.55:
            return "moderate to elevated"

        if "low" in label and volatility_pressure < 0.55:
            return "contained"

        return "moderate"

    @staticmethod
    def _classify_correlation_regime(
        correlation_pressure: float,
        equity_bond_corr: float,
        equity_gold_corr: float,
    ) -> str:
        if correlation_pressure >= 0.75:
            return "high correlation / diversification weakening"

        if correlation_pressure >= 0.55:
            return "moderately elevated correlation"

        if equity_bond_corr < 0 and equity_gold_corr < 0:
            return "diversifying"

        return "normal"

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        try:
            if value is None:
                return default
            return float(value)
        except Exception:
            return default

    @staticmethod
    def _clip(value: float) -> float:
        return min(1.0, max(0.0, float(value)))


if __name__ == "__main__":
    agent = MarketStructureAgent()
    result = agent.run()
    print(json.dumps(result, indent=2, default=str))