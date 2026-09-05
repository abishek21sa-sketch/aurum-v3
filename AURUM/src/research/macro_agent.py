from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from src.research.base_research_agent import BaseResearchAgent


class MacroAgent(BaseResearchAgent):
    """
    AURUM Macro Agent.

    Uses AURUM's existing macro feature layer to estimate:
    - macro outlook
    - macro risk score
    - volatility pressure
    - inflation pressure
    - yield/rates pressure
    - momentum breadth pressure
    """

    agent_name = "macro_agent"

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

        vix_level = self._safe_float(latest.get("vix_level"), default=18.0)
        vix_stress_ratio = self._safe_float(latest.get("vix_stress_ratio"), default=1.0)
        inflation_pressure_proxy = self._safe_float(
            latest.get("inflation_pressure_proxy"), default=0.0
        )
        liquidity_stress_proxy = self._safe_float(
            latest.get("liquidity_stress_proxy"), default=1.0
        )
        yield_spread_proxy = self._safe_float(
            latest.get("yield_spread_proxy"), default=0.0
        )
        momentum_breadth = self._safe_float(latest.get("momentum_breadth"), default=0.5)
        realized_vol_regime_score = self._safe_float(
            latest.get("realized_vol_regime_score"), default=0.5
        )
        volatility_regime_label = str(
            latest.get("volatility_regime_label", "unknown")
        )

        spy_momentum_20d = self._safe_float(
            latest.get("spy_momentum_20d"), default=0.0
        )
        qqq_momentum_20d = self._safe_float(
            latest.get("qqq_momentum_20d"), default=0.0
        )
        tlt_momentum_20d = self._safe_float(
            latest.get("tlt_momentum_20d"), default=0.0
        )

        vix_pressure = self._score_vix_pressure(vix_level, vix_stress_ratio)

        inflation_pressure = self._clip(
            0.50 + inflation_pressure_proxy * 10.0
        )

        yield_pressure = self._clip(
            0.50 - yield_spread_proxy * 3.0
        )

        liquidity_pressure = self._score_liquidity_pressure(liquidity_stress_proxy)

        breadth_pressure = self._clip(1.0 - momentum_breadth)

        realized_vol_pressure = self._clip(realized_vol_regime_score)

        risk_asset_momentum_support = self._clip(
            0.50 + ((spy_momentum_20d + qqq_momentum_20d) / 2.0) * 5.0
        )

        bond_momentum_pressure = self._clip(
            0.50 - tlt_momentum_20d * 5.0
        )

        macro_risk_score = round(
            self._clip(
                0.25 * vix_pressure
                + 0.20 * realized_vol_pressure
                + 0.15 * inflation_pressure
                + 0.15 * yield_pressure
                + 0.10 * liquidity_pressure
                + 0.10 * breadth_pressure
                + 0.05 * bond_momentum_pressure
            ),
            4,
        )

        macro_outlook = self._classify_macro_outlook(
            macro_risk_score=macro_risk_score,
            risk_asset_momentum_support=risk_asset_momentum_support,
            momentum_breadth=momentum_breadth,
        )

        return {
            "macro_outlook": macro_outlook,
            "macro_risk_score": macro_risk_score,
            "vix_level": round(vix_level, 4),
            "vix_stress_ratio": round(vix_stress_ratio, 4),
            "vix_pressure": round(vix_pressure, 4),
            "realized_vol_pressure": round(realized_vol_pressure, 4),
            "inflation_pressure": round(inflation_pressure, 4),
            "yield_pressure": round(yield_pressure, 4),
            "liquidity_pressure": round(liquidity_pressure, 4),
            "breadth_pressure": round(breadth_pressure, 4),
            "bond_momentum_pressure": round(bond_momentum_pressure, 4),
            "risk_asset_momentum_support": round(risk_asset_momentum_support, 4),
            "momentum_breadth": round(momentum_breadth, 4),
            "spy_momentum_20d": round(spy_momentum_20d, 4),
            "qqq_momentum_20d": round(qqq_momentum_20d, 4),
            "tlt_momentum_20d": round(tlt_momentum_20d, 4),
            "yield_spread_proxy": round(yield_spread_proxy, 4),
            "inflation_pressure_proxy": round(inflation_pressure_proxy, 4),
            "liquidity_stress_proxy": round(liquidity_stress_proxy, 4),
            "volatility_regime_label": volatility_regime_label,
            "macro_signal_quality": self._assess_signal_quality(),
        }

    def recommend(self) -> List[str]:
        score = float(self.analysis.get("macro_risk_score", 0.5))
        outlook = str(self.analysis.get("macro_outlook", "neutral"))
        momentum_support = float(
            self.analysis.get("risk_asset_momentum_support", 0.5)
        )
        breadth = float(self.analysis.get("momentum_breadth", 0.5))

        recommendations: List[str] = []

        if score >= 0.75:
            recommendations.append(
                "Maintain defensive macro positioning until volatility, rates, or liquidity pressure improves."
            )
            recommendations.append(
                "Avoid aggressive growth overweight while macro risk remains high."
            )

        elif score >= 0.60:
            recommendations.append(
                "Keep portfolio risk controlled and avoid large directional bets."
            )
            recommendations.append(
                "Use regime and risk agents as confirmation before increasing exposure."
            )

        elif score >= 0.40:
            recommendations.append(
                "Maintain neutral macro positioning."
            )
            recommendations.append(
                "Allow optimizer, regime engine, and risk desk signals to drive tactical allocation."
            )

        else:
            recommendations.append(
                "Macro conditions appear supportive enough for moderate risk exposure."
            )
            recommendations.append(
                "Growth exposure may be acceptable if confirmed by regime and portfolio agents."
            )

        if momentum_support >= 0.65 and breadth >= 0.40:
            recommendations.append(
                "Risk asset momentum is constructive, so avoid becoming overly defensive without confirmation from the risk agent."
            )

        if breadth < 0.35:
            recommendations.append(
                "Momentum breadth is weak, so monitor for narrow-market risk."
            )

        recommendations.append(f"Current macro stance: {outlook}.")
        return recommendations

    def explain(self) -> str:
        outlook = self.analysis.get("macro_outlook", "neutral")
        risk = self.analysis.get("macro_risk_score", 0.5)
        vix_pressure = self.analysis.get("vix_pressure", 0.5)
        realized_vol = self.analysis.get("realized_vol_pressure", 0.5)
        yield_pressure = self.analysis.get("yield_pressure", 0.5)
        breadth_pressure = self.analysis.get("breadth_pressure", 0.5)
        momentum_support = self.analysis.get("risk_asset_momentum_support", 0.5)
        vol_label = self.analysis.get("volatility_regime_label", "unknown")

        return (
            f"The Macro Agent classifies the environment as {outlook} with a "
            f"macro risk score of {risk}. The score is driven by VIX pressure "
            f"of {vix_pressure}, realized volatility pressure of {realized_vol}, "
            f"yield pressure of {yield_pressure}, and breadth pressure of "
            f"{breadth_pressure}. Risk asset momentum support is "
            f"{momentum_support}, and the current volatility regime label is "
            f"{vol_label}. This cleaned-up version uses AURUM's engineered macro "
            f"features instead of over-penalizing raw realized volatility."
        )

    def _assess_signal_quality(self) -> str:
        latest = self.observations.get("latest_features", {})

        required_fields = [
            "vix_level",
            "vix_stress_ratio",
            "inflation_pressure_proxy",
            "liquidity_stress_proxy",
            "yield_spread_proxy",
            "momentum_breadth",
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
    def _score_vix_pressure(vix_level: float, vix_stress_ratio: float) -> float:
        level_score = 0.0

        if vix_level < 15:
            level_score = 0.25
        elif vix_level < 20:
            level_score = 0.40
        elif vix_level < 25:
            level_score = 0.60
        elif vix_level < 30:
            level_score = 0.75
        else:
            level_score = 0.90

        ratio_score = MacroAgent._clip((vix_stress_ratio - 0.80) / 0.70)

        return MacroAgent._clip(0.60 * level_score + 0.40 * ratio_score)

    @staticmethod
    def _score_liquidity_pressure(liquidity_stress_proxy: float) -> float:
        return MacroAgent._clip((liquidity_stress_proxy - 0.85) / 0.50)

    @staticmethod
    def _classify_macro_outlook(
        macro_risk_score: float,
        risk_asset_momentum_support: float,
        momentum_breadth: float,
    ) -> str:
        if macro_risk_score >= 0.75:
            return "defensive"

        if macro_risk_score >= 0.60:
            return "cautiously defensive"

        if macro_risk_score >= 0.40:
            if risk_asset_momentum_support >= 0.65 and momentum_breadth >= 0.40:
                return "neutral with constructive risk momentum"
            return "neutral"

        if risk_asset_momentum_support >= 0.60:
            return "constructive"

        return "moderately constructive"

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
    agent = MacroAgent()
    result = agent.run()
    print(json.dumps(result, indent=2, default=str))