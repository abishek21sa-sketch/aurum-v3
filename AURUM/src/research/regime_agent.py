from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.research.base_research_agent import BaseResearchAgent


class RegimeAgent(BaseResearchAgent):
    """
    AURUM Regime Agent.

    Consumes existing regime and digital twin outputs when available.

    Analyzes:
    - current regime
    - expected next regime
    - regime confidence
    - transition risk
    - regime stability
    """

    agent_name = "regime_agent"

    def __init__(self) -> None:
        super().__init__()

        self.possible_paths = {
            "live_digital_twin_state": [
                Path("results/digital_twin/live_state/live_market_state.json"),
                Path("results/digital_twin/final_report/digital_twin_final_summary.json"),
                Path("results/institutional/latest_institutional_runtime_state.json"),
                Path("results/institutional/canonical_runtime_state.json"),
                Path("results/runtime/state/latest_runtime_state.json"),
            ],
            "regime_decision": [
                Path("results/regime_intelligence/transition_decision.json"),
                Path("results/regime_intelligence/final_regime_allocation_summary.json"),
                Path("results/regime_intelligence/portfolio_intelligence_report.json"),
                Path("results/optimization/regime_allocation_policy.json"),
                Path("results/institutional/latest_institutional_runtime_state.json"),
            ],
            "regime_probabilities": [
                Path("results/regime_intelligence/confidence_exposure_summary.json"),
                Path("results/digital_twin/regime_transition/regime_transition_summary.json"),
                Path("results/regime_intelligence/final_regime_allocation_summary.json"),
                Path("results/optimization/regime_allocation_policy.json"),
            ],
            "transition_matrix": [
                Path("results/regime_intelligence/transition_decision.json"),
                Path("results/digital_twin/regime_transition/regime_transition_summary.json"),
                Path("results/optimization/regime_allocation_policy.json"),
            ],
        }

    def observe(self) -> Dict[str, Any]:
        observations: Dict[str, Any] = {
            "available_sources": {},
            "live_digital_twin_state": {},
            "regime_decision": {},
            "regime_probabilities": {},
            "transition_matrix": {},
        }

        for source_name, paths in self.possible_paths.items():
            found_path = self._first_existing_path(paths)
            observations["available_sources"][source_name] = (
                str(found_path) if found_path else None
            )

            if found_path:
                observations[source_name] = self._load_json(found_path)

        return observations

    def analyze(self) -> Dict[str, Any]:
        twin_state = self.observations.get("live_digital_twin_state", {})
        regime_decision = self.observations.get("regime_decision", {})
        regime_probs = self.observations.get("regime_probabilities", {})
        transition_matrix = self.observations.get("transition_matrix", {})

        current_regime = self._extract_current_regime(
            twin_state=twin_state,
            regime_decision=regime_decision,
            regime_probs=regime_probs,
        )

        regime_confidence = self._extract_regime_confidence(
            regime_decision=regime_decision,
            regime_probs=regime_probs,
            current_regime=current_regime,
        )

        expected_next_regime = self._extract_expected_next_regime(
            current_regime=current_regime,
            regime_decision=regime_decision,
            regime_probs=regime_probs,
            transition_matrix=transition_matrix,
        )

        transition_risk = self._estimate_transition_risk(
            current_regime=current_regime,
            expected_next_regime=expected_next_regime,
            regime_confidence=regime_confidence,
            twin_state=twin_state,
            transition_matrix=transition_matrix,
        )

        regime_stability = round(self._clip(1.0 - transition_risk), 4)

        regime_risk_level = self._classify_regime_risk(
            current_regime=current_regime,
            transition_risk=transition_risk,
            regime_confidence=regime_confidence,
        )

        return {
            "current_regime": current_regime,
            "expected_next_regime": expected_next_regime,
            "regime_confidence": round(regime_confidence, 4),
            "transition_risk": round(transition_risk, 4),
            "regime_stability": regime_stability,
            "regime_risk_level": regime_risk_level,
            "source_quality": self._assess_source_quality(),
            "live_state_label": self._safe_get(
                twin_state,
                ["state_label", "live_state", "status"],
                default="unknown",
            ),
            "market_stress_score": self._safe_float(
                self._safe_get(
                    twin_state,
                    ["market_stress_score", "stress_score", "risk_score"],
                    default=0.5,
                ),
                default=0.5,
            ),
        }

    def recommend(self) -> List[str]:
        current_regime = str(self.analysis.get("current_regime", "unknown"))
        next_regime = str(self.analysis.get("expected_next_regime", "unknown"))
        transition_risk = float(self.analysis.get("transition_risk", 0.5))
        confidence = float(self.analysis.get("regime_confidence", 0.5))
        risk_level = str(self.analysis.get("regime_risk_level", "moderate"))

        recommendations: List[str] = []

        if transition_risk >= 0.75:
            recommendations.append(
                "Regime transition risk is high; avoid large allocation changes until confirmation improves."
            )
            recommendations.append(
                "Use defensive sizing and require confirmation from risk and portfolio agents."
            )

        elif transition_risk >= 0.55:
            recommendations.append(
                "Regime transition risk is elevated; keep allocation flexible."
            )
            recommendations.append(
                "Avoid overcommitting to the current regime if next-regime probability is rising."
            )

        elif transition_risk >= 0.35:
            recommendations.append(
                "Regime conditions are moderately stable; use normal tactical allocation controls."
            )

        else:
            recommendations.append(
                "Regime appears stable; current allocation can remain regime-aligned."
            )

        if confidence < 0.50:
            recommendations.append(
                "Regime confidence is low; reduce dependence on regime-only allocation decisions."
            )

        if current_regime != next_regime and next_regime != "unknown":
            recommendations.append(
                f"Monitor possible transition from {current_regime} to {next_regime}."
            )

        recommendations.append(f"Current regime risk level: {risk_level}.")
        return recommendations

    def explain(self) -> str:
        current_regime = self.analysis.get("current_regime", "unknown")
        next_regime = self.analysis.get("expected_next_regime", "unknown")
        confidence = self.analysis.get("regime_confidence", 0.5)
        transition_risk = self.analysis.get("transition_risk", 0.5)
        stability = self.analysis.get("regime_stability", 0.5)
        source_quality = self.analysis.get("source_quality", "low")

        return (
            f"The Regime Agent identifies the current regime as {current_regime} "
            f"with confidence {confidence}. The expected next regime is "
            f"{next_regime}. Transition risk is {transition_risk}, producing a "
            f"regime stability score of {stability}. Source quality is "
            f"{source_quality}, based on which regime and digital twin artifacts "
            f"were available."
        )

    def _extract_current_regime(
        self,
        twin_state: Dict[str, Any],
        regime_decision: Dict[str, Any],
        regime_probs: Dict[str, Any],
    ) -> str:
        candidates = [
            self._safe_get(regime_decision, ["current_regime", "regime", "selected_regime"]),
            self._safe_get(twin_state, ["current_regime", "regime", "market_regime"]),
            self._highest_probability_regime(regime_probs),
        ]

        for candidate in candidates:
            if candidate:
                return str(candidate)

        return "unknown"

    def _extract_regime_confidence(
        self,
        regime_decision: Dict[str, Any],
        regime_probs: Dict[str, Any],
        current_regime: str,
    ) -> float:
        direct_confidence = self._safe_get(
            regime_decision,
            ["confidence", "regime_confidence", "selected_confidence"],
            default=None,
        )

        if direct_confidence is not None:
            return self._clip(self._safe_float(direct_confidence, default=0.5))

        probs = self._normalize_probabilities(regime_probs)

        if current_regime in probs:
            return self._clip(probs[current_regime])

        if probs:
            return self._clip(max(probs.values()))

        return 0.50

    def _extract_expected_next_regime(
        self,
        current_regime: str,
        regime_decision: Dict[str, Any],
        regime_probs: Dict[str, Any],
        transition_matrix: Dict[str, Any],
    ) -> str:
        direct_next = self._safe_get(
            regime_decision,
            [
                "expected_next_regime",
                "next_regime",
                "predicted_next_regime",
                "most_likely_next_regime",
                "effective_allocation_regime",
                "detected_current_regime",
            ],
            default=None,
        )

        if direct_next:
            return str(direct_next)

        highest_prob = self._highest_probability_regime(regime_decision)
        if highest_prob:
            return highest_prob

        highest_prob = self._highest_probability_regime(regime_probs)
        if highest_prob:
            return highest_prob

        next_from_matrix = self._next_regime_from_transition_matrix(
            current_regime=current_regime,
            transition_matrix=transition_matrix,
        )

        if next_from_matrix:
            return next_from_matrix

        return current_regime if current_regime != "unknown" else "unknown"
    
    def _estimate_transition_risk(
        self,
        current_regime: str,
        expected_next_regime: str,
        regime_confidence: float,
        twin_state: Dict[str, Any],
        transition_matrix: Dict[str, Any],
    ) -> float:
        direct_transition_risk = self._safe_get(
            transition_matrix,
            ["transition_risk_score", "transition_risk", "regime_transition_risk"],
            default=None,
        )

        if direct_transition_risk is not None:
            return self._clip(self._safe_float(direct_transition_risk, default=0.5))

        market_stress_score = self._safe_float(
            self._safe_get(
                twin_state,
                ["market_stress_score", "stress_score", "risk_score"],
                default=0.5,
            ),
            default=0.5,
        )

        regime_change_flag = 1.0 if current_regime != expected_next_regime else 0.0
        confidence_penalty = 1.0 - self._clip(regime_confidence)

        return self._clip(
            0.45 * market_stress_score
            + 0.30 * confidence_penalty
            + 0.25 * regime_change_flag
        )

    def _classify_regime_risk(
        self,
        current_regime: str,
        transition_risk: float,
        regime_confidence: float,
    ) -> str:
        regime_lower = current_regime.lower()

        if "crisis" in regime_lower or "stress" in regime_lower or "defensive" in regime_lower:
            base = 0.20
        elif "high_vol" in regime_lower or "volatile" in regime_lower:
            base = 0.15
        else:
            base = 0.0

        adjusted = self._clip(transition_risk + base + max(0.0, 0.5 - regime_confidence))

        if adjusted >= 0.75:
            return "high"
        if adjusted >= 0.55:
            return "elevated"
        if adjusted >= 0.35:
            return "moderate"
        return "low"

    def _assess_source_quality(self) -> str:
        sources = self.observations.get("available_sources", {})
        available_count = sum(1 for value in sources.values() if value)

        if available_count >= 3:
            return "high"
        if available_count == 2:
            return "medium"
        if available_count == 1:
            return "low"
        return "fallback"

    @staticmethod
    def _first_existing_path(paths: List[Path]) -> Optional[Path]:
        for path in paths:
            if path.exists():
                return path
        return None

    @staticmethod
    def _load_json(path: Path) -> Dict[str, Any]:
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, dict):
                return data

            return {"data": data}

        except Exception as exc:
            return {"error": str(exc), "path": str(path)}

    @staticmethod
    def _safe_get(
        data: Dict[str, Any],
        keys: List[str],
        default: Any = None,
    ) -> Any:
        if not isinstance(data, dict):
            return default

        for key in keys:
            if key in data:
                return data[key]

        nested_candidates = [
            "analysis",
            "summary",
            "result",
            "decision",
            "latest",
            "state",
            "payload",
        ]

        for container_key in nested_candidates:
            nested = data.get(container_key)
            if isinstance(nested, dict):
                for key in keys:
                    if key in nested:
                        return nested[key]

        return default

    @staticmethod
    def _normalize_probabilities(data: Dict[str, Any]) -> Dict[str, float]:
        if not isinstance(data, dict):
            return {}

        possible_containers = [
            data.get("regime_probabilities", {}),
            data.get("probabilities", {}),
            data.get("latest_probabilities", {}),
        ]

        for container in possible_containers:
            if not isinstance(container, dict):
                continue

            numeric_items: Dict[str, float] = {}

            for key, value in container.items():
                try:
                    numeric_items[str(key)] = float(value)
                except Exception:
                    continue

            if numeric_items:
                total = sum(v for v in numeric_items.values() if v >= 0)

                if total > 0:
                    return {
                        key: max(0.0, value) / total
                        for key, value in numeric_items.items()
                    }

        return {}

    @classmethod
    def _highest_probability_regime(cls, data: Dict[str, Any]) -> Optional[str]:
        probs = cls._normalize_probabilities(data)

        if not probs:
            return None

        return max(probs.items(), key=lambda item: item[1])[0]

    @staticmethod
    def _next_regime_from_transition_matrix(
        current_regime: str,
        transition_matrix: Dict[str, Any],
    ) -> Optional[str]:
        if not isinstance(transition_matrix, dict):
            return None

        possible_matrix = transition_matrix

        for key in ["matrix", "transition_matrix", "probabilities"]:
            if isinstance(transition_matrix.get(key), dict):
                possible_matrix = transition_matrix[key]
                break

        row = possible_matrix.get(current_regime)

        if not isinstance(row, dict):
            return None

        numeric_row: Dict[str, float] = {}

        for regime, prob in row.items():
            try:
                numeric_row[str(regime)] = float(prob)
            except Exception:
                continue

        if not numeric_row:
            return None

        return max(numeric_row.items(), key=lambda item: item[1])[0]

    @staticmethod
    def _transition_probability(
        current_regime: str,
        expected_next_regime: str,
        transition_matrix: Dict[str, Any],
    ) -> Optional[float]:
        if not isinstance(transition_matrix, dict):
            return None

        possible_matrix = transition_matrix

        for key in ["matrix", "transition_matrix", "probabilities"]:
            if isinstance(transition_matrix.get(key), dict):
                possible_matrix = transition_matrix[key]
                break

        row = possible_matrix.get(current_regime)

        if not isinstance(row, dict):
            return None

        try:
            return RegimeAgent._clip(float(row.get(expected_next_regime)))
        except Exception:
            return None

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
    agent = RegimeAgent()
    result = agent.run()
    print(json.dumps(result, indent=2, default=str))