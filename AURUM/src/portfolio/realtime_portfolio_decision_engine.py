# src/portfolio/realtime_portfolio_decision_engine.py

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
STREAM_OPTIMIZER_EVENTS = "optimizer_events"
STREAM_PORTFOLIO_DECISIONS = "portfolio_decisions"


@dataclass
class RealtimePortfolioDecision:
    event_type: str
    timestamp_utc: str
    action: str
    urgency: str
    should_optimize: bool
    current_regime: str
    recommended_posture: str
    risk_level: str
    market_stress_score: float
    projected_var_95: float
    projected_cvar_95: float
    projected_drawdown: float
    recommended_changes: Dict[str, float]
    reason: str
    redis_event_id: Optional[str] = None


class RealtimePortfolioDecisionEngine:
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

    def build_recommended_changes(
        self,
        action: str,
        urgency: str,
    ) -> Dict[str, float]:
        if action == "pause_trading":
            return {}

        if action == "risk_off_rotation":
            return {
                "SPY": -0.07,
                "QQQ": -0.08,
                "DIA": -0.04,
                "TLT": 0.06,
                "GLD": 0.05,
                "CASH": 0.08,
            }

        if action == "rebalance_defensive":
            return {
                "SPY": -0.05,
                "QQQ": -0.05,
                "TLT": 0.04,
                "GLD": 0.03,
                "CASH": 0.03,
            }

        if action == "increase_hedge":
            return {
                "SPY": -0.03,
                "QQQ": -0.04,
                "TLT": 0.03,
                "GLD": 0.03,
                "CASH": 0.01,
            }

        if action == "increase_cash":
            return {
                "SPY": -0.03,
                "QQQ": -0.03,
                "DIA": -0.02,
                "CASH": 0.08,
            }

        if action == "reduce_equity":
            return {
                "SPY": -0.04,
                "QQQ": -0.04,
                "DIA": -0.02,
                "TLT": 0.03,
                "GLD": 0.03,
                "CASH": 0.04,
            }

        return {}

    def decide_action(
        self,
        optimizer_trigger: Dict[str, Any],
        regime_decision: Dict[str, Any],
        risk_projection: Dict[str, Any],
    ) -> tuple[str, str]:
        should_optimize = str(
            optimizer_trigger.get("should_optimize", "false")
        ).lower() == "true"

        urgency = str(optimizer_trigger.get("urgency", "none"))
        current_regime = str(regime_decision.get("current_regime", "unknown"))
        posture = str(regime_decision.get("recommended_posture", "hold"))
        risk_level = str(risk_projection.get("risk_level", "unknown"))

        projected_drawdown = float(
            risk_projection.get(
                "projected_drawdown",
                risk_projection.get("projected_expected_drawdown", 0.0),
            )
            or 0.0
        )

        stress_score = float(
            regime_decision.get(
                "market_stress_score",
                risk_projection.get("live_market_stress_score", 0.0),
            )
            or 0.0
        )

        if not should_optimize:
            return "hold", "Optimizer trigger is inactive; maintain current allocation."

        if current_regime == "crisis" or risk_level == "critical" or stress_score >= 0.85:
            return "risk_off_rotation", "Crisis regime or critical risk detected."

        if projected_drawdown <= -0.12:
            return "rebalance_defensive", "Projected drawdown exceeds defensive rebalance threshold."

        if current_regime == "liquidity_stress" or posture == "raise_cash":
            return "increase_cash", "Liquidity stress detected; raise cash allocation."

        if current_regime == "volatility_shock" or posture == "increase_hedge":
            return "increase_hedge", "Volatility shock detected; increase hedge allocation."

        if current_regime == "defensive":
            return "reduce_equity", "Defensive regime detected; reduce equity exposure."

        if posture == "reduce_risk":
            return "reduce_equity", "Risk-reduction posture selected; reduce equity exposure."

        if urgency in {"high", "critical"}:
            return "rebalance_defensive", "High optimizer urgency requires defensive rebalance."

        return "hold", "No portfolio action required beyond monitoring."

    def build_decision(
        self,
        optimizer_trigger: Dict[str, Any],
        regime_decision: Dict[str, Any],
        risk_projection: Dict[str, Any],
    ) -> RealtimePortfolioDecision:
        action, reason = self.decide_action(
            optimizer_trigger=optimizer_trigger,
            regime_decision=regime_decision,
            risk_projection=risk_projection,
        )

        urgency = str(optimizer_trigger.get("urgency", "none"))
        should_optimize = str(
            optimizer_trigger.get("should_optimize", "false")
        ).lower() == "true"

        current_regime = str(regime_decision.get("current_regime", "unknown"))
        posture = str(regime_decision.get("recommended_posture", "hold"))
        risk_level = str(risk_projection.get("risk_level", "unknown"))

        stress_score = float(
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

        changes = self.build_recommended_changes(action, urgency)

        return RealtimePortfolioDecision(
            event_type="portfolio_decision",
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            action=action,
            urgency=urgency,
            should_optimize=should_optimize,
            current_regime=current_regime,
            recommended_posture=posture,
            risk_level=risk_level,
            market_stress_score=stress_score,
            projected_var_95=projected_var_95,
            projected_cvar_95=projected_cvar_95,
            projected_drawdown=projected_drawdown,
            recommended_changes=changes,
            reason=reason,
        )

    def publish_decision(self, decision: RealtimePortfolioDecision) -> str:
        data = asdict(decision)
        data.pop("redis_event_id", None)

        payload = {
            key: json.dumps(value) if isinstance(value, (dict, list, bool)) else str(value)
            for key, value in data.items()
            if value is not None
        }

        return self.redis_client.xadd(STREAM_PORTFOLIO_DECISIONS, payload)

    def run_once(self) -> RealtimePortfolioDecision:
        optimizer_trigger = self.latest_event(
            STREAM_OPTIMIZER_EVENTS,
            event_type="optimizer_trigger",
        )

        digital_twin_state = self.latest_event(
            STREAM_MARKET_SIGNALS,
            event_type="live_digital_twin_state",
        )

        risk_projection = self.latest_event(
            STREAM_RISK_EVENTS,
            event_type="risk_projection",
        )

        if not optimizer_trigger:
            raise RuntimeError(
                "No optimizer_trigger event found in optimizer_events."
            )

        if not digital_twin_state:
            raise RuntimeError(
                "No live_digital_twin_state event found in market_signals."
            )

        if not risk_projection:
            raise RuntimeError(
                "No risk_projection event found in risk_events."
            )

        regime_decision = {
            "current_regime": digital_twin_state.get(
                "current_regime",
                "unknown",
            ),
            "recommended_posture": (
                "reduce_risk"
                if digital_twin_state.get("state_label")
                in {"watch", "critical"}
                else "hold"
            ),
            "market_stress_score": float(
                digital_twin_state.get(
                    "market_stress_score",
                    0.0,
                )
                or 0.0
            ),
        }

        decision = self.build_decision(
            optimizer_trigger=optimizer_trigger,
            regime_decision=regime_decision,
            risk_projection=risk_projection,
        )

        redis_event_id = self.publish_decision(decision)
        decision.redis_event_id = redis_event_id

        return decision

    def print_decision(self, decision: RealtimePortfolioDecision) -> None:
        print("=" * 80)
        print("AURUM REAL-TIME PORTFOLIO DECISION ENGINE")
        print("=" * 80)
        print(f"Action: {decision.action}")
        print(f"Urgency: {decision.urgency}")
        print(f"Should Optimize: {decision.should_optimize}")
        print(f"Current Regime: {decision.current_regime}")
        print(f"Recommended Posture: {decision.recommended_posture}")
        print(f"Risk Level: {decision.risk_level}")
        print(f"Market Stress Score: {decision.market_stress_score}")
        print(f"Projected VaR 95: {decision.projected_var_95:.4f}")
        print(f"Projected CVaR 95: {decision.projected_cvar_95:.4f}")
        print(f"Projected Drawdown: {decision.projected_drawdown:.4f}")
        print(f"Recommended Changes: {decision.recommended_changes}")
        print(f"Reason: {decision.reason}")
        print(f"Redis Event ID: {decision.redis_event_id}")


def main() -> None:
    engine = RealtimePortfolioDecisionEngine()
    decision = engine.run_once()
    engine.print_decision(decision)


if __name__ == "__main__":
    main()