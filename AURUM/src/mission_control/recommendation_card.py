"""
AURUM Mission Control 4
Recommendation Card

Purpose:
Converts AURUM intelligence into one clear action card.

Output:
    results/mission_control/recommendation_card.json

Run:
    python -m src.mission_control.recommendation_card
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = ROOT / "results"
MISSION_DIR = RESULTS_DIR / "mission_control"

DASHBOARD_STATE_PATH = MISSION_DIR / "dashboard_state.json"
RECOMMENDATION_CARD_PATH = MISSION_DIR / "recommendation_card.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path, default: Any = None) -> Any:
    if default is None:
        default = {}
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default
    return default


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def infer_recommended_action(posture: str, permission: str, regime: str) -> str:
    posture = posture.lower()
    permission = permission.lower()
    regime = regime.lower()

    if permission == "blocked":
        if posture == "defensive" or regime == "defensive":
            return "prepare_defensive_rebalance"
        return "hold_until_governance_clears"

    if posture == "defensive" or regime == "defensive":
        return "reduce_equity_risk"

    if posture in {"risk_on", "risk-on"} or regime in {"risk_on", "risk-on"}:
        return "increase_risk_selectively"

    if posture == "normal" or regime == "normal":
        return "maintain_balanced_allocation"

    return "maintain_current_portfolio"


def build_top_reasons(
    posture: str,
    permission: str,
    regime: str,
    biggest_risk: str,
    confidence: float,
    risk_regime: dict[str, Any],
) -> list[str]:
    reasons: list[str] = []

    if biggest_risk and biggest_risk != "No dominant risk identified yet":
        reasons.append(f"Biggest identified risk is {biggest_risk}")

    if regime and regime != "unknown":
        reasons.append(f"Current regime is {regime}")

    if posture and posture != "unknown":
        reasons.append(f"Portfolio posture is {posture}")

    if permission == "blocked":
        reasons.append("Execution is blocked by governance controls")
    elif permission == "allowed":
        reasons.append("Execution is allowed by governance controls")
    elif permission == "review_required":
        reasons.append("Execution requires additional governance review")

    cvar = risk_regime.get("cvar")
    if cvar is not None:
        reasons.append(f"Tail-risk metric CVaR is currently {cvar}")

    drawdown = risk_regime.get("drawdown")
    if drawdown is not None:
        reasons.append(f"Drawdown metric is currently {drawdown}")

    anomalies = risk_regime.get("anomalies", [])
    if isinstance(anomalies, list) and anomalies:
        reasons.append(f"{len(anomalies)} anomaly alert(s) are active")

    if confidence >= 0.80:
        reasons.append("CIO confidence is high")
    elif confidence >= 0.60:
        reasons.append("CIO confidence is moderate")
    else:
        reasons.append("CIO confidence is low or unavailable")

    return reasons[:5]


def infer_next_best_action(
    recommended_action: str,
    permission: str,
    posture: str,
    biggest_risk: str,
) -> str:
    if permission == "blocked":
        return "Maintain current portfolio until governance clears execution."

    if recommended_action == "reduce_equity_risk":
        return "Reduce equity exposure and increase defensive allocation according to the approved optimizer output."

    if recommended_action == "prepare_defensive_rebalance":
        return "Prepare defensive rebalance instructions, but do not execute until governance permission changes."

    if recommended_action == "increase_risk_selectively":
        return "Increase risk selectively only in assets with favorable regime, liquidity, and risk-budget support."

    if recommended_action == "maintain_balanced_allocation":
        return "Maintain balanced allocation and continue monitoring for regime or tail-risk changes."

    if biggest_risk and biggest_risk != "No dominant risk identified yet":
        return f"Monitor {biggest_risk} closely and wait for a clearer CIO directive."

    return "Maintain current portfolio and continue monitoring live market, risk, and governance signals."


def build_recommendation_card() -> dict[str, Any]:
    MISSION_DIR.mkdir(parents=True, exist_ok=True)

    dashboard_state = read_json(DASHBOARD_STATE_PATH, {})

    mission = dashboard_state.get("mission_control", {})
    risk_regime = dashboard_state.get("risk_regime", {})
    portfolio_directive = dashboard_state.get("portfolio_directive", {})

    regime = str(mission.get("current_regime", "unknown")).lower()
    posture = str(mission.get("portfolio_posture", "unknown")).lower()
    permission = str(mission.get("execution_permission", "unknown")).lower()
    confidence = safe_float(mission.get("cio_confidence", 0.0))
    biggest_risk = str(mission.get("biggest_risk", "No dominant risk identified yet"))

    recommended_action = (
        mission.get("recommended_action")
        or portfolio_directive.get("recommended_action")
        or infer_recommended_action(posture, permission, regime)
    )

    if recommended_action in {"", None, "unknown"}:
        recommended_action = infer_recommended_action(posture, permission, regime)

    top_reasons = build_top_reasons(
        posture=posture,
        permission=permission,
        regime=regime,
        biggest_risk=biggest_risk,
        confidence=confidence,
        risk_regime=risk_regime,
    )

    next_best_action = infer_next_best_action(
        recommended_action=str(recommended_action),
        permission=permission,
        posture=posture,
        biggest_risk=biggest_risk,
    )

    card = {
        "timestamp": utc_now(),
        "portfolio_posture": posture,
        "recommended_action": str(recommended_action),
        "execution_permission": permission,
        "confidence": confidence,
        "biggest_risk": biggest_risk,
        "top_reasons": top_reasons,
        "next_best_action": next_best_action,
        "decision_summary": (
            f"AURUM is currently {posture} with execution {permission}. "
            f"The recommended action is {recommended_action}. "
            f"Primary risk: {biggest_risk}."
        ),
    }

    write_json(RECOMMENDATION_CARD_PATH, card)
    return card


def print_summary(card: dict[str, Any]) -> None:
    print("=" * 80)
    print("AURUM RECOMMENDATION CARD")
    print("=" * 80)
    print(f"Saved:                {RECOMMENDATION_CARD_PATH.relative_to(ROOT)}")
    print(f"Portfolio Posture:    {card.get('portfolio_posture')}")
    print(f"Recommended Action:   {card.get('recommended_action')}")
    print(f"Execution Permission: {card.get('execution_permission')}")
    print(f"Confidence:           {card.get('confidence')}")
    print(f"Biggest Risk:         {card.get('biggest_risk')}")
    print("-" * 80)
    print("Top Reasons:")
    for reason in card.get("top_reasons", []):
        print(f"- {reason}")
    print("-" * 80)
    print(f"Next Best Action:     {card.get('next_best_action')}")
    print("=" * 80)


def main() -> None:
    card = build_recommendation_card()
    print_summary(card)


if __name__ == "__main__":
    main()