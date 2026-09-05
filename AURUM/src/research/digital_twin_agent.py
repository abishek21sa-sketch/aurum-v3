from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.research.base_research_agent import BaseResearchAgent


class DigitalTwinAgent(BaseResearchAgent):
    """
    AURUM Digital Twin Agent.

    Evaluates:
    - live digital twin state
    - live risk projection
    - stress test outcomes
    - contagion outcomes
    - Monte Carlo summary
    - regime transition summary
    - historical replay results
    """

    agent_name = "digital_twin_agent"

    def __init__(self) -> None:
        super().__init__()

        self.possible_paths = {
            "live_state": [
                Path("results/digital_twin/live_state/live_market_state.json"),
            ],
            "live_risk_projection": [
                Path("results/digital_twin/live_risk_projection/live_risk_projection.json"),
            ],
            "stress_test_results": [
                Path("results/digital_twin/stress_testing/stress_test_results.json"),
            ],
            "contagion_results": [
                Path("results/digital_twin/contagion_engine/contagion_results.json"),
            ],
            "monte_carlo_summary": [
                Path("results/digital_twin/monte_carlo_lab/monte_carlo_summary.json"),
            ],
            "historical_replay": [
                Path("results/digital_twin/historical_replay/historical_replay_results.json"),
            ],
            "regime_transition": [
                Path("results/digital_twin/regime_transition/regime_transition_summary.json"),
                Path("results/regime_intelligence/transition_decision.json"),
            ],
            "final_summary": [
                Path("results/digital_twin/final_report/digital_twin_final_summary.json"),
            ],
        }

    def observe(self) -> Dict[str, Any]:
        observations: Dict[str, Any] = {
            "available_sources": {},
            "live_state": {},
            "live_risk_projection": {},
            "stress_test_results": {},
            "contagion_results": {},
            "monte_carlo_summary": {},
            "historical_replay": {},
            "regime_transition": {},
            "final_summary": {},
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
        live_state = self.observations.get("live_state", {})
        live_risk = self.observations.get("live_risk_projection", {})
        stress = self.observations.get("stress_test_results", {})
        contagion = self.observations.get("contagion_results", {})
        monte_carlo = self.observations.get("monte_carlo_summary", {})
        replay = self.observations.get("historical_replay", {})
        transition = self.observations.get("regime_transition", {})
        final_summary = self.observations.get("final_summary", {})

        live_state_label = self._extract_first_string(
            [live_state, live_risk],
            ["state_label", "live_state_label", "status"],
            default="unknown",
        )

        current_regime = self._extract_first_string(
            [live_state, transition, final_summary],
            [
                "current_regime",
                "detected_current_regime",
                "effective_allocation_regime",
                "regime",
            ],
            default="unknown",
        )

        market_stress_score = self._extract_first_float(
            [live_state, live_risk],
            [
                "market_stress_score",
                "live_market_stress_score",
                "stress_score",
            ],
            default=0.5,
        )

        projected_var_95 = self._extract_first_float(
            [live_risk],
            ["projected_var_95", "var_95", "VaR_95"],
            default=0.10,
        )

        projected_cvar_95 = self._extract_first_float(
            [live_risk],
            ["projected_cvar_95", "cvar_95", "CVaR_95"],
            default=0.12,
        )

        projected_drawdown = self._extract_first_float(
            [live_risk],
            [
                "projected_drawdown",
                "projected_expected_drawdown",
                "expected_drawdown",
            ],
            default=-0.08,
        )

        projected_worst_stress_impact = self._extract_first_float(
            [live_risk],
            ["projected_worst_stress_impact", "worst_stress_impact"],
            default=None,
        )

        projected_worst_contagion_impact = self._extract_first_float(
            [live_risk],
            ["projected_worst_contagion_impact", "worst_contagion_impact"],
            default=None,
        )

        survival_probability = self._extract_first_float(
            [live_risk, monte_carlo, final_summary],
            [
                "survival_probability",
                "portfolio_survival_probability",
                "probability_of_survival",
            ],
            default=0.75,
        )

        transition_risk_score = self._extract_first_float(
            [transition],
            [
                "transition_risk_score",
                "transition_risk",
                "regime_transition_risk",
            ],
            default=0.35,
        )

        regime_confidence = self._extract_first_float(
            [transition],
            ["regime_confidence", "confidence"],
            default=0.7,
        )

        worst_stress_case = self._find_worst_case(
            stress,
            impact_keys=[
                "portfolio_impact",
                "impact",
                "shock_impact",
                "loss",
            ],
            name_keys=[
                "name",
                "scenario_id",
                "scenario",
            ],
        )

        worst_contagion_case = self._find_worst_case(
            contagion,
            impact_keys=[
                "total_portfolio_impact",
                "portfolio_impact",
                "impact",
                "loss",
            ],
            name_keys=[
                "source_asset",
                "name",
                "scenario_id",
            ],
        )

        monte_carlo_risk_score = self._estimate_monte_carlo_risk(monte_carlo)
        replay_risk_score = self._estimate_replay_risk(replay)

        stress_loss = abs(
            projected_worst_stress_impact
            if projected_worst_stress_impact is not None
            else worst_stress_case["impact"]
        )

        contagion_loss = abs(
            projected_worst_contagion_impact
            if projected_worst_contagion_impact is not None
            else worst_contagion_case["impact"]
        )

        future_risk_score = round(
            self._clip(
                0.20 * self._clip(market_stress_score)
                + 0.20 * self._score_loss(stress_loss)
                + 0.15 * self._score_loss(contagion_loss)
                + 0.15 * self._score_loss(abs(projected_drawdown))
                + 0.10 * self._score_tail(projected_var_95, projected_cvar_95)
                + 0.10 * transition_risk_score
                + 0.05 * monte_carlo_risk_score
                + 0.05 * replay_risk_score
            ),
            4,
        )

        future_risk_assessment = self._classify_future_risk(future_risk_score)

        most_likely_case = self._build_most_likely_case(
            current_regime=current_regime,
            live_state_label=live_state_label,
            market_stress_score=market_stress_score,
            survival_probability=survival_probability,
        )

        worst_case = self._build_worst_case(
            worst_stress_case=worst_stress_case,
            worst_contagion_case=worst_contagion_case,
            projected_worst_stress_impact=projected_worst_stress_impact,
            projected_worst_contagion_impact=projected_worst_contagion_impact,
        )

        digital_twin_confidence = self._estimate_confidence(
            survival_probability=survival_probability,
            regime_confidence=regime_confidence,
        )

        return {
            "future_risk_assessment": future_risk_assessment,
            "future_risk_score": future_risk_score,
            "current_regime": current_regime,
            "live_state_label": live_state_label,
            "market_stress_score": round(market_stress_score, 4),
            "projected_var_95": round(projected_var_95, 4),
            "projected_cvar_95": round(projected_cvar_95, 4),
            "projected_drawdown": round(projected_drawdown, 4),
            "projected_worst_stress_impact": (
                round(projected_worst_stress_impact, 4)
                if projected_worst_stress_impact is not None
                else None
            ),
            "projected_worst_contagion_impact": (
                round(projected_worst_contagion_impact, 4)
                if projected_worst_contagion_impact is not None
                else None
            ),
            "survival_probability": round(survival_probability, 4),
            "transition_risk_score": round(transition_risk_score, 4),
            "regime_confidence": round(regime_confidence, 4),
            "worst_stress_case": worst_stress_case,
            "worst_contagion_case": worst_contagion_case,
            "monte_carlo_risk_score": round(monte_carlo_risk_score, 4),
            "replay_risk_score": round(replay_risk_score, 4),
            "most_likely_case": most_likely_case,
            "worst_case": worst_case,
            "digital_twin_confidence": round(digital_twin_confidence, 4),
            "digital_twin_signal_quality": self._assess_signal_quality(),
        }

    def recommend(self) -> List[str]:
        recommendations: List[str] = []

        risk_score = float(self.analysis.get("future_risk_score", 0.5))
        assessment = str(self.analysis.get("future_risk_assessment", "moderate"))
        survival_probability = float(self.analysis.get("survival_probability", 0.75))
        transition_risk = float(self.analysis.get("transition_risk_score", 0.35))

        if risk_score >= 0.75:
            recommendations.append(
                "Future risk is high; maintain defensive posture and review worst-case exposure."
            )
            recommendations.append(
                "Do not increase risk until digital twin projections improve."
            )

        elif risk_score >= 0.60:
            recommendations.append(
                "Future risk is elevated; keep hedges active and avoid aggressive re-risking."
            )

        elif risk_score >= 0.40:
            recommendations.append(
                "Future risk is moderate; continue standard monitoring and scenario review."
            )

        else:
            recommendations.append(
                "Future risk appears contained; no digital-twin-driven de-risking is required."
            )

        if survival_probability < 0.80:
            recommendations.append(
                "Survival probability is below preferred threshold; review downside protection."
            )

        if transition_risk >= 0.55:
            recommendations.append(
                "Regime transition risk is elevated; prepare for allocation adjustment."
            )

        recommendations.append(f"Digital twin future risk assessment: {assessment}.")
        return recommendations

    def explain(self) -> str:
        return (
            f"The Digital Twin Agent classifies future risk as "
            f"{self.analysis['future_risk_assessment']} with a future risk score "
            f"of {self.analysis['future_risk_score']}. The most likely case is: "
            f"{self.analysis['most_likely_case']} Worst case: "
            f"{self.analysis['worst_case']} Survival probability is "
            f"{self.analysis['survival_probability']}."
        )

    def _build_most_likely_case(
        self,
        current_regime: str,
        live_state_label: str,
        market_stress_score: float,
        survival_probability: float,
    ) -> str:
        if market_stress_score >= 0.75:
            return (
                f"Continuation of {current_regime} regime with elevated stress and "
                f"{live_state_label} live state."
            )

        if market_stress_score >= 0.45:
            return (
                f"Moderate-stress continuation of {current_regime} regime with "
                f"{live_state_label} live state."
            )

        if survival_probability >= 0.85:
            return (
                f"Stable continuation of {current_regime} regime with acceptable "
                f"survival probability."
            )

        return (
            f"Watch-state continuation of {current_regime} regime with moderate "
            f"downside uncertainty."
        )

    def _build_worst_case(
        self,
        worst_stress_case: Dict[str, Any],
        worst_contagion_case: Dict[str, Any],
        projected_worst_stress_impact: Optional[float],
        projected_worst_contagion_impact: Optional[float],
    ) -> str:
        stress_name = worst_stress_case.get("name", "unknown stress case")
        stress_impact = (
            projected_worst_stress_impact
            if projected_worst_stress_impact is not None
            else worst_stress_case.get("impact", 0.0)
        )

        contagion_name = worst_contagion_case.get("name", "unknown contagion case")
        contagion_impact = (
            projected_worst_contagion_impact
            if projected_worst_contagion_impact is not None
            else worst_contagion_case.get("impact", 0.0)
        )

        return (
            f"{stress_name} with estimated impact {round(stress_impact, 4)}, "
            f"combined with contagion from {contagion_name} with estimated impact "
            f"{round(contagion_impact, 4)}."
        )

    def _find_worst_case(
        self,
        data: Any,
        impact_keys: List[str],
        name_keys: List[str],
    ) -> Dict[str, Any]:
        records = self._extract_records(data)

        if not records:
            return {
                "name": "unknown",
                "impact": 0.0,
                "severity": "unknown",
            }

        worst_record = None
        worst_impact = 0.0

        for record in records:
            if not isinstance(record, dict):
                continue

            impact = self._extract_value_from_keys(record, impact_keys)

            if impact is None:
                continue

            impact_float = self._safe_float(impact, default=0.0)

            if abs(impact_float) >= abs(worst_impact):
                worst_impact = impact_float
                worst_record = record

        if worst_record is None:
            return {
                "name": "unknown",
                "impact": 0.0,
                "severity": "unknown",
            }

        name = self._extract_value_from_keys(worst_record, name_keys)
        severity = self._extract_value_from_keys(
            worst_record,
            ["severity", "survival_status", "network_stress_level"],
        )

        return {
            "name": str(name) if name is not None else "unknown",
            "impact": round(worst_impact, 4),
            "severity": str(severity) if severity is not None else "unknown",
        }

    @staticmethod
    def _extract_records(data: Any) -> List[Dict[str, Any]]:
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]

        if isinstance(data, dict):
            for key in ["data", "results", "scenarios", "records", "summary"]:
                value = data.get(key)

                if isinstance(value, list):
                    return [x for x in value if isinstance(x, dict)]

        return []

    @staticmethod
    def _extract_value_from_keys(
        data: Dict[str, Any],
        keys: List[str],
    ) -> Any:
        for key in keys:
            if key in data:
                return data[key]

        return None

    def _estimate_monte_carlo_risk(self, monte_carlo: Dict[str, Any]) -> float:
        if not isinstance(monte_carlo, dict) or not monte_carlo:
            return 0.5

        risk_value = self._safe_get(
            monte_carlo,
            [
                "risk_score",
                "failure_probability",
                "drawdown_probability",
                "probability_of_loss",
            ],
            default=None,
        )

        if risk_value is not None:
            return self._clip(self._safe_float(risk_value, default=0.5))

        numeric_values = self._collect_numeric_values_by_keywords(
            monte_carlo,
            ["loss", "drawdown", "var", "cvar", "risk"],
        )

        if not numeric_values:
            return 0.5

        avg = sum(abs(x) for x in numeric_values) / len(numeric_values)
        return self._clip(avg)

    def _estimate_replay_risk(self, replay: Dict[str, Any]) -> float:
        if not isinstance(replay, dict) or not replay:
            return 0.5

        direct = self._safe_get(
            replay,
            [
                "replay_risk_score",
                "historical_risk_score",
                "max_replay_drawdown",
                "worst_replay_loss",
            ],
            default=None,
        )

        if direct is not None:
            return self._clip(abs(self._safe_float(direct, default=0.5)))

        numeric_values = self._collect_numeric_values_by_keywords(
            replay,
            ["loss", "drawdown", "impact", "risk"],
        )

        if not numeric_values:
            return 0.5

        worst = max(abs(x) for x in numeric_values)
        return self._score_loss(worst)

    @staticmethod
    def _score_loss(loss: float) -> float:
        return DigitalTwinAgent._clip(abs(loss) / 0.25)

    @staticmethod
    def _score_tail(var_95: float, cvar_95: float) -> float:
        var_score = DigitalTwinAgent._clip(abs(var_95) / 0.15)
        cvar_score = DigitalTwinAgent._clip(abs(cvar_95) / 0.20)

        return DigitalTwinAgent._clip(0.45 * var_score + 0.55 * cvar_score)

    @staticmethod
    def _classify_future_risk(score: float) -> str:
        if score >= 0.75:
            return "high"

        if score >= 0.60:
            return "elevated"

        if score >= 0.40:
            return "moderate"

        return "contained"

    @staticmethod
    def _estimate_confidence(
        survival_probability: float,
        regime_confidence: float,
    ) -> float:
        return DigitalTwinAgent._clip(
            0.60 * survival_probability + 0.40 * regime_confidence
        )

    def _assess_signal_quality(self) -> str:
        sources = self.observations.get("available_sources", {})
        count = sum(1 for value in sources.values() if value is not None)

        if count >= 7:
            return "high"

        if count >= 4:
            return "medium"

        if count >= 1:
            return "low"

        return "fallback"

    @classmethod
    def _safe_get(
        cls,
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
            "results",
            "metrics",
            "projection",
            "risk_projection",
            "latest",
            "payload",
        ]

        for container_key in nested_candidates:
            nested = data.get(container_key)

            if isinstance(nested, dict):
                value = cls._safe_get(nested, keys, default=None)

                if value is not None:
                    return value

        return default

    @classmethod
    def _extract_first_float(
        cls,
        sources: List[Dict[str, Any]],
        keys: List[str],
        default: Optional[float],
    ) -> Optional[float]:
        for source in sources:
            value = cls._safe_get(source, keys, default=None)

            if value is not None:
                return cls._safe_float(value, default=default if default is not None else 0.0)

        return default

    @classmethod
    def _extract_first_string(
        cls,
        sources: List[Dict[str, Any]],
        keys: List[str],
        default: str,
    ) -> str:
        for source in sources:
            value = cls._safe_get(source, keys, default=None)

            if value is not None:
                return str(value)

        return default

    @classmethod
    def _collect_numeric_values_by_keywords(
        cls,
        data: Any,
        keywords: List[str],
    ) -> List[float]:
        values: List[float] = []

        if isinstance(data, dict):
            for key, value in data.items():
                key_lower = str(key).lower()

                if isinstance(value, (dict, list)):
                    values.extend(
                        cls._collect_numeric_values_by_keywords(value, keywords)
                    )

                elif any(keyword in key_lower for keyword in keywords):
                    try:
                        values.append(float(value))
                    except Exception:
                        continue

        elif isinstance(data, list):
            for item in data:
                values.extend(cls._collect_numeric_values_by_keywords(item, keywords))

        return values

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
    agent = DigitalTwinAgent()
    result = agent.run()

    print(json.dumps(result, indent=2, default=str))