# src/execution/rebalance_scheduler.py

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any


EXECUTION_DIR = Path("results/execution")

REBALANCE_SUMMARY_PATH = EXECUTION_DIR / "rebalance_decision_summary.json"
TURNOVER_SUMMARY_PATH = EXECUTION_DIR / "turnover_control_summary.json"

REBALANCE_SCHEDULE_PATH = EXECUTION_DIR / "rebalance_schedule.json"

DEFAULT_SCHEDULE_CONFIG = {
    "calendar_frequency": "monthly",
    "days_since_last_rebalance": 35,
    "calendar_rebalance_days": {
        "weekly": 7,
        "monthly": 30,
        "quarterly": 90,
        "annual": 365,
    },
    "regime_change_detected": True,
    "risk_trigger_active": False,
    "volatility_trigger_active": False,
    "drawdown_trigger_active": False,
    "min_turnover_to_rebalance": 0.05,
    "max_cost_bps_allowed": 5.0,
}


def ensure_execution_dir() -> None:
    EXECUTION_DIR.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing required file: {path}. "
            "Run previous execution-layer modules first."
        )

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def evaluate_calendar_trigger(config: Dict[str, Any]) -> Dict[str, Any]:
    frequency = config["calendar_frequency"]
    required_days = config["calendar_rebalance_days"].get(frequency)

    if required_days is None:
        raise ValueError(f"Unsupported calendar frequency: {frequency}")

    days_since_last = int(config["days_since_last_rebalance"])
    triggered = days_since_last >= required_days

    return {
        "triggered": triggered,
        "frequency": frequency,
        "days_since_last_rebalance": days_since_last,
        "required_days": required_days,
    }


def evaluate_event_triggers(config: Dict[str, Any]) -> Dict[str, Any]:
    triggers = {
        "regime_change_detected": bool(config["regime_change_detected"]),
        "risk_trigger_active": bool(config["risk_trigger_active"]),
        "volatility_trigger_active": bool(config["volatility_trigger_active"]),
        "drawdown_trigger_active": bool(config["drawdown_trigger_active"]),
    }

    return {
        "triggered": any(triggers.values()),
        "details": triggers,
    }


def evaluate_turnover_trigger(
    turnover_summary: Dict[str, Any],
    config: Dict[str, Any],
) -> Dict[str, Any]:
    filtered_turnover = float(turnover_summary["filtered_turnover"])
    threshold = float(config["min_turnover_to_rebalance"])

    return {
        "triggered": filtered_turnover >= threshold,
        "filtered_turnover": filtered_turnover,
        "threshold": threshold,
    }


def evaluate_cost_gate(
    rebalance_summary: Dict[str, Any],
    config: Dict[str, Any],
) -> Dict[str, Any]:
    approved_cost_bps = float(
        rebalance_summary["approved_estimated_cost_bps_of_portfolio"]
    )
    max_allowed = float(config["max_cost_bps_allowed"])

    return {
        "passed": approved_cost_bps <= max_allowed,
        "approved_cost_bps": approved_cost_bps,
        "max_allowed_cost_bps": max_allowed,
    }


def determine_rebalance_decision(
    calendar_trigger: Dict[str, Any],
    event_trigger: Dict[str, Any],
    turnover_trigger: Dict[str, Any],
    cost_gate: Dict[str, Any],
) -> Dict[str, Any]:
    trigger_reasons = []

    if calendar_trigger["triggered"]:
        trigger_reasons.append("calendar_schedule_due")

    if event_trigger["triggered"]:
        trigger_reasons.append("event_trigger_active")

    if turnover_trigger["triggered"]:
        trigger_reasons.append("turnover_above_threshold")

    trigger_active = len(trigger_reasons) > 0

    should_rebalance = trigger_active and cost_gate["passed"]

    if should_rebalance:
        recommendation = "REBALANCE_NOW"
    elif trigger_active and not cost_gate["passed"]:
        recommendation = "DEFER_COST_TOO_HIGH"
    else:
        recommendation = "NO_REBALANCE"

    return {
        "should_rebalance": should_rebalance,
        "recommendation": recommendation,
        "trigger_reasons": trigger_reasons,
        "cost_gate_passed": cost_gate["passed"],
    }


def build_rebalance_schedule(
    config: Dict[str, Any],
    turnover_summary: Dict[str, Any],
    rebalance_summary: Dict[str, Any],
) -> Dict[str, Any]:
    now = datetime.now()
    frequency = config["calendar_frequency"]
    required_days = config["calendar_rebalance_days"][frequency]

    calendar_trigger = evaluate_calendar_trigger(config)
    event_trigger = evaluate_event_triggers(config)
    turnover_trigger = evaluate_turnover_trigger(turnover_summary, config)
    cost_gate = evaluate_cost_gate(rebalance_summary, config)

    decision = determine_rebalance_decision(
        calendar_trigger=calendar_trigger,
        event_trigger=event_trigger,
        turnover_trigger=turnover_trigger,
        cost_gate=cost_gate,
    )

    next_calendar_date = now + timedelta(days=required_days)

    schedule = {
        "timestamp": now.isoformat(timespec="seconds"),
        "calendar_trigger": calendar_trigger,
        "event_trigger": event_trigger,
        "turnover_trigger": turnover_trigger,
        "cost_gate": cost_gate,
        "decision": decision,
        "next_calendar_rebalance_estimate": next_calendar_date.date().isoformat(),
    }

    return schedule


def save_rebalance_schedule(schedule: Dict[str, Any]) -> None:
    ensure_execution_dir()

    with REBALANCE_SCHEDULE_PATH.open("w", encoding="utf-8") as f:
        json.dump(schedule, f, indent=4)


def print_rebalance_schedule(schedule: Dict[str, Any]) -> None:
    decision = schedule["decision"]

    print("=" * 80)
    print("AURUM REBALANCE SCHEDULING ENGINE")
    print("=" * 80)

    print("\nCALENDAR TRIGGER")
    print("-" * 80)
    cal = schedule["calendar_trigger"]
    print(f"Frequency: {cal['frequency']}")
    print(f"Days Since Last Rebalance: {cal['days_since_last_rebalance']}")
    print(f"Required Days: {cal['required_days']}")
    print(f"Triggered: {cal['triggered']}")

    print("\nEVENT TRIGGERS")
    print("-" * 80)
    for name, active in schedule["event_trigger"]["details"].items():
        print(f"{name}: {active}")
    print(f"Any Event Triggered: {schedule['event_trigger']['triggered']}")

    print("\nTURNOVER TRIGGER")
    print("-" * 80)
    turn = schedule["turnover_trigger"]
    print(f"Filtered Turnover: {turn['filtered_turnover']:.2%}")
    print(f"Threshold: {turn['threshold']:.2%}")
    print(f"Triggered: {turn['triggered']}")

    print("\nCOST GATE")
    print("-" * 80)
    cost = schedule["cost_gate"]
    print(f"Approved Cost: {cost['approved_cost_bps']:.2f} bps")
    print(f"Max Allowed Cost: {cost['max_allowed_cost_bps']:.2f} bps")
    print(f"Passed: {cost['passed']}")

    print("\nREBALANCE DECISION")
    print("-" * 80)
    print(f"Recommendation: {decision['recommendation']}")
    print(f"Should Rebalance: {decision['should_rebalance']}")
    print(f"Trigger Reasons: {decision['trigger_reasons']}")
    print(f"Next Calendar Estimate: {schedule['next_calendar_rebalance_estimate']}")

    print("\nOUTPUTS")
    print("-" * 80)
    print(f"Rebalance Schedule: {REBALANCE_SCHEDULE_PATH}")

    print("\nAURUM REBALANCE SCHEDULING ENGINE COMPLETE")


def main() -> None:
    ensure_execution_dir()

    turnover_summary = load_json(TURNOVER_SUMMARY_PATH)
    rebalance_summary = load_json(REBALANCE_SUMMARY_PATH)

    schedule = build_rebalance_schedule(
        config=DEFAULT_SCHEDULE_CONFIG,
        turnover_summary=turnover_summary,
        rebalance_summary=rebalance_summary,
    )

    save_rebalance_schedule(schedule)
    print_rebalance_schedule(schedule)


if __name__ == "__main__":
    main()