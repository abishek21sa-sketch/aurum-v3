"""Fail-closed deployment boundary checks for the AURUM research build."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re
from pathlib import Path
from typing import Any


PREFLIGHT_SCHEMA_VERSION = "1.0"
_SKIP_DIRS = {".git", ".hg", ".svn", ".venv", "__pycache__", ".pytest_cache", ".pytest_acceptance_tmp"}


@dataclass(frozen=True)
class PreflightCheck:
    check_id: str
    domain: str
    status: str
    severity: str
    summary: str
    details: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "domain": self.domain,
            "status": self.status,
            "severity": self.severity,
            "summary": self.summary,
            "details": dict(self.details),
        }


def _check(check_id: str, domain: str, status: str, severity: str, summary: str, **details: Any) -> PreflightCheck:
    return PreflightCheck(check_id, domain, status, severity, summary, details)


def _service_block(compose: str, service: str) -> str:
    lines = compose.splitlines()
    start = next((index for index, line in enumerate(lines) if line == f"  {service}:"), None)
    if start is None:
        return ""
    selected = [lines[start]]
    for line in lines[start + 1 :]:
        if line.startswith("  ") and not line.startswith("    ") and line.strip():
            break
        selected.append(line)
    return "\n".join(selected)


def _secret_filename_findings(root: Path) -> list[str]:
    findings: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in _SKIP_DIRS for part in relative.parts):
            continue
        if path.name.lower() in {".env", ".env.local", ".env.production", "id_rsa", "id_ed25519"} or path.suffix.lower() in {".pem", ".key", ".p12", ".pfx"}:
            findings.append(relative.as_posix())
    return sorted(findings)


def build_deployment_preflight(root: Path) -> dict[str, Any]:
    """Return repository-proven deployment controls without persisting state."""
    compose_path = root / "docker-compose.yml"
    compose = compose_path.read_text(encoding="utf-8") if compose_path.is_file() else ""
    dockerfiles = {
        "Dockerfile.api": (root / "Dockerfile.api"),
        "Dockerfile.dashboard": (root / "Dockerfile.dashboard"),
    }
    evidence: dict[str, Any] = {}
    try:
        from src.institutional.mars_cvar_product import build_reference_product_evidence

        evidence = build_reference_product_evidence(root)
    except Exception as exc:  # pragma: no cover - represented by the failed boundary check
        evidence = {"error": str(exc)}
    governance = evidence.get("governance", {})
    execution_safe = governance.get("execution_enabled") is False and governance.get("research_promotion") == "RESEARCH_ONLY"
    checks: list[PreflightCheck] = []

    checks.append(_check("boundary.research_execution_disabled", "governance", "PASS" if execution_safe else "FAIL", "INFO" if execution_safe else "CRITICAL", "Research build remains fail-closed for execution", execution_enabled=governance.get("execution_enabled"), research_promotion=governance.get("research_promotion")))
    secret_findings = _secret_filename_findings(root)
    checks.append(_check("security.repository_secret_hygiene", "security", "PASS" if not secret_findings else "FAIL", "INFO" if not secret_findings else "CRITICAL", "No private-key or environment-secret files are present", findings=secret_findings))

    workflow = root.parent / ".github" / "workflows" / "aurum-acceptance.yml"
    checks.append(_check("delivery.github_acceptance_workflow", "delivery", "PASS" if workflow.is_file() else "FAIL", "INFO" if workflow.is_file() else "HIGH", "Repository contains an automated acceptance workflow", present=workflow.is_file()))
    checks.append(_check("operations.runbook_present", "operations", "PASS" if (root / "docs/OPERATIONS_RUNBOOK.md").is_file() else "FAIL", "INFO" if (root / "docs/OPERATIONS_RUNBOOK.md").is_file() else "HIGH", "Operator runbook is present"))
    checks.append(_check("operations.recovery_plan_present", "operations", "PASS" if (root / "docs/DISASTER_RECOVERY.md").is_file() else "FAIL", "INFO" if (root / "docs/DISASTER_RECOVERY.md").is_file() else "HIGH", "Disaster-recovery contract is present"))
    checks.append(_check("deployment.production_profile_present", "deployment", "PASS" if (root / "configs/prod.yaml").is_file() else "FAIL", "INFO" if (root / "configs/prod.yaml").is_file() else "HIGH", "Production configuration profile exists"))

    images = re.findall(r"^\s*image:\s*(\S+)", compose, flags=re.MULTILINE)
    unpinned = [image for image in images if "@sha256:" not in image]
    checks.append(_check("deployment.image_provenance_pinned", "supply_chain", "PASS" if not unpinned else "FAIL", "INFO" if not unpinned else "HIGH", "Production container images are pinned by immutable digest", images=images, unpinned_images=unpinned))
    default_credential = bool(re.search(r"POSTGRES_PASSWORD\s*(?:=|:)\s*aurum\b", compose, flags=re.IGNORECASE))
    checks.append(_check("deployment.external_secret_injection", "security", "PASS" if not default_credential else "FAIL", "INFO" if not default_credential else "CRITICAL", "Database credentials are supplied by deployment secret management", default_credential_present=default_credential))

    missing_non_root = []
    for name, path in dockerfiles.items():
        content = path.read_text(encoding="utf-8") if path.is_file() else ""
        if not re.search(r"^\s*USER\s+\S+", content, flags=re.MULTILINE):
            missing_non_root.append(name)
    checks.append(_check("deployment.non_root_containers", "container_security", "PASS" if not missing_non_root else "FAIL", "INFO" if not missing_non_root else "HIGH", "Application containers declare a non-root runtime user", missing_user_declarations=missing_non_root))
    api_block = _service_block(compose, "api")
    api_healthcheck = "healthcheck:" in api_block
    checks.append(_check("deployment.api_healthcheck", "reliability", "PASS" if api_healthcheck else "FAIL", "INFO" if api_healthcheck else "HIGH", "API service has a deployment health check", configured=api_healthcheck))
    direct_ports = re.findall(r"^\s*-\s*[\"']?(\d+):(\d+)[\"']?\s*$", compose, flags=re.MULTILINE)
    checks.append(_check("deployment.ingress_boundary", "network_security", "PASS" if not direct_ports else "FAIL", "INFO" if not direct_ports else "HIGH", "Production services are exposed through approved ingress", direct_host_bindings=[f"{host}:{container}" for host, container in direct_ports]))
    checks.append(_check("paper_trading.execution_isolation", "execution_control", "PASS" if execution_safe else "FAIL", "INFO" if execution_safe else "CRITICAL", "Paper/research workflows cannot authorize live execution", execution_enabled=governance.get("execution_enabled")))

    failures = [check for check in checks if check.status == "FAIL"]
    blockers = [check.check_id for check in failures if check.severity in {"CRITICAL", "HIGH"}]
    return {
        "schema_version": PREFLIGHT_SCHEMA_VERSION,
        "service": "AURUM deployment boundary",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "overall_status": "PRODUCTION_BLOCKED" if blockers else "READY_FOR_HUMAN_REVIEW",
        "research_gate": "PASS" if execution_safe and not secret_findings else "FAIL",
        "production_gate": "PASS" if not blockers else "BLOCKED",
        "decision_id": evidence.get("decision", {}).get("decision_id"),
        "execution_enabled": governance.get("execution_enabled"),
        "research_promotion": governance.get("research_promotion"),
        "checks": [check.as_dict() for check in checks],
        "summary": {"total_checks": len(checks), "passed_checks": len(checks) - len(failures), "failed_checks": len(failures), "production_blockers": len(blockers)},
        "blockers": blockers,
        "required_actions": [
            "Pin every production image by immutable digest.",
            "Inject database and API secrets from an external secret manager.",
            "Run containers as a dedicated non-root identity.",
            "Expose services only through authenticated ingress with health checks.",
            "Complete organization-owned IAM, backup, incident, and change-approval controls.",
        ] if blockers else [],
        "boundary_note": "A passing research gate proves repository controls only; production deployment remains blocked until deployment-owned controls pass.",
    }
