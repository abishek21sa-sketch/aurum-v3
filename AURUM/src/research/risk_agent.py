from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.research.base_research_agent import BaseResearchAgent


class RiskAgent(BaseResearchAgent):
    """
    AURUM Risk Agent.

    Analyzes:
    - VaR
    - CVaR
    - projected drawdown
    - live risk projection
    - stress testing
    - contagion outputs
    """

    agent_name = "risk_agent"

    def __init__(self) -> None:
        super().__init__()

        self.possible_paths = {
            "risk_snapshot": [
                Path("results/monitoring/risk_snapshot.json"),
                Path("results/risk/risk_dashboard.json"),
            ],
            "risk_history": [
                Path("results/monitoring/risk_history_summary.json"),
                Path("results/monitoring/risk_budget_summary.json"),
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
            "drawdown_governance": [
                Path("results/governance/drawdown_governance_summary.json"),
            ],
        }

    def observe(self) -> Dict[str, Any]:
        observations: Dict[str, Any] = {
            "available_sources": {},
            "risk_snapshot": {},
            "risk_history": {},
            "live_risk_projection": {},
            "stress_test_results": {},
            "contagion_results": {},
            "drawdown_governance": {},
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
        risk_snapshot = self.observations.get("risk_snapshot", {})
        risk_history = self.observations.get("risk_history", {})
        live_projection = self.observations.get("live_risk_projection", {})
        stress_results = self.observations.get("stress_test_results", {})
        contagion_results = self.observations.get("contagion_results", {})
        drawdown_governance = self.observations.get("drawdown_governance", {})

        var_95 = self._extract_first_float(
            [
                risk_snapshot,
                risk_history,
                live_projection,
            ],
            [
                "var_95",
                "VaR_95",
                "portfolio_var_95",
                "projected_var_95",
                "projected_VaR_95",
            ],
            default=0.05,
        )

        cvar_95 = self._extract_first_float(
            [
                risk_snapshot,
                risk_history,
                live_projection,
            ],
            [
                "cvar_95",
                "CVaR_95",
                "portfolio_cvar_95",
                "projected_cvar_95",
                "projected_CVaR_95",
            ],
            default=0.08,
        )

        projected_drawdown = self._extract_first_float(
            [
                live_projection,
                risk_snapshot,
                risk_history,
                drawdown_governance,
            ],
            [
                "projected_drawdown",
                "max_drawdown",
                "current_drawdown",
                "drawdown",
                "projected_max_drawdown",
            ],
            default=0.10,
        )

        stress_score = self._estimate_stress_score(
            stress_results=stress_results,
            live_projection=live_projection,
        )

        contagion_score = self._estimate_contagion_score(contagion_results)

        tail_risk_score = self._score_tail_risk(
            var_95=var_95,
            cvar_95=cvar_95,
            projected_drawdown=projected_drawdown,
        )

        overall_risk_score = round(
            self._clip(
                0.35 * tail_risk_score
                + 0.25 * stress_score
                + 0.20 * contagion_score
                + 0.20 * self._score_drawdown(projected_drawdown)
            ),
            4,
        )

        risk_assessment = self._classify_risk_assessment(overall_risk_score)

        return {
            "risk_assessment": risk_assessment,
            "overall_risk_score": overall_risk_score,
            "tail_risk_score": round(tail_risk_score, 4),
            "stress_score": round(stress_score, 4),
            "contagion_score": round(contagion_score, 4),
            "var_95": round(var_95, 4),
            "cvar_95": round(cvar_95, 4),
            "projected_drawdown": round(projected_drawdown, 4),
            "drawdown_pressure": round(self._score_drawdown(projected_drawdown), 4),
            "tail_risk_report": self._build_tail_risk_report(
                var_95=var_95,
                cvar_95=cvar_95,
                projected_drawdown=projected_drawdown,
                tail_risk_score=tail_risk_score,
            ),
            "stress_summary": self._build_stress_summary(
                stress_score=stress_score,
                contagion_score=contagion_score,
            ),
            "risk_signal_quality": self._assess_source_quality(),
        }

    def recommend(self) -> List[str]:
        risk_score = float(self.analysis.get("overall_risk_score", 0.5))
        assessment = str(self.analysis.get("risk_assessment", "moderate"))
        tail_risk = float(self.analysis.get("tail_risk_score", 0.5))
        stress_score = float(self.analysis.get("stress_score", 0.5))
        contagion_score = float(self.analysis.get("contagion_score", 0.5))

        recommendations: List[str] = []

        if risk_score >= 0.75:
            recommendations.append(
                "Risk is high; reduce aggressive exposure and prioritize capital preservation."
            )
            recommendations.append(
                "Require governance approval before increasing portfolio risk."
            )

        elif risk_score >= 0.60:
            recommendations.append(
                "Risk is elevated; keep allocation defensive and avoid large rebalance increases."
            )
            recommendations.append(
                "Use stress-test results before approving new risk exposure."
            )

        elif risk_score >= 0.40:
            recommendations.append(
                "Risk is moderate; maintain normal risk controls."
            )
            recommendations.append(
                "Allow regime and portfolio agents to guide tactical positioning."
            )

        else:
            recommendations.append(
                "Risk is contained; no immediate de-risking action is required."
            )

        if tail_risk >= 0.65:
            recommendations.append(
                "Tail risk is elevated; monitor VaR, CVaR, and drawdown limits closely."
            )

        if stress_score >= 0.65:
            recommendations.append(
                "Stress-test pressure is elevated; review worst-case scenario exposure."
            )

        if contagion_score >= 0.65:
            recommendations.append(
                "Contagion risk is elevated; diversification may fail under stress."
            )

        recommendations.append(f"Current risk assessment: {assessment}.")
        return recommendations

    def explain(self) -> str:
        assessment = self.analysis.get("risk_assessment", "moderate")
        overall = self.analysis.get("overall_risk_score", 0.5)
        tail = self.analysis.get("tail_risk_score", 0.5)
        stress = self.analysis.get("stress_score", 0.5)
        contagion = self.analysis.get("contagion_score", 0.5)
        drawdown = self.analysis.get("projected_drawdown", 0.0)

        return (
            f"The Risk Agent classifies current portfolio risk as {assessment} "
            f"with an overall risk score of {overall}. Tail risk score is {tail}, "
            f"stress score is {stress}, contagion score is {contagion}, and "
            f"projected drawdown is {drawdown}."
        )

    def _build_tail_risk_report(
        self,
        var_95: float,
        cvar_95: float,
        projected_drawdown: float,
        tail_risk_score: float,
    ) -> str:
        return (
            f"VaR 95 is {round(var_95, 4)}, CVaR 95 is {round(cvar_95, 4)}, "
            f"and projected drawdown is {round(projected_drawdown, 4)}. "
            f"Tail risk score is {round(tail_risk_score, 4)}."
        )

    def _build_stress_summary(
        self,
        stress_score: float,
        contagion_score: float,
    ) -> str:
        return (
            f"Stress score is {round(stress_score, 4)} and contagion score is "
            f"{round(contagion_score, 4)}. These values summarize scenario-loss "
            f"pressure and cross-asset shock propagation risk."
        )

    def _score_tail_risk(
        self,
        var_95: float,
        cvar_95: float,
        projected_drawdown: float,
    ) -> float:
        var_score = self._clip(abs(var_95) / 0.10)
        cvar_score = self._clip(abs(cvar_95) / 0.15)
        drawdown_score = self._score_drawdown(projected_drawdown)

        return self._clip(
            0.30 * var_score
            + 0.40 * cvar_score
            + 0.30 * drawdown_score
        )

    @staticmethod
    def _score_drawdown(drawdown: float) -> float:
        return RiskAgent._clip(abs(drawdown) / 0.25)

    def _estimate_stress_score(
        self,
        stress_results: Dict[str, Any],
        live_projection: Dict[str, Any],
    ) -> float:
        direct_score = self._safe_get(
            live_projection,
            ["stress_score", "market_stress_score", "live_stress_score"],
            default=None,
        )

        if direct_score is not None:
            return self._clip(self._safe_float(direct_score, default=0.5))

        losses = self._collect_numeric_values_by_keywords(
            stress_results,
            keywords=["loss", "drawdown", "impact", "shock"],
        )

        if not losses:
            return 0.5

        worst_loss = max(abs(value) for value in losses)
        return self._clip(worst_loss / 0.25)

    def _estimate_contagion_score(self, contagion_results: Dict[str, Any]) -> float:
        direct_score = self._safe_get(
            contagion_results,
            ["contagion_score", "systemic_risk_score", "network_risk_score"],
            default=None,
        )

        if direct_score is not None:
            return self._clip(self._safe_float(direct_score, default=0.5))

        numeric_values = self._collect_numeric_values_by_keywords(
            contagion_results,
            keywords=["contagion", "correlation", "spillover", "risk"],
        )

        if not numeric_values:
            return 0.5

        avg_value = sum(abs(v) for v in numeric_values) / len(numeric_values)
        return self._clip(avg_value)

    @staticmethod
    def _classify_risk_assessment(score: float) -> str:
        if score >= 0.75:
            return "high"
        if score >= 0.60:
            return "elevated"
        if score >= 0.40:
            return "moderate"
        return "contained"

    def _assess_source_quality(self) -> str:
        sources = self.observations.get("available_sources", {})
        available_count = sum(1 for value in sources.values() if value)

        if available_count >= 5:
            return "high"
        if available_count >= 3:
            return "medium"
        if available_count >= 1:
            return "low"
        return "fallback"

    @classmethod
    def _extract_first_float(
        cls,
        sources: List[Dict[str, Any]],
        keys: List[str],
        default: float,
    ) -> float:
        for source in sources:
            value = cls._safe_get(source, keys, default=None)

            if value is not None:
                return cls._safe_float(value, default=default)

        return default

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
            "risk_metrics",
            "portfolio_metrics",
            "projection",
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
    agent = RiskAgent()
    result = agent.run()
    print(json.dumps(result, indent=2, default=str))