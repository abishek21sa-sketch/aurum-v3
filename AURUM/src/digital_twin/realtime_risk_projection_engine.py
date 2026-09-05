# src/digital_twin/realtime_risk_projection_engine.py

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import redis


REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0
STREAM_RISK_EVENTS = "risk_events"

LIVE_STATE_PATH = Path("results/digital_twin/live_state/live_market_state.json")
MONTE_CARLO_SUMMARY_PATH = Path("results/digital_twin/monte_carlo_lab/monte_carlo_summary.json")
STRESS_TEST_PATH = Path("results/digital_twin/stress_testing/stress_test_results.json")
CONTAGION_PATH = Path("results/digital_twin/contagion_engine/contagion_results.json")
REGIME_PATH = Path("results/digital_twin/regime_transition/regime_transition_summary.json")

OUTPUT_DIR = Path("results/digital_twin/live_risk_projection")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class RealtimeRiskProjection:
    event_type: str
    timestamp_utc: str
    live_state_label: str
    live_market_stress_score: float
    projected_var_95: float
    projected_cvar_95: float
    projected_expected_drawdown: float
    projected_drawdown: float
    projected_worst_stress_impact: float
    projected_worst_contagion_impact: float
    survival_probability: float
    risk_level: str
    recommended_monitoring_mode: str
    redis_event_id: Optional[str] = None


class RealtimeRiskProjectionEngine:
    def __init__(self) -> None:
        self.redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True,
        )

    def load_json(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def stress_multiplier(self, stress_score: float) -> float:
        return 1.0 + min(max(stress_score, 0.0), 1.0)

    def classify_risk_level(
        self,
        projected_drawdown: float,
        survival_probability: float,
        stress_score: float,
    ) -> str:
        if projected_drawdown <= -0.25 or survival_probability < 0.80 or stress_score >= 0.85:
            return "critical"
        if projected_drawdown <= -0.15 or survival_probability < 0.90 or stress_score >= 0.60:
            return "high"
        if projected_drawdown <= -0.08 or survival_probability < 0.95 or stress_score >= 0.35:
            return "moderate"
        return "low"

    def monitoring_mode(self, risk_level: str) -> str:
        if risk_level == "critical":
            return "continuous_governance_review"
        if risk_level == "high":
            return "heightened_intraday_monitoring"
        if risk_level == "moderate":
            return "standard_intraday_monitoring"
        return "normal_monitoring"

    def publish_risk_projection(self, projection: RealtimeRiskProjection) -> str:
        data = asdict(projection)
        data.pop("redis_event_id", None)

        payload = {
            key: json.dumps(value) if isinstance(value, (dict, list, bool)) else str(value)
            for key, value in data.items()
            if value is not None
        }

        return self.redis_client.xadd(STREAM_RISK_EVENTS, payload)

    def run(self) -> RealtimeRiskProjection:
        live_state = self.load_json(LIVE_STATE_PATH)
        monte_carlo = self.load_json(MONTE_CARLO_SUMMARY_PATH)
        stress_results = self.load_json(STRESS_TEST_PATH)
        contagion_results = self.load_json(CONTAGION_PATH)
        regime = self.load_json(REGIME_PATH)

        if not live_state:
            raise FileNotFoundError(
                f"Missing live state file: {LIVE_STATE_PATH}. "
                "Run python -m src.digital_twin.live_digital_twin_state_engine first."
            )

        stress_score = float(live_state.get("market_stress_score", 0.0))
        multiplier = self.stress_multiplier(stress_score)

        base_var = float(monte_carlo.get("var_95", 0.0))
        base_cvar = float(monte_carlo.get("cvar_95", 0.0))
        base_drawdown = float(monte_carlo.get("expected_max_drawdown", 0.0))

        projected_var = base_var * multiplier
        projected_cvar = base_cvar * multiplier
        projected_drawdown = base_drawdown * multiplier

        worst_stress_impact = 0.0
        if isinstance(stress_results, list) and stress_results:
            worst_stress_impact = min(float(x.get("portfolio_impact", 0.0)) for x in stress_results)

        worst_contagion_impact = 0.0
        if isinstance(contagion_results, list) and contagion_results:
            worst_contagion_impact = min(float(x.get("total_portfolio_impact", 0.0)) for x in contagion_results)

        panic_probability = float(regime.get("panic_probability", 0.0))
        risk_off_probability = float(regime.get("risk_off_probability", 0.0))

        survival_probability = (
            1.0
            - max(0.0, stress_score * 0.25)
            - max(0.0, panic_probability * 0.25)
            - max(0.0, risk_off_probability * 0.15)
        )
        survival_probability = round(max(min(survival_probability, 1.0), 0.0), 4)

        risk_level = self.classify_risk_level(
            projected_drawdown=projected_drawdown,
            survival_probability=survival_probability,
            stress_score=stress_score,
        )

        projection = RealtimeRiskProjection(
            event_type="risk_projection",
            timestamp_utc=str(live_state.get("timestamp_utc")),
            live_state_label=str(live_state.get("state_label", "unknown")),
            live_market_stress_score=stress_score,
            projected_var_95=projected_var,
            projected_cvar_95=projected_cvar,
            projected_expected_drawdown=projected_drawdown,
            projected_drawdown=projected_drawdown,
            projected_worst_stress_impact=worst_stress_impact,
            projected_worst_contagion_impact=worst_contagion_impact,
            survival_probability=survival_probability,
            risk_level=risk_level,
            recommended_monitoring_mode=self.monitoring_mode(risk_level),
        )

        redis_event_id = self.publish_risk_projection(projection)
        projection.redis_event_id = redis_event_id

        self.write_outputs(projection)
        return projection

    def write_outputs(self, projection: RealtimeRiskProjection) -> None:
        json_path = OUTPUT_DIR / "live_risk_projection.json"
        txt_path = OUTPUT_DIR / "live_risk_projection_report.txt"

        json_path.write_text(
            json.dumps(asdict(projection), indent=2),
            encoding="utf-8",
        )

        lines = [
            "=" * 80,
            "AURUM REAL-TIME RISK PROJECTION ENGINE",
            "=" * 80,
            f"Timestamp UTC: {projection.timestamp_utc}",
            f"Redis Event ID: {projection.redis_event_id}",
            f"Live State Label: {projection.live_state_label}",
            f"Live Market Stress Score: {projection.live_market_stress_score}",
            "-" * 80,
            f"Projected VaR 95: {projection.projected_var_95:.4f}",
            f"Projected CVaR 95: {projection.projected_cvar_95:.4f}",
            f"Projected Expected Drawdown: {projection.projected_expected_drawdown:.4f}",
            f"Worst Stress Impact: {projection.projected_worst_stress_impact:.4f}",
            f"Worst Contagion Impact: {projection.projected_worst_contagion_impact:.4f}",
            f"Survival Probability: {projection.survival_probability:.4f}",
            f"Risk Level: {projection.risk_level}",
            f"Monitoring Mode: {projection.recommended_monitoring_mode}",
        ]

        txt_path.write_text("\n".join(lines), encoding="utf-8")

    def print_projection(self, projection: RealtimeRiskProjection) -> None:
        print("=" * 80)
        print("AURUM REAL-TIME RISK PROJECTION ENGINE")
        print("=" * 80)
        print(f"Live State: {projection.live_state_label}")
        print(f"Stress Score: {projection.live_market_stress_score}")
        print(f"Projected VaR 95: {projection.projected_var_95:.4f}")
        print(f"Projected CVaR 95: {projection.projected_cvar_95:.4f}")
        print(f"Projected Drawdown: {projection.projected_drawdown:.4f}")
        print(f"Worst Stress Impact: {projection.projected_worst_stress_impact:.4f}")
        print(f"Worst Contagion Impact: {projection.projected_worst_contagion_impact:.4f}")
        print(f"Survival Probability: {projection.survival_probability:.4f}")
        print(f"Risk Level: {projection.risk_level}")
        print(f"Monitoring Mode: {projection.recommended_monitoring_mode}")
        print(f"Redis Event ID: {projection.redis_event_id}")


def main() -> None:
    engine = RealtimeRiskProjectionEngine()
    projection = engine.run()
    engine.print_projection(projection)


if __name__ == "__main__":
    main()