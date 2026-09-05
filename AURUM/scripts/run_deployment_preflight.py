"""Generate the AURUM deployment-boundary preflight artifact."""

from __future__ import annotations

import json
from pathlib import Path

from src.institutional.deployment_preflight import build_deployment_preflight


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    payload = build_deployment_preflight(ROOT)
    output = ROOT / "artifacts/compliance/deployment_preflight.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"AURUM_DEPLOYMENT_PREFLIGHT={payload['research_gate']}")
    print(f"AURUM_PRODUCTION_GATE={payload['production_gate']}")
    print(f"AURUM_PREFLIGHT_CHECKS={payload['summary']['passed_checks']}/{payload['summary']['total_checks']}")
    print(f"AURUM_PREFLIGHT_BLOCKERS={payload['summary']['production_blockers']}")
    return 0 if payload["research_gate"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
