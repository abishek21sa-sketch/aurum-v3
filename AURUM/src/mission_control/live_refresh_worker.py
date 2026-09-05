"""
AURUM Mission Control 1
Always-On Refresh Worker

Purpose:
Runs the AURUM institutional cycle automatically and writes Mission Control status files.

This module does NOT rewrite the existing AURUM system.
It calls existing scripts/modules when available, and gracefully degrades when some
artifacts are missing.

Run:
    python -m src.mission_control.live_refresh_worker
"""

from __future__ import annotations

import argparse
import importlib
import json
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


ROOT = Path(__file__).resolve().parents[2]

RESULTS_DIR = ROOT / "results"
MISSION_DIR = RESULTS_DIR / "mission_control"

LATEST_REFRESH_PATH = MISSION_DIR / "latest_refresh.json"
REFRESH_HISTORY_PATH = MISSION_DIR / "refresh_history.jsonl"
SYSTEM_STATUS_PATH = MISSION_DIR / "system_status.json"


@dataclass
class RefreshResult:
    timestamp: str
    status: str
    market_data_status: str
    regime: str
    portfolio_posture: str
    execution_permission: str
    confidence: float
    biggest_risk: str
    errors: list[str]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_dirs() -> None:
    MISSION_DIR.mkdir(parents=True, exist_ok=True)


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


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload) + "\n")


def run_module(module_name: str, errors: list[str]) -> bool:
    """
    Run an existing AURUM module/script using python -m.

    If the module does not exist or fails, we record the error but continue.
    Mission Control should not die because one backend artifact is missing.
    """
    try:
        importlib.import_module(module_name)
    except Exception as exc:
        errors.append(f"SKIPPED {module_name}: import failed: {exc}")
        return False

    try:
        completed = subprocess.run(
            [sys.executable, "-m", module_name],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=180,
        )
        if completed.returncode != 0:
            err = completed.stderr.strip() or completed.stdout.strip()
            errors.append(f"FAILED {module_name}: {err[:500]}")
            return False
        return True
    except Exception as exc:
        errors.append(f"FAILED {module_name}: {exc}")
        return False


def detect_market_data_status() -> str:
    snapshot_path = RESULTS_DIR / "realtime" / "live_market_snapshot.json"
    data = read_json(snapshot_path, {})
    if not data:
        return "missing"

    generated_at = (
        data.get("generated_at")
        or data.get("timestamp")
        or data.get("as_of")
        or data.get("created_at")
    )

    if not generated_at:
        return "available"

    try:
        dt = datetime.fromisoformat(str(generated_at).replace("Z", "+00:00"))
        age_seconds = (datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).total_seconds()
        if age_seconds <= 15 * 60:
            return "fresh"
        if age_seconds <= 60 * 60:
            return "aging"
        return "stale"
    except Exception:
        return "available"


def extract_regime() -> str:
    candidates = [
        RESULTS_DIR / "regimes" / "latest_regime.json",
        RESULTS_DIR / "research" / "committee_decision.json",
        RESULTS_DIR / "research_firm" / "daily_research_firm_state.json",
        RESULTS_DIR / "portfolio_os" / "portfolio_state_machine.json",
    ]

    keys = [
        "regime",
        "current_regime",
        "latest_market_regime",
        "market_regime",
        "investment_view",
    ]

    for path in candidates:
        data = read_json(path, {})
        for key in keys:
            value = data.get(key)
            if value:
                return str(value).lower()

    return "unknown"


def extract_portfolio_posture() -> str:
    candidates = [
        RESULTS_DIR / "portfolio_os" / "portfolio_directive.json",
        RESULTS_DIR / "cio" / "cio_portfolio_directive.json",
        RESULTS_DIR / "research_firm" / "ai_research_firm_mode.json",
        RESULTS_DIR / "research" / "committee_decision.json",
    ]

    keys = [
        "portfolio_posture",
        "posture",
        "recommended_posture",
        "investment_view",
        "portfolio_view",
    ]

    for path in candidates:
        data = read_json(path, {})
        for key in keys:
            value = data.get(key)
            if value:
                return str(value).lower()

    return "unknown"


def extract_execution_permission() -> str:
    candidates = [
        RESULTS_DIR / "portfolio_os" / "portfolio_directive.json",
        RESULTS_DIR / "cio" / "cio_portfolio_directive.json",
        RESULTS_DIR / "research" / "committee_decision.json",
        RESULTS_DIR / "institutional" / "daily_institutional_cycle.json",
    ]

    for path in candidates:
        data = read_json(path, {})

        for key in ["execution_permission", "approval_status", "execution_status"]:
            value = data.get(key)
            if value:
                value = str(value).lower()
                if "block" in value or "reject" in value:
                    return "blocked"
                if "allow" in value or "clear" in value or "approved" in value:
                    return "allowed"
                return value

        allow_execution = data.get("allow_execution")
        if isinstance(allow_execution, bool):
            return "allowed" if allow_execution else "blocked"

    return "unknown"


def extract_confidence() -> float:
    candidates = [
        RESULTS_DIR / "cio" / "cio_market_thesis.json",
        RESULTS_DIR / "cio" / "cio_portfolio_directive.json",
        RESULTS_DIR / "research" / "committee_decision.json",
        RESULTS_DIR / "research_firm" / "ai_research_firm_mode.json",
        RESULTS_DIR / "portfolio_os" / "portfolio_directive.json",
    ]

    for path in candidates:
        data = read_json(path, {})
        for key in ["confidence", "cio_confidence", "overall_confidence"]:
            value = data.get(key)
            if isinstance(value, (int, float)):
                return round(float(value), 4)

    return 0.0


def extract_biggest_risk() -> str:
    candidates = [
        RESULTS_DIR / "research_firm" / "ai_research_firm_mode.json",
        RESULTS_DIR / "institutional" / "daily_institutional_cycle.json",
        RESULTS_DIR / "cio" / "cio_market_thesis.json",
        RESULTS_DIR / "reliability" / "platform_health_report.json",
    ]

    keys = [
        "highest_risk",
        "biggest_risk",
        "primary_risk",
        "top_risk",
        "risk_summary",
    ]

    for path in candidates:
        data = read_json(path, {})
        for key in keys:
            value = data.get(key)
            if value:
                return str(value)

    return "No dominant risk identified yet"


def run_existing_aurum_cycle(errors: list[str]) -> list[str]:
    """
    Calls existing modules if present.

    Keep this list conservative. Add/remove module names based on your actual repo.
    Missing modules are skipped, not fatal.
    """
    modules = [
        "scripts.generate_live_market_snapshot",
        "src.research_firm.ai_research_firm_mode",
        "src.portfolio_os.portfolio_operating_system",
        "src.cio.chief_investment_officer_agent",
    ]

    executed = []
    for module in modules:
        ok = run_module(module, errors)
        if ok:
            executed.append(module)

    return executed


def run_refresh_cycle() -> RefreshResult:
    ensure_dirs()

    errors: list[str] = []
    executed_modules = run_existing_aurum_cycle(errors)

    market_data_status = detect_market_data_status()
    regime = extract_regime()
    posture = extract_portfolio_posture()
    permission = extract_execution_permission()
    confidence = extract_confidence()
    biggest_risk = extract_biggest_risk()

    status = "success" if not errors else "partial_success"

    result = RefreshResult(
        timestamp=utc_now(),
        status=status,
        market_data_status=market_data_status,
        regime=regime,
        portfolio_posture=posture,
        execution_permission=permission,
        confidence=confidence,
        biggest_risk=biggest_risk,
        errors=errors,
    )

    payload = asdict(result)
    payload["executed_modules"] = executed_modules

    write_json(LATEST_REFRESH_PATH, payload)
    append_jsonl(REFRESH_HISTORY_PATH, payload)

    system_status = {
        "timestamp": result.timestamp,
        "mission_control_status": result.status,
        "last_refresh_status": result.status,
        "market_data_status": result.market_data_status,
        "executed_module_count": len(executed_modules),
        "error_count": len(errors),
        "dashboard_ready": True,
    }
    write_json(SYSTEM_STATUS_PATH, system_status)

    return result


def print_result(result: RefreshResult) -> None:
    print("=" * 80)
    print("AURUM MISSION CONTROL REFRESH")
    print("=" * 80)
    print(f"Timestamp:            {result.timestamp}")
    print(f"Status:               {result.status}")
    print(f"Market Data:          {result.market_data_status}")
    print(f"Regime:               {result.regime}")
    print(f"Portfolio Posture:    {result.portfolio_posture}")
    print(f"Execution Permission: {result.execution_permission}")
    print(f"CIO Confidence:       {result.confidence}")
    print(f"Biggest Risk:         {result.biggest_risk}")
    print("-" * 80)

    if result.errors:
        print("Warnings / Errors:")
        for err in result.errors:
            print(f"- {err}")
    else:
        print("All available modules completed successfully.")

    print("=" * 80)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run AURUM Mission Control refresh worker.")
    parser.add_argument("--once", action="store_true", help="Run one refresh cycle.")
    parser.add_argument("--loop", action="store_true", help="Run refresh cycle continuously.")
    parser.add_argument("--interval", type=int, default=300, help="Loop interval in seconds.")
    args = parser.parse_args()

    if not args.once and not args.loop:
        args.once = True

    if args.once:
        result = run_refresh_cycle()
        print_result(result)
        return

    while True:
        result = run_refresh_cycle()
        print_result(result)
        time.sleep(args.interval)


if __name__ == "__main__":
    main()