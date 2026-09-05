"""
AURUM Mission Control Validator

Checks that all Mission Control outputs are fresh,
sane, and ready for demo.

Run:
    python scripts/validate_mission_control.py
"""

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MISSION_DIR = ROOT / "results" / "mission_control"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def check_file(
    name: str,
    path: Path,
    max_age_minutes: int = 15,
    sanity_checks: dict = None,
) -> bool:
    if not path.exists():
        print(f"  FAIL {name}: FILE MISSING")
        return False

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"  FAIL {name}: JSON ERROR {e}")
        return False

    # Freshness check
    ts = data.get("timestamp") or data.get("generated_at")
    if ts:
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            age_mins = (utc_now() - dt.astimezone(timezone.utc)).total_seconds() / 60
            if age_mins > max_age_minutes:
                print(f"  WARN {name}: STALE ({int(age_mins)}m old, max {max_age_minutes}m)")
            else:
                age_str = f"{int(age_mins)}m ago"
        except Exception:
            age_str = "unknown age"
    else:
        age_str = "no timestamp"

    # Sanity checks
    if sanity_checks:
        for field, check in sanity_checks.items():
            value = data
            for key in field.split("."):
                if isinstance(value, dict):
                    value = value.get(key)
                else:
                    value = None
                    break
            if not check(value):
                print(f"  FAIL {name}: sanity failed on {field} = {value}")
                return False

    age_display = f"{int(age_mins)}m ago" if ts else "no timestamp"
    print(f"  OK   {name} ({age_display})")
    return True


def main() -> None:
    print("=" * 60)
    print("AURUM MISSION CONTROL VALIDATOR")
    print(f"Time: {utc_now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 60)

    checks = [
        ("dashboard_state.json", MISSION_DIR / "dashboard_state.json", 15, None),
        ("recommendation_card.json", MISSION_DIR / "recommendation_card.json", 15, None),
        ("portfolio_state.json", MISSION_DIR / "portfolio_state.json", 15, {
            "portfolio_value": lambda v: v is not None and 50000 < float(v or 0) < 500000,
            "daily_pnl": lambda v: v is not None and -50000 < float(v or 0) < 50000,
        }),
        ("alpaca_state.json", MISSION_DIR / "alpaca_state.json", 15, {
            "account.portfolio_value": lambda v: v is not None and 50000 < float(v or 0) < 500000,
        }),
        ("provider_status.json", MISSION_DIR / "provider_status.json", 15, None),
        ("infrastructure_status.json", MISSION_DIR / "infrastructure_status.json", 15, None),
        ("agent_health.json", MISSION_DIR / "agent_health.json", 15, None),
        ("copilot_response.json", MISSION_DIR / "copilot_response.json", 60, {
            "source": lambda v: v in ("groq_llama3.3_70b", "rule_based", "fallback"),
        }),
        ("scheduler_status.json", MISSION_DIR / "scheduler_status.json", 600, None),
        ("runner_status.json", MISSION_DIR / "runner_status.json", 15, None),
    ]

    passed = 0
    failed = 0
    for name, path, max_age, sanity in checks:
        ok = check_file(name, path, max_age, sanity)
        if ok:
            passed += 1
        else:
            failed += 1

    # Check dashboard file
    dash = ROOT / "dashboard/aurum_mission_control.py"
    if dash.exists():
        print(f"  OK   dashboard/aurum_mission_control.py ({dash.stat().st_size // 1024}KB)")
        passed += 1
    else:
        print("  FAIL dashboard/aurum_mission_control.py: MISSING")
        failed += 1

    print()
    print(f"Result: {passed}/{passed+failed} checks passed")
    if failed == 0:
        print("AURUM Mission Control is DEMO READY.")
    else:
        print(f"WARNING: {failed} issues need attention.")
    print("=" * 60)


if __name__ == "__main__":
    main()
