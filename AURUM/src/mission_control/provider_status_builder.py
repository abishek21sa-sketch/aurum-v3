"""
AURUM Mission Control
Provider Status Builder

Output:
    results/mission_control/provider_status.json

Run:
    python -m src.mission_control.provider_status_builder
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MISSION_DIR = ROOT / "results" / "mission_control"
PROVIDER_STATUS_PATH = MISSION_DIR / "provider_status.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def build_provider_status() -> dict[str, Any]:
    # Load env
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

    active_provider = "yfinance+finnhub" if os.getenv("FINNHUB_API_KEY") else "yfinance"

    providers = {
        "yfinance": {
            "provider": "yfinance",
            "interface_exists": True,
            "keys_required": False,
            "keys_configured": True,
            "production_ready": True,
            "status": "active" if active_provider == "yfinance" else "available",
            "notes": "Default research-grade market data feed.",
        },
        "alpaca": {
            "provider": "alpaca",
            "interface_exists": True,
            "keys_required": True,
            "keys_configured": bool(os.getenv("ALPACA_API_KEY") and os.getenv("ALPACA_SECRET_KEY")),
            "production_ready": bool(os.getenv("ALPACA_API_KEY") and os.getenv("ALPACA_SECRET_KEY")),
            "status": "active" if active_provider == "alpaca" else "unavailable_no_keys",
            "notes": "Requires ALPACA_API_KEY and ALPACA_SECRET_KEY.",
        },
        "polygon": {
            "provider": "polygon",
            "interface_exists": True,
            "keys_required": True,
            "keys_configured": bool(os.getenv("POLYGON_API_KEY")),
            "production_ready": bool(os.getenv("POLYGON_API_KEY")),
            "status": "active" if active_provider == "polygon" else "unavailable_no_keys",
            "notes": "Requires POLYGON_API_KEY.",
        },
        "finnhub": {
            "provider": "finnhub",
            "interface_exists": True,
            "keys_required": True,
            "keys_configured": bool(os.getenv("FINNHUB_API_KEY")),
            "production_ready": bool(os.getenv("FINNHUB_API_KEY")),
            "status": "active" if os.getenv("FINNHUB_API_KEY") else "unavailable_no_keys",
            "notes": "Real-time quotes and news. Used alongside yfinance.",
        },
    }

    for name, data in providers.items():
        if name != active_provider and data["keys_configured"]:
            data["status"] = "available"

        if name == active_provider and not data["keys_configured"] and data["keys_required"]:
            data["status"] = "active_but_missing_keys"

    payload = {
        "timestamp": utc_now(),
        "active_provider": active_provider,
        "providers": providers,
        "summary": {
            "active_feed": active_provider,
            "available_interfaces": ["yfinance", "finnhub", "alpaca", "polygon"],
            "production_ready": [
                name for name, data in providers.items() if data["production_ready"]
            ],
        },
    }

    write_json(PROVIDER_STATUS_PATH, payload)
    return payload


def main() -> None:
    status = build_provider_status()

    print("=" * 80)
    print("AURUM PROVIDER STATUS")
    print("=" * 80)
    print(f"Saved: {PROVIDER_STATUS_PATH.relative_to(ROOT)}")
    print(f"Active Provider: {status['active_provider']}")
    print(f"Production Ready: {', '.join(status['summary']['production_ready'])}")
    print("=" * 80)


if __name__ == "__main__":
    main()