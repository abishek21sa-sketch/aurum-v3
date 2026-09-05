# src/regime/realtime_regime_decision_engine.py

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import redis


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

MARKET_SIGNALS_STREAM = "market_signals"
RISK_EVENTS_STREAM = "risk_events"


class RealtimeRegimeDecisionEngine:
    def __init__(self, redis_url: str = REDIS_URL):
        self.redis = redis.Redis.from_url(redis_url, decode_responses=True)

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _decode_event(raw_event: Dict[str, Any]) -> Dict[str, Any]:
        decoded = {}

        for key, value in raw_event.items():
            try:
                decoded[key] = json.loads(value)
            except Exception:
                decoded[key] = value

        return decoded

    def get_latest_event(self, stream_name: str, event_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        events = self.redis.xrevrange(stream_name, count=50)

        for _, raw_event in events:
            event = self._decode_event(raw_event)

            if event_type is None or event.get("event_type") == event_type:
                return event

        return None

    def classify_regime(
        self,
        market_state: Dict[str, Any],
        risk_projection: Dict[str, Any],
    ) -> Dict[str, Any]:
        state_label = market_state.get("state_label", "unknown")
        stress_score = float(market_state.get("market_stress_score", 0.0) or 0.0)
        volatility_state = market_state.get("volatility_state", "unknown")
        liquidity_state = market_state.get("liquidity_state", "unknown")
        alert_state = market_state.get("alert_state", "unknown")

        risk_level = risk_projection.get("risk_level", "unknown")
        projected_var_95 = float(risk_projection.get("projected_var_95", 0.0) or 0.0)
        projected_cvar_95 = float(risk_projection.get("projected_cvar_95", 0.0) or 0.0)
        projected_drawdown = float(risk_projection.get("projected_drawdown", 0.0) or 0.0)

        if (
            state_label == "critical"
            or stress_score >= 0.90
            or projected_drawdown <= -0.08
        ):
            regime = "crisis"
            confidence = 0.94
            posture = "risk_off"
            explanation = "Critical market stress or severe projected drawdown detected."

        elif liquidity_state in {"weak", "stale"} and stress_score >= 0.70:
            regime = "liquidity_stress"
            confidence = 0.88
            posture = "raise_cash"
            explanation = "Liquidity weakness detected under elevated stress."

        elif volatility_state == "high" and risk_level in {"high", "critical"}:
            regime = "volatility_shock"
            confidence = 0.86
            posture = "increase_hedge"
            explanation = "High volatility and elevated projected portfolio risk detected."

        elif (
            state_label == "elevated_risk"
            or risk_level == "high"
            or alert_state == "active_alerting"
            or projected_var_95 >= 0.04
            or projected_cvar_95 >= 0.06
        ):
            regime = "defensive"
            confidence = 0.82
            posture = "reduce_risk"
            explanation = "Elevated risk conditions require defensive allocation posture."

        elif state_label == "normal" and stress_score <= 0.35 and risk_level in {"low", "normal", "unknown"}:
            regime = "risk_on"
            confidence = 0.76
            posture = "increase_exposure"
            explanation = "Normal market state with low stress supports risk-on posture."

        else:
            regime = "neutral"
            confidence = 0.68
            posture = "hold"
            explanation = "Mixed signals detected; maintain neutral allocation posture."

        return {
            "event_type": "regime_decision",
            "current_regime": regime,
            "confidence": confidence,
            "recommended_posture": posture,
            "state_label": state_label,
            "market_stress_score": stress_score,
            "volatility_state": volatility_state,
            "liquidity_state": liquidity_state,
            "alert_state": alert_state,
            "risk_level": risk_level,
            "projected_var_95": projected_var_95,
            "projected_cvar_95": projected_cvar_95,
            "projected_drawdown": projected_drawdown,
            "reason": explanation,
            "timestamp": self._now(),
        }

    def publish_regime_decision(self, decision: Dict[str, Any]) -> str:
        payload = {
            key: json.dumps(value) if isinstance(value, (dict, list, bool)) else str(value)
            for key, value in decision.items()
        }

        return self.redis.xadd(MARKET_SIGNALS_STREAM, payload)

    def run_once(self) -> Dict[str, Any]:
        market_state = self.get_latest_event(
            MARKET_SIGNALS_STREAM,
            event_type="live_digital_twin_state",
        )

        risk_projection = self.get_latest_event(
            RISK_EVENTS_STREAM,
            event_type="risk_projection",
        )

        if not market_state:
            raise RuntimeError("No live_digital_twin_state event found in market_signals.")

        if not risk_projection:
            raise RuntimeError("No risk_projection event found in risk_events.")

        decision = self.classify_regime(market_state, risk_projection)
        event_id = self.publish_regime_decision(decision)

        decision["redis_event_id"] = event_id
        return decision


def main() -> None:
    engine = RealtimeRegimeDecisionEngine()
    decision = engine.run_once()

    print("=" * 80)
    print("AURUM REAL-TIME REGIME DECISION ENGINE")
    print("=" * 80)
    print(f"Current Regime: {decision['current_regime']}")
    print(f"Confidence: {decision['confidence']}")
    print(f"Recommended Posture: {decision['recommended_posture']}")
    print(f"State Label: {decision['state_label']}")
    print(f"Risk Level: {decision['risk_level']}")
    print(f"Reason: {decision['reason']}")
    print(f"Redis Event ID: {decision['redis_event_id']}")


if __name__ == "__main__":
    main()