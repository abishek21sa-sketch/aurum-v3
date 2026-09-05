"""Enterprise integration status and ownership contract.

This is deliberately descriptive. It makes the remaining SSO, tenancy,
immutable-storage, and service-management work machine-readable without
pretending the repository can enforce organization-owned controls by itself.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def build_enterprise_platform_status(root: Path) -> dict[str, Any]:
    production_profile = root / "docker-compose.production.yml"
    controls = [
        {"control_id": "identity.sso", "status": "DEPLOYMENT_REQUIRED", "owner": "customer_platform", "evidence": "Gateway/identity integration is not supplied by the repository."},
        {"control_id": "identity.rbac_enforcement", "status": "DEPLOYMENT_REQUIRED", "owner": "customer_platform", "evidence": "Role policy is declared; enforcement belongs at the service and gateway boundary."},
        {"control_id": "tenancy.isolation", "status": "RESEARCH_SINGLE_TENANT", "owner": "aurum_product", "evidence": "Multi-tenant data partitioning and tenant-scoped keys are not enabled in this research build."},
        {"control_id": "evidence.immutable_storage", "status": "DEPLOYMENT_REQUIRED", "owner": "customer_platform", "evidence": "Exports are hash-linked; WORM/retention storage must be bound by deployment."},
        {"control_id": "operations.slo_and_support", "status": "CUSTOMER_APPROVAL_REQUIRED", "owner": "aurum_operations", "evidence": "RTO, RPO, SLO, on-call, and support commitments must be approved per customer."},
        {"control_id": "deployment.production_profile", "status": "PASS" if production_profile.is_file() else "FAIL", "owner": "aurum_product", "evidence": str(production_profile.name)},
    ]
    return {
        "schema_version": "1.0",
        "service": "AURUM enterprise platform contract",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "status": "INTEGRATION_READY_NOT_PRODUCTION" if all(item["status"] != "FAIL" for item in controls) else "INCOMPLETE",
        "identity_mode": "DEPLOYMENT_SSO_REQUIRED",
        "tenancy_mode": "SINGLE_TENANT_RESEARCH_BUILD",
        "audit_storage_mode": "HASH_LINKED_LOCAL_EXPORT",
        "execution_enabled": False,
        "research_promotion": "RESEARCH_ONLY",
        "controls": controls,
        "role_policy_source": "src/institutional/enterprise_readiness.py:build_role_policy",
        "required_customer_evidence": [
            "SSO/OIDC or SAML integration test and break-glass procedure",
            "RBAC and segregation-of-duties test evidence",
            "Tenant-isolation test evidence if multiple customers share a deployment",
            "Immutable retention, access logs, legal hold, backup, and restore evidence",
            "Approved SLO/RTO/RPO, incident response, support, and change-management records",
        ],
        "boundary_note": "This contract identifies integration ownership; it is not a substitute for customer IAM, compliance, or operational controls.",
    }
