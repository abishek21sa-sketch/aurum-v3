"""Operational readiness contract for an enterprise AURUM deployment."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


OPERATIONS_SCHEMA_VERSION = "1.0"


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
    }
    configured = all(value not in (None, "", "CUSTOMER_CONFIGURATION_REQUIRED", "CUSTOMER_APPROVAL_REQUIRED") for value in customer_fields.values())
    failures = [item for item in static_controls if item["status"] == "FAIL"]
    return {
        "schema_version": OPERATIONS_SCHEMA_VERSION,
        "service": "AURUM enterprise operations contract",
        "generated_at_utc": _utc_now(),
        "status": "PASS" if configured and not failures else "CUSTOMER_CONFIGURATION_REQUIRED" if not failures else "INCOMPLETE",
        "static_repository_controls": static_controls,
        "customer_operating_configuration": customer_fields,
        "customer_configuration_complete": configured,
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
