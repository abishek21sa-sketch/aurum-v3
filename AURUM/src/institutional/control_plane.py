"""Unified enterprise control-plane summary for the AURUM handoff.

The summary intentionally reports three different denominators: repository
engineering coverage, deployment preflight coverage, and customer acceptance
evidence. Combining those into one percentage would overstate readiness.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from src.institutional.ai_evaluation import build_ai_evaluation
from src.institutional.deployment_preflight import build_deployment_preflight
from src.institutional.enterprise_platform import build_enterprise_platform_status
from src.institutional.enterprise_readiness import build_enterprise_readiness
from src.institutional.live_data_contract import build_live_data_status
from src.institutional.model_validation import build_model_validation


CONTROL_PLANE_SCHEMA_VERSION = "1.0"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _coverage(passed: int, total: int) -> dict[str, Any]:
    return {"passed": passed, "total": total, "percent": round((passed / total) * 100, 1) if total else 0.0}


def build_control_plane(root: Path, evidence: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Aggregate the six readiness areas without collapsing their boundaries."""
    if evidence is None:
        from src.institutional.mars_cvar_product import build_reference_product_evidence

        evidence = build_reference_product_evidence(root)
    readiness = build_enterprise_readiness(root, evidence)
    preflight = build_deployment_preflight(root)
    data_status = build_live_data_status(root)
    model_validation = build_model_validation(root, evidence)
    enterprise = build_enterprise_platform_status(root)
    ai_evaluation = build_ai_evaluation(root)

    repository_areas = [
        {"area": "ai_intelligence", "status": ai_evaluation["status"], "evidence": "/v1/platform/ai-evaluation"},
        {"area": "governed_live_data", "status": data_status["status"], "evidence": "/v1/platform/data-status"},
        {"area": "model_validation", "status": model_validation["status"], "evidence": "/v1/platform/model-validation"},
        {"area": "enterprise_platform", "status": enterprise["status"], "evidence": "/v1/platform/enterprise-status"},
        {"area": "deployment_controls", "status": "PASS" if preflight["research_gate"] == "PASS" else "FAIL", "evidence": "/v1/platform/deployment-preflight"},
        {"area": "customer_packaging", "status": "PASS" if readiness["release_gate"] == "PASS" else "FAIL", "evidence": "/v1/platform/readiness"},
    ]
    accepted_statuses = {"PASS", "REFERENCE_ONLY", "READY_FOR_INDEPENDENT_REVIEW", "INTEGRATION_READY_NOT_PRODUCTION"}
    repository_passed = sum(item["status"] in accepted_statuses for item in repository_areas)
    deployment_summary = preflight.get("summary", {})
    customer_controls = enterprise.get("required_customer_evidence", [])
    return {
        "schema_version": CONTROL_PLANE_SCHEMA_VERSION,
        "service": "AURUM enterprise control plane",
        "generated_at_utc": _utc_now(),
        "decision_id": evidence.get("decision", {}).get("decision_id"),
        "status": "RESEARCH_READY_INTEGRATION_IN_PROGRESS",
        "production_blocked": preflight.get("production_gate") != "PASS",
        "research_promotion": "RESEARCH_ONLY",
        "execution_enabled": False,
        "repository_control_coverage": _coverage(repository_passed, len(repository_areas)),
        "deployment_preflight_coverage": _coverage(int(deployment_summary.get("passed_checks", 0)), int(deployment_summary.get("total_checks", 0))),
        "customer_acceptance_coverage": _coverage(0, len(customer_controls)),
        "repository_areas": repository_areas,
        "deployment": {"research_gate": preflight.get("research_gate"), "production_gate": preflight.get("production_gate"), "blockers": preflight.get("blockers", [])},
        "customer_acceptance": {"status": "EVIDENCE_REQUIRED", "required_evidence": customer_controls},
        "next_actions": [
            "Bind the production profile to immutable image digests and signed provenance.",
            "Integrate customer SSO/RBAC, tenant isolation, immutable evidence storage, and access logging.",
            "Run approved live-data provider, outage, reconciliation, and freshness drills before optimizer use.",
            "Complete independent model validation and committee sign-off separately from optimization authorization.",
            "Approve customer SLO/RTO/RPO, backup/restore, incident, support, and change-management evidence.",
        ],
        "claim_boundary": "This control plane distinguishes repository evidence from deployment and customer acceptance. It is not a certification, investment approval, or production authorization.",
    }
