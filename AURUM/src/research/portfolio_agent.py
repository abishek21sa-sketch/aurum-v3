from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.research.base_research_agent import BaseResearchAgent


class PortfolioAgent(BaseResearchAgent):
    """
    AURUM Portfolio Agent.

    Evaluates:
    - portfolio health
    - concentration risk
    - allocation drift
    - governance approval
    - execution readiness
    """

    agent_name = "portfolio_agent"

    def __init__(self) -> None:
        super().__init__()

        self.possible_paths = {
            "portfolio_state": [
                Path("results/portfolio/realtime_portfolio_state.json"),
                Path("results/portfolio/institutional_portfolio_state.json"),
                Path("results/execution/current_portfolio_state.json"),
            ],
            "optimized_portfolio": [
                Path("results/optimization/realtime_optimized_portfolio.json"),
                Path("results/optimization/final_optimizer_decision_report.json"),
            ],
            "portfolio_decision": [
                Path("results/portfolio/portfolio_decision_orchestration.json"),
            ],
            "governance_decision": [
                Path("results/portfolio/governance_execution_decision.json"),
                Path("results/governance/portfolio_approval_decision.json"),
            ],
            "portfolio_health": [
                Path("results/monitoring/portfolio_health_score.json"),
            ],
            "portfolio_drift": [
                Path("results/monitoring/portfolio_drift_summary.json"),
            ],
            "concentration": [
                Path("results/governance/concentration_summary.json"),
            ],
        }

    def observe(self) -> Dict[str, Any]:
        observations: Dict[str, Any] = {
            "available_sources": {},
            "portfolio_state": {},
            "optimized_portfolio": {},
            "portfolio_decision": {},
            "governance_decision": {},
            "portfolio_health": {},
            "portfolio_drift": {},
            "concentration": {},
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
        portfolio_state = self.observations.get("portfolio_state", {})
        portfolio_health = self.observations.get("portfolio_health", {})
        concentration = self.observations.get("concentration", {})
        drift = self.observations.get("portfolio_drift", {})
        governance = self.observations.get("governance_decision", {})
        optimized = self.observations.get("optimized_portfolio", {})

        raw_health_score = self._extract_first_float(
            [portfolio_health, portfolio_state],
            ["health_score", "portfolio_health_score", "score"],
            default=75.0,
        )
        health_score = self._normalize_score(raw_health_score)

        max_absolute_drift = self._extract_first_float(
            [drift],
            ["max_absolute_drift", "max_drift", "drift_score"],
            default=0.0,
        )

        rebalance_required = self._extract_first_bool(
            [drift],
            ["rebalance_required", "should_rebalance"],
            default=False,
        )

        drift_pressure = self._score_drift(max_absolute_drift, rebalance_required)

        largest_position_weight = self._extract_first_float(
            [concentration],
            ["largest_position_weight", "top_1_exposure"],
            default=0.25,
        )

        top_3_exposure = self._extract_first_float(
            [concentration],
            ["top_3_exposure"],
            default=0.60,
        )

        hhi = self._extract_first_float(
            [concentration],
            ["herfindahl_hirschman_index", "hhi"],
            default=0.20,
        )

        concentration_status = self._extract_first_string(
            [concentration],
            ["concentration_status", "status"],
            default="UNKNOWN",
        )

        concentration_score = self._score_concentration(
            largest_position_weight=largest_position_weight,
            top_3_exposure=top_3_exposure,
            hhi=hhi,
            concentration_status=concentration_status,
        )

        approval_decision = self._extract_first_string(
            [governance],
            ["approval_decision", "governance_status", "execution_status", "status"],
            default="UNKNOWN",
        )

        approved = self._extract_first_bool(
            [governance],
            ["approved", "allow_execution"],
            default=None,
        )

        committee_decision = self._extract_first_string(
            [governance],
            ["committee_decision"],
            default="UNKNOWN",
        )

        compliance_status = self._extract_first_string(
            [governance],
            ["compliance_status"],
            default="UNKNOWN",
        )

        execution_status = self._extract_first_string(
            [governance],
            ["execution_status"],
            default="UNKNOWN",
        )

        turnover = self._extract_first_float(
            [optimized],
            ["turnover"],
            default=0.0,
        )

        execution_turnover = self._safe_get(
            optimized,
            ["execution_summary"],
            default={},
        )

        if isinstance(execution_turnover, dict):
            turnover = self._safe_float(
                execution_turnover.get("turnover", turnover),
                default=turnover,
            )

        governance_penalty = self._score_governance_penalty(
            approved=approved,
            approval_decision=approval_decision,
            committee_decision=committee_decision,
            compliance_status=compliance_status,
            execution_status=execution_status,
        )

        portfolio_score = round(
            self._clip(
                0.45 * health_score
                + 0.20 * (1.0 - concentration_score)
                + 0.15 * (1.0 - drift_pressure)
                + 0.10 * (1.0 - self._score_turnover(turnover))
                + 0.10 * (1.0 - governance_penalty)
                - 0.20 * governance_penalty
            ),
            4,
        )

        portfolio_assessment = self._classify_portfolio_assessment(
            portfolio_score=portfolio_score,
            governance_penalty=governance_penalty,
        )

        concentration_risk = self._classify_concentration_risk(
            concentration_score=concentration_score,
            concentration_status=concentration_status,
        )

        return {
            "portfolio_assessment": portfolio_assessment,
            "portfolio_score": portfolio_score,
            "health_score": round(health_score, 4),
            "raw_health_score": round(raw_health_score, 4),
            "concentration_score": round(concentration_score, 4),
            "concentration_risk": concentration_risk,
            "concentration_status": concentration_status,
            "largest_position_weight": round(largest_position_weight, 4),
            "top_3_exposure": round(top_3_exposure, 4),
            "hhi": round(hhi, 4),
            "drift_pressure": round(drift_pressure, 4),
            "max_absolute_drift": round(max_absolute_drift, 6),
            "rebalance_required": rebalance_required,
            "turnover": round(turnover, 4),
            "governance_penalty": round(governance_penalty, 4),
            "approval_decision": approval_decision,
            "approved": approved,
            "committee_decision": committee_decision,
            "compliance_status": compliance_status,
            "execution_status": execution_status,
            "suggested_adjustments": self._generate_adjustments(
                concentration_score=concentration_score,
                concentration_status=concentration_status,
                drift_pressure=drift_pressure,
                governance_penalty=governance_penalty,
                approval_decision=approval_decision,
                compliance_status=compliance_status,
            ),
            "portfolio_signal_quality": self._assess_signal_quality(),
        }

    def recommend(self) -> List[str]:
        recommendations: List[str] = []

        assessment = str(self.analysis.get("portfolio_assessment", "watch"))
        portfolio_score = float(self.analysis.get("portfolio_score", 0.5))
        concentration_risk = str(self.analysis.get("concentration_risk", "moderate"))
        governance_penalty = float(self.analysis.get("governance_penalty", 0.0))
        approval_decision = str(self.analysis.get("approval_decision", "UNKNOWN"))
        compliance_status = str(self.analysis.get("compliance_status", "UNKNOWN"))

        if governance_penalty >= 0.75:
            recommendations.append(
                "Do not execute portfolio changes until governance blocks are resolved."
            )
            recommendations.append(
                f"Governance status requires review: {approval_decision}, {compliance_status}."
            )
        elif portfolio_score >= 0.75:
            recommendations.append(
                "Portfolio structure is healthy, but continue normal monitoring."
            )
        elif portfolio_score >= 0.55:
            recommendations.append(
                "Portfolio is acceptable but should remain on watch."
            )
        else:
            recommendations.append(
                "Portfolio quality is weak; review optimizer, governance, and concentration controls."
            )

        if concentration_risk == "high":
            recommendations.append(
                "Concentration risk is high; reduce largest-position and top-three exposure where possible."
            )

        if self.analysis.get("rebalance_required") is True:
            recommendations.append(
                "Portfolio drift indicates rebalancing should be reviewed."
            )

        recommendations.append(f"Current portfolio assessment: {assessment}.")
        return recommendations

    def explain(self) -> str:
        return (
            f"The Portfolio Agent classifies the portfolio as "
            f"{self.analysis['portfolio_assessment']} with a portfolio score of "
            f"{self.analysis['portfolio_score']}. Health score is "
            f"{self.analysis['health_score']}, concentration risk is "
            f"{self.analysis['concentration_risk']}, and governance approval is "
            f"{self.analysis['approval_decision']}. Compliance status is "
            f"{self.analysis['compliance_status']}."
        )

    def _generate_adjustments(
        self,
        concentration_score: float,
        concentration_status: str,
        drift_pressure: float,
        governance_penalty: float,
        approval_decision: str,
        compliance_status: str,
    ) -> List[str]:
        adjustments: List[str] = []

        if governance_penalty >= 0.75:
            adjustments.append(
                "Resolve governance rejection before execution."
            )

        if "NON_COMPLIANT" in compliance_status.upper():
            adjustments.append(
                "Investigate compliance breach and update portfolio constraints."
            )

        if "BLOCKED" in approval_decision.upper():
            adjustments.append(
                "Keep execution blocked until approval gate clears."
            )

        if concentration_score >= 0.70 or "HIGH" in concentration_status.upper():
            adjustments.append(
                "Reduce concentration in the largest holdings."
            )

        if drift_pressure >= 0.70:
            adjustments.append(
                "Review rebalance need due to elevated portfolio drift."
            )

        if not adjustments:
            adjustments.append(
                "No major portfolio adjustments required."
            )

        return adjustments

    @staticmethod
    def _normalize_score(score: float) -> float:
        if score > 1.0:
            return PortfolioAgent._clip(score / 100.0)
        return PortfolioAgent._clip(score)

    @staticmethod
    def _score_concentration(
        largest_position_weight: float,
        top_3_exposure: float,
        hhi: float,
        concentration_status: str,
    ) -> float:
        largest_score = PortfolioAgent._clip(largest_position_weight / 0.40)
        top_3_score = PortfolioAgent._clip(top_3_exposure / 0.80)
        hhi_score = PortfolioAgent._clip(hhi / 0.30)

        status_bonus = 0.0
        if "HIGH" in concentration_status.upper():
            status_bonus = 0.20
        elif "MODERATE" in concentration_status.upper():
            status_bonus = 0.10

        return PortfolioAgent._clip(
            0.40 * largest_score
            + 0.35 * top_3_score
            + 0.25 * hhi_score
            + status_bonus
        )

    @staticmethod
    def _score_drift(max_absolute_drift: float, rebalance_required: bool) -> float:
        drift_score = PortfolioAgent._clip(abs(max_absolute_drift) / 0.10)

        if rebalance_required:
            drift_score = max(drift_score, 0.75)

        return PortfolioAgent._clip(drift_score)

    @staticmethod
    def _score_turnover(turnover: float) -> float:
        return PortfolioAgent._clip(abs(turnover) / 0.50)

    @staticmethod
    def _score_governance_penalty(
        approved: Optional[bool],
        approval_decision: str,
        committee_decision: str,
        compliance_status: str,
        execution_status: str,
    ) -> float:
        penalty = 0.0

        combined = " ".join(
            [
                str(approval_decision),
                str(committee_decision),
                str(compliance_status),
                str(execution_status),
            ]
        ).upper()

        if approved is False:
            penalty += 0.40

        if "BLOCKED" in combined:
            penalty += 0.30

        if "REJECTED" in combined:
            penalty += 0.25

        if "NON_COMPLIANT" in combined or "CRITICAL" in combined:
            penalty += 0.30

        return PortfolioAgent._clip(penalty)

    @staticmethod
    def _classify_portfolio_assessment(
        portfolio_score: float,
        governance_penalty: float,
    ) -> str:
        if governance_penalty >= 0.75:
            return "blocked"

        if portfolio_score >= 0.80:
            return "strong"

        if portfolio_score >= 0.60:
            return "healthy"

        if portfolio_score >= 0.40:
            return "watch"

        return "weak"

    @staticmethod
    def _classify_concentration_risk(
        concentration_score: float,
        concentration_status: str,
    ) -> str:
        if concentration_score >= 0.70 or "HIGH" in concentration_status.upper():
            return "high"

        if concentration_score >= 0.45 or "MODERATE" in concentration_status.upper():
            return "moderate"

        return "low"

    def _assess_signal_quality(self) -> str:
        count = sum(
            1
            for value in self.observations["available_sources"].values()
            if value is not None
        )

        if count >= 6:
            return "high"

        if count >= 3:
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
            "portfolio_metrics",
            "execution_summary",
            "risk_controls",
            "institutional_final_decision",
            "decision_flow",
            "governance_decision",
            "optimizer_decision",
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
        default: float,
    ) -> float:
        for source in sources:
            value = cls._safe_get(source, keys, default=None)

            if value is not None:
                return cls._safe_float(value, default=default)

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
    def _extract_first_bool(
        cls,
        sources: List[Dict[str, Any]],
        keys: List[str],
        default: Optional[bool],
    ) -> Optional[bool]:
        for source in sources:
            value = cls._safe_get(source, keys, default=None)

            if value is None:
                continue

            if isinstance(value, bool):
                return value

            if isinstance(value, str):
                lowered = value.strip().lower()

                if lowered in {"true", "yes", "approved", "pass", "allowed"}:
                    return True

                if lowered in {"false", "no", "rejected", "blocked", "fail"}:
                    return False

        return default

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
    def _first_existing_path(paths: List[Path]) -> Optional[Path]:
        for path in paths:
            if path.exists():
                return path
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
        return max(0.0, min(1.0, float(value)))


if __name__ == "__main__":
    agent = PortfolioAgent()
    result = agent.run()

    print(json.dumps(result, indent=2, default=str))