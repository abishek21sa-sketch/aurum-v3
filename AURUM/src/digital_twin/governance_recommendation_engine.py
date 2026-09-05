# src/digital_twin/governance_recommendation_engine.py

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict


LIVE_STATE_PATH = Path("results/digital_twin/live_state/live_market_state.json")

LIVE_RISK_PATH = Path(
    "results/digital_twin/live_risk_projection/live_risk_projection.json"
)

SCENARIO_MATCH_PATH = Path(
    "results/digital_twin/live_scenario_matching/live_scenario_match.json"
)

REGIME_PATH = Path(
    "results/digital_twin/regime_transition/regime_transition_summary.json"
)

OUTPUT_DIR = Path("results/digital_twin/governance_recommendation")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class GovernanceRecommendation:
    timestamp_utc: str
    action: str
    confidence: float
    risk_level: str
    portfolio_posture: str
    monitoring_mode: str
    escalation_required: bool
    closest_scenario: str
    scenario_similarity_score: float
    reason: str


class GovernanceRecommendationEngine:
    def load_json(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def decide_action(
        self,
        risk_level: str,
        stress_score: float,
        survival_probability: float,
        scenario_similarity: float,
        closest_scenario: str,
        regime_risk_level: str,
    ) -> str:
        closest = closest_scenario.lower()

        if (
            risk_level == "critical"
            or survival_probability < 0.80
            or stress_score >= 0.85
        ):
            return "force_de_risk_and_escalate"

        if (
            risk_level == "high"
            or survival_probability < 0.90
            or "contagion" in closest
            or scenario_similarity >= 0.90
        ):
            return "reduce_risk_and_trigger_governance_review"

        if (
            risk_level == "moderate"
            or regime_risk_level.lower() == "moderate"
            or stress_score >= 0.35
        ):
            return "tighten_limits_and_monitor"

        return "maintain_current_posture"

    def decide_posture(self, action: str) -> str:
        if action == "force_de_risk_and_escalate":
            return "defensive_de_risking"
        if action == "reduce_risk_and_trigger_governance_review":
            return "risk_reduction"
        if action == "tighten_limits_and_monitor":
            return "cautious"
        return "normal"

    def compute_confidence(
        self,
        stress_score: float,
        scenario_similarity: float,
        survival_probability: float,
    ) -> float:
        confidence = (
            0.40 * stress_score
            + 0.40 * scenario_similarity
            + 0.20 * (1.0 - survival_probability)
        )

        return round(max(min(confidence, 1.0), 0.0), 4)

    def build_reason(
        self,
        action: str,
        risk_level: str,
        stress_score: float,
        survival_probability: float,
        closest_scenario: str,
        scenario_similarity: float,
        regime_risk_level: str,
    ) -> str:
        return (
            f"Action={action} because live risk level is {risk_level}, "
            f"market stress score is {stress_score:.2f}, "
            f"survival probability is {survival_probability:.2f}, "
            f"closest scenario is {closest_scenario} "
            f"with similarity {scenario_similarity:.2f}, "
            f"and regime risk level is {regime_risk_level}."
        )

    def run(self) -> GovernanceRecommendation:
        live_state = self.load_json(LIVE_STATE_PATH)
        live_risk = self.load_json(LIVE_RISK_PATH)
        scenario_match = self.load_json(SCENARIO_MATCH_PATH)
        regime = self.load_json(REGIME_PATH)

        if not live_state:
            raise FileNotFoundError(
                f"Missing live state file: {LIVE_STATE_PATH}"
            )

        if not live_risk:
            raise FileNotFoundError(
                f"Missing live risk projection file: {LIVE_RISK_PATH}"
            )

        if not scenario_match:
            raise FileNotFoundError(
                f"Missing scenario match file: {SCENARIO_MATCH_PATH}"
            )

        timestamp = str(live_state.get("timestamp_utc"))

        stress_score = float(live_state.get("market_stress_score", 0.0))
        risk_level = str(live_risk.get("risk_level", "unknown"))
        survival_probability = float(live_risk.get("survival_probability", 1.0))
        monitoring_mode = str(
            live_risk.get("recommended_monitoring_mode", "normal_monitoring")
        )

        closest_scenario = str(scenario_match.get("closest_scenario", "unknown"))
        scenario_similarity = float(
            scenario_match.get("closest_similarity_score", 0.0)
        )

        regime_risk_level = str(regime.get("regime_risk_level", "unknown"))

        action = self.decide_action(
            risk_level=risk_level,
            stress_score=stress_score,
            survival_probability=survival_probability,
            scenario_similarity=scenario_similarity,
            closest_scenario=closest_scenario,
            regime_risk_level=regime_risk_level,
        )

        posture = self.decide_posture(action)

        confidence = self.compute_confidence(
            stress_score=stress_score,
            scenario_similarity=scenario_similarity,
            survival_probability=survival_probability,
        )

        escalation_required = action in {
            "force_de_risk_and_escalate",
            "reduce_risk_and_trigger_governance_review",
        }

        reason = self.build_reason(
            action=action,
            risk_level=risk_level,
            stress_score=stress_score,
            survival_probability=survival_probability,
            closest_scenario=closest_scenario,
            scenario_similarity=scenario_similarity,
            regime_risk_level=regime_risk_level,
        )

        recommendation = GovernanceRecommendation(
            timestamp_utc=timestamp,
            action=action,
            confidence=confidence,
            risk_level=risk_level,
            portfolio_posture=posture,
            monitoring_mode=monitoring_mode,
            escalation_required=escalation_required,
            closest_scenario=closest_scenario,
            scenario_similarity_score=scenario_similarity,
            reason=reason,
        )

        self.write_outputs(recommendation)
        return recommendation

    def write_outputs(self, recommendation: GovernanceRecommendation) -> None:
        json_path = OUTPUT_DIR / "governance_recommendation.json"
        txt_path = OUTPUT_DIR / "governance_recommendation_report.txt"

        json_path.write_text(
            json.dumps(asdict(recommendation), indent=2),
            encoding="utf-8",
        )

        lines = [
            "=" * 80,
            "AURUM LIVE DIGITAL TWIN GOVERNANCE RECOMMENDATION",
            "=" * 80,
            f"Timestamp UTC: {recommendation.timestamp_utc}",
            f"Action: {recommendation.action}",
            f"Confidence: {recommendation.confidence:.4f}",
            f"Risk Level: {recommendation.risk_level}",
            f"Portfolio Posture: {recommendation.portfolio_posture}",
            f"Monitoring Mode: {recommendation.monitoring_mode}",
            f"Escalation Required: {recommendation.escalation_required}",
            "-" * 80,
            f"Closest Scenario: {recommendation.closest_scenario}",
            f"Scenario Similarity Score: {recommendation.scenario_similarity_score:.4f}",
            "-" * 80,
            "Reason:",
            recommendation.reason,
        ]

        txt_path.write_text("\n".join(lines), encoding="utf-8")

    def print_recommendation(self, recommendation: GovernanceRecommendation) -> None:
        print("=" * 80)
        print("AURUM LIVE DIGITAL TWIN GOVERNANCE RECOMMENDATION")
        print("=" * 80)
        print(f"Action: {recommendation.action}")
        print(f"Confidence: {recommendation.confidence:.4f}")
        print(f"Risk Level: {recommendation.risk_level}")
        print(f"Portfolio Posture: {recommendation.portfolio_posture}")
        print(f"Monitoring Mode: {recommendation.monitoring_mode}")
        print(f"Escalation Required: {recommendation.escalation_required}")
        print("-" * 80)
        print(f"Closest Scenario: {recommendation.closest_scenario}")
        print(f"Scenario Similarity: {recommendation.scenario_similarity_score:.4f}")
        print("-" * 80)
        print(recommendation.reason)


def main() -> None:
    engine = GovernanceRecommendationEngine()
    recommendation = engine.run()
    engine.print_recommendation(recommendation)


if __name__ == "__main__":
    main()