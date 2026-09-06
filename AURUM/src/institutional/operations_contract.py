"""Operational readiness contract for an enterprise AURUM deployment."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


OPERATIONS_SCHEMA_VERSION = "1.0"


CUSTOMER_EVIDENCE_DEFINITIONS = (
    {
        "evidence_id": "availability_slo_alerting",
        "label": "Approved availability SLO and alert routing",
        "owner": "customer_operations",
        "required_fields": ("slo_target", "alert_route"),
    },
    {
        "evidence_id": "recovery_objectives_drill",
        "label": "Approved RTO/RPO and successful backup/restore drill",
        "owner": "customer_operations",
        "required_fields": ("rto_minutes", "rpo_minutes", "backup_restore_drill_id"),
    },
    {
        "evidence_id": "retention_legal_hold",
        "label": "Retention, legal hold, and deletion-approval record",
        "owner": "customer_compliance",
        "required_fields": ("retention_days", "legal_hold_record", "deletion_approval_record"),
    },
    {
        "evidence_id": "support_escalation",
        "label": "Named support owner and incident escalation path",
        "owner": "customer_support",
        "required_fields": ("support_owner", "incident_escalation_path"),
    },
    {
        "evidence_id": "change_rollback",
        "label": "Change-approval and rollback record",
        "owner": "customer_change_control",
        "required_fields": ("change_approval_record", "rollback_plan_reference"),
    },
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_config(root: Path) -> dict[str, Any]:
    path = root / "config" / "operations.json"
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _configured(value: Any) -> bool:
    return value not in (None, "", "CUSTOMER_CONFIGURATION_REQUIRED", "CUSTOMER_APPROVAL_REQUIRED")


def build_operations_status(root: Path) -> dict[str, Any]:
    config = _load_config(root)
    static_controls = [
        {"control_id": "operations.runbook", "status": "PASS" if (root / "docs/OPERATIONS_RUNBOOK.md").is_file() else "FAIL", "evidence": "docs/OPERATIONS_RUNBOOK.md"},
        {"control_id": "operations.disaster_recovery", "status": "PASS" if (root / "docs/DISASTER_RECOVERY.md").is_file() else "FAIL", "evidence": "docs/DISASTER_RECOVERY.md"},
        {"control_id": "operations.observability_endpoint", "status": "PASS" if (root / "src/api/main.py").is_file() else "FAIL", "evidence": "/v1/platform/observability"},
        {"control_id": "operations.production_profile", "status": "PASS" if (root / "docker-compose.production.yml").is_file() else "FAIL", "evidence": "docker-compose.production.yml"},
    ]
    customer_fields = {
        "slo_target": config.get("slo_target"),
        "rto_minutes": config.get("rto_minutes"),
        "rpo_minutes": config.get("rpo_minutes"),
        "retention_days": config.get("retention_days"),
        "support_owner": config.get("support_owner"),
        "alert_route": config.get("alert_route"),
        "backup_restore_drill_id": config.get("backup_restore_drill_id"),
        "change_approval_record": config.get("change_approval_record"),
        "legal_hold_record": config.get("legal_hold_record"),
        "deletion_approval_record": config.get("deletion_approval_record"),
        "incident_escalation_path": config.get("incident_escalation_path"),
        "rollback_plan_reference": config.get("rollback_plan_reference"),
    }
    evidence_register = []
    for definition in CUSTOMER_EVIDENCE_DEFINITIONS:
        missing_fields = [field for field in definition["required_fields"] if not _configured(customer_fields.get(field))]
        evidence_register.append(
            {
                "evidence_id": definition["evidence_id"],
                "label": definition["label"],
                "owner": definition["owner"],
                "required_fields": list(definition["required_fields"]),
                "missing_fields": missing_fields,
                "status": "EVIDENCED" if not missing_fields else "REQUIRED",
            }
        )
    configured = all(item["status"] == "EVIDENCED" for item in evidence_register)
    failures = [item for item in static_controls if item["status"] == "FAIL"]
    return {
        "schema_version": OPERATIONS_SCHEMA_VERSION,
        "service": "AURUM enterprise operations contract",
        "generated_at_utc": _utc_now(),
        "status": "PASS" if configured and not failures else "CUSTOMER_CONFIGURATION_REQUIRED" if not failures else "INCOMPLETE",
        "static_repository_controls": static_controls,
        "customer_operating_configuration": customer_fields,
        "customer_configuration_complete": configured,
        "customer_evidence_register": evidence_register,
        "required_customer_evidence": [
            "Approved availability SLO and alert routing",
            "Approved RTO/RPO and successful backup/restore drill",
            "Retention, legal hold, and deletion-approval record",
            "Named support owner and incident escalation path",
            "Change-approval and rollback record",
        ],
        "execution_enabled": False,
        "research_promotion": "RESEARCH_ONLY",
        "claim_boundary": "Repository contracts describe operational ownership; they do not prove uptime, recovery performance, or customer approval.",
    }
