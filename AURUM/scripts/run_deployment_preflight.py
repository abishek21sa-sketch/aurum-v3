"""Generate the AURUM deployment-boundary preflight artifact."""

from __future__ import annotations

import json
from pathlib import Path

from src.institutional.deployment_preflight import build_deployment_preflight
from src.institutional.enterprise_platform import build_enterprise_platform_status
from src.institutional.ai_evaluation import build_ai_evaluation
from src.institutional.control_plane import build_control_plane
from src.institutional.operations_contract import build_operations_status
from src.institutional.live_data_contract import build_live_data_status
from src.institutional.model_validation import build_model_validation
from src.institutional.mars_cvar_product import build_reference_product_evidence


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    payload = build_deployment_preflight(ROOT)
    output = ROOT / "artifacts/compliance/deployment_preflight.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    evidence = build_reference_product_evidence(ROOT)
    generated = {
        "live_data_status": build_live_data_status(ROOT),
        "model_validation": build_model_validation(ROOT, evidence),
        "enterprise_platform": build_enterprise_platform_status(ROOT),
        "ai_evaluation": build_ai_evaluation(ROOT),
        "control_plane": build_control_plane(ROOT, evidence),
        "operations_status": build_operations_status(ROOT),
    }
    for name, value in generated.items():
        artifact = ROOT / "artifacts" / "compliance" / f"{name}.json"
        artifact.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"AURUM_DEPLOYMENT_PREFLIGHT={payload['research_gate']}")
    print(f"AURUM_PRODUCTION_GATE={payload['production_gate']}")
    print(f"AURUM_PREFLIGHT_CHECKS={payload['summary']['passed_checks']}/{payload['summary']['total_checks']}")
    print(f"AURUM_PREFLIGHT_BLOCKERS={payload['summary']['production_blockers']}")
    return 0 if payload["research_gate"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
