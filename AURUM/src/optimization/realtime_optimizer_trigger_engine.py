# src/optimization/realtime_optimizer_trigger_engine.py

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import redis


REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0

STREAM_MARKET_SIGNALS = "market_signals"
STREAM_RISK_EVENTS = "risk_events"
STREAM_ALERTS_CANDIDATES = ["market_alerts", "alerts"]
STREAM_OPTIMIZER_EVENTS = "optimizer_events"


@dataclass
class RealtimeOptimizerTrigger:
    event_type: str
    timestamp_utc: str
    should_optimize: bool
    trigger_reason: str
    urgency: str
    current_regime: str
    recommended_posture: str
    regime_confidence: float
    risk_level: str
    market_stress_score: float
    projected_var_95: float
    projected_cvar_95: float
    projected_drawdown: float
    alert_state: str
    redis_event_id: Optional[str] = None


class RealtimeOptimizerTriggerEngine:
    def __init__(self) -> None:
        self.redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True,
        )

    def decode_event(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        decoded = {}

        for key, value in raw_event.items():
            try:
                decoded[key] = json.loads(value)
            except Exception:
                decoded[key] = value

        return decoded

    def latest_event(
        self,
        stream: str,
        event_type: Optional[str] = None,
        lookback: int = 100,
    ) -> Optional[Dict[str, Any]]:
        rows = self.redis_client.xrevrange(stream, count=lookback)

        for _, raw_event in rows:
            event = self.decode_event(raw_event)

            if event_type is None or event.get("event_type") == event_type:
                return event

        return None

    def stream_length(self, stream: str) -> int:
        try:
            return int(self.redis_client.xlen(stream))
        except Exception:
            return 0

    def latest_alert_state(self) -> str:
        for stream in STREAM_ALERTS_CANDIDATES:
            if self.stream_length(stream) > 0:
                return "active_or_recent_alerts"
        return "quiet"

    def build_trigger(
        self,
        regime_decision: Dict[str, Any],
        risk_projection: Dict[str, Any],
    ) -> RealtimeOptimizerTrigger:
        current_regime = str(regime_decision.get("current_regime", "unknown"))
        recommended_posture = str(regime_decision.get("recommended_posture", "hold"))
        regime_confidence = float(regime_decision.get("confidence", 0.0) or 0.0)

        risk_level = str(risk_projection.get("risk_level", "unknown"))
        market_stress_score = float(
            regime_decision.get(
                "market_stress_score",
                risk_projection.get("live_market_stress_score", 0.0),
            )
            or 0.0
        )

        projected_var_95 = float(risk_projection.get("projected_var_95", 0.0) or 0.0)
        projected_cvar_95 = float(risk_projection.get("projected_cvar_95", 0.0) or 0.0)
        projected_drawdown = float(
            risk_projection.get(
                "projected_drawdown",
                risk_projection.get("projected_expected_drawdown", 0.0),
            )
            or 0.0
        )

        alert_state = str(regime_decision.get("alert_state", self.latest_alert_state()))

        should_optimize = False
        urgency = "none"
        reasons = []

        if current_regime in {"crisis", "liquidity_stress", "volatility_shock"}:
            should_optimize = True
            urgency = "critical"
            reasons.append(f"regime_shift_to_{current_regime}")

        if current_regime == "defensive":
            should_optimize = True
            urgency = max(urgency, "high", key=["none", "low", "medium", "high", "critical"].index)
            reasons.append("defensive_regime_detected")

        if risk_level in {"high", "critical"}:
            should_optimize = True
            urgency = "critical" if risk_level == "critical" else max(
                urgency,
                "high",
                key=["none", "low", "medium", "high", "critical"].index,
            )
            reasons.append(f"{risk_level}_risk_level")

        if market_stress_score >= 0.75:
            should_optimize = True
            urgency = "critical"
            reasons.append("market_stress_threshold_breached")
        elif market_stress_score >= 0.50:
            should_optimize = True
            urgency = max(urgency, "high", key=["none", "low", "medium", "high", "critical"].index)
            reasons.append("elevated_market_stress")

        if projected_drawdown <= -0.08:
            should_optimize = True
            urgency = max(urgency, "high", key=["none", "low", "medium", "high", "critical"].index)
            reasons.append("projected_drawdown_threshold_breached")

        if projected_var_95 >= 0.10 or projected_cvar_95 >= 0.08:
            should_optimize = True
            urgency = max(urgency, "medium", key=["none", "low", "medium", "high", "critical"].index)
            reasons.append("projected_tail_risk_elevated")

        if alert_state in {"active_alerting", "active_or_recent_alerts"}:
            should_optimize = True
            urgency = max(urgency, "medium", key=["none", "low", "medium", "high", "critical"].index)
            reasons.append("active_alert_context")

        if recommended_posture in {"risk_off", "reduce_risk", "raise_cash", "increase_hedge"}:
            should_optimize = True
            urgency = max(urgency, "medium", key=["none", "low", "medium", "high", "critical"].index)
            reasons.append(f"posture_{recommended_posture}")

        if not reasons:
            reasons.append("no_optimizer_trigger_conditions_met")
            urgency = "none"

        return RealtimeOptimizerTrigger(
            event_type="optimizer_trigger",
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            should_optimize=should_optimize,
            trigger_reason=";".join(reasons),
            urgency=urgency,
            current_regime=current_regime,
            recommended_posture=recommended_posture,
            regime_confidence=regime_confidence,
            risk_level=risk_level,
            market_stress_score=market_stress_score,
            projected_var_95=projected_var_95,
            projected_cvar_95=projected_cvar_95,
            projected_drawdown=projected_drawdown,
            alert_state=alert_state,
        )

    def publish_trigger(self, trigger: RealtimeOptimizerTrigger) -> str:
        data = asdict(trigger)
        data.pop("redis_event_id", None)

        payload = {
            key: json.dumps(value) if isinstance(value, (dict, list, bool)) else str(value)
            for key, value in data.items()
            if value is not None
        }

        return self.redis_client.xadd(STREAM_OPTIMIZER_EVENTS, payload)

    def run_once(self) -> RealtimeOptimizerTrigger:
        regime_decision = self.latest_event(
            STREAM_MARKET_SIGNALS,
            event_type="regime_decision",
        )

        risk_projection = self.latest_event(
            STREAM_RISK_EVENTS,
            event_type="risk_projection",
        )

        if not regime_decision:
            raise RuntimeError("No regime_decision event found in market_signals.")

        if not risk_projection:
            raise RuntimeError("No risk_projection event found in risk_events.")

        trigger = self.build_trigger(regime_decision, risk_projection)
        redis_event_id = self.publish_trigger(trigger)
        trigger.redis_event_id = redis_event_id

        return trigger

    def print_trigger(self, trigger: RealtimeOptimizerTrigger) -> None:
        print("=" * 80)
        print("AURUM REAL-TIME OPTIMIZER TRIGGER ENGINE")
        print("=" * 80)
        print(f"Should Optimize: {trigger.should_optimize}")
        print(f"Urgency: {trigger.urgency}")
        print(f"Trigger Reason: {trigger.trigger_reason}")
        print(f"Current Regime: {trigger.current_regime}")
        print(f"Recommended Posture: {trigger.recommended_posture}")
        print(f"Risk Level: {trigger.risk_level}")
        print(f"Market Stress Score: {trigger.market_stress_score}")
        print(f"Projected VaR 95: {trigger.projected_var_95:.4f}")
        print(f"Projected CVaR 95: {trigger.projected_cvar_95:.4f}")
        print(f"Projected Drawdown: {trigger.projected_drawdown:.4f}")
        print(f"Alert State: {trigger.alert_state}")
        print(f"Redis Event ID: {trigger.redis_event_id}")


def main() -> None:
    engine = RealtimeOptimizerTriggerEngine()
    trigger = engine.run_once()
    engine.print_trigger(trigger)


if __name__ == "__main__":
    main()