"""Secure intake contracts for deployment and customer-owned evidence.

The repository can validate evidence shape, hashes, control identifiers, and
approval metadata. It cannot independently attest that an external authority
actually approved a record, so missing manifests remain fail-closed.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any


EVIDENCE_SCHEMA_VERSION = "1.0"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$", re.IGNORECASE)
CUSTOMER_CONTROL_DEFINITIONS = (
    ("identity.sso", "SSO/OIDC or SAML integration and break-glass procedure", "customer_platform"),
    ("identity.rbac_enforcement", "RBAC and segregation-of-duties enforcement evidence", "customer_platform"),
    ("tenancy.isolation", "Tenant-isolation evidence for shared deployments", "aurum_product"),
    ("evidence.immutable_storage", "Immutable retention, access logs, legal hold, backup, and restore evidence", "customer_platform"),
    ("operations.slo_and_support", "Approved SLO/RTO/RPO, incident response, support, and change records", "aurum_operations"),
)
IMAGE_KEYS = ("AURUM_REDIS_IMAGE", "AURUM_TIMESCALE_IMAGE", "AURUM_API_IMAGE", "AURUM_DASHBOARD_IMAGE")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _external_path(root: Path, environment_name: str, repository_name: str) -> tuple[Path, str]:
    configured = os.environ.get(environment_name)
    if configured:
        path = Path(configured).expanduser()
        return (path if path.is_absolute() else root / path, "ENVIRONMENT")
    return root / "config" / repository_name, "REPOSITORY"


def _sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError:
        return None
    return digest.hexdigest()


def _valid_record(item: Any) -> bool:
    if not isinstance(item, dict):
        return False
    required = ("evidence_uri", "evidence_sha256", "approved_by", "approved_at_utc", "verification_record")
    if any(item.get(key) in (None, "") for key in required):
        return False
    if not SHA256_RE.fullmatch(str(item.get("evidence_sha256"))):
        return False
    try:
        datetime.fromisoformat(str(item["approved_at_utc"]).replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def build_customer_evidence_status(root: Path) -> dict[str, Any]:
    """Validate the external customer-control evidence manifest, if supplied."""
    path, source = _external_path(root, "AURUM_CUSTOMER_EVIDENCE_FILE", "customer_evidence.json")
    payload = _load_json(path) if path.is_file() else None
    manifest_schema_valid = bool(payload and payload.get("schema_version") == EVIDENCE_SCHEMA_VERSION)
    controls_by_id = payload.get("controls", {}) if payload else {}
    if isinstance(controls_by_id, list):
        controls_by_id = {item.get("control_id"): item for item in controls_by_id if isinstance(item, dict)}
    controls = []
    for control_id, label, owner in CUSTOMER_CONTROL_DEFINITIONS:
        item = controls_by_id.get(control_id, {}) if isinstance(controls_by_id, dict) else {}
        valid = _valid_record(item)
        controls.append(
            {
                "control_id": control_id,
                "label": label,
                "owner": item.get("owner", owner) if isinstance(item, dict) else owner,
                "status": "EVIDENCED" if valid else "REQUIRED",
                "evidence_uri": item.get("evidence_uri") if valid else None,
                "evidence_sha256": item.get("evidence_sha256") if valid else None,
                "approved_by": item.get("approved_by") if valid else None,
                "approved_at_utc": item.get("approved_at_utc") if valid else None,
                "verification_record": item.get("verification_record") if valid else None,
            }
        )
    passed = sum(item["status"] == "EVIDENCED" for item in controls)
    return {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "service": "AURUM customer evidence intake",
        "generated_at_utc": _utc_now(),
        "source": source,
        "manifest_present": path.is_file(),
        "manifest_schema_valid": manifest_schema_valid,
        "manifest_path": str(path) if source == "ENVIRONMENT" else "config/customer_evidence.json",
        "status": "EVIDENCED" if manifest_schema_valid and passed == len(controls) else "REQUIRED",
        "coverage": {"passed": passed, "total": len(controls), "percent": round((passed / len(controls)) * 100, 1)},
        "controls": controls,
        "claim_boundary": "Shape and hash metadata are validated locally; customer authority and the underlying evidence remain external responsibilities.",
    }


def _valid_image_reference(value: Any) -> bool:
    return bool(isinstance(value, str) and "@sha256:" in value and SHA256_RE.fullmatch(value.rsplit("@sha256:", 1)[1]))


def build_production_image_provenance(root: Path) -> dict[str, Any]:
    """Validate an externally supplied immutable-image provenance manifest."""
    path, source = _external_path(root, "AURUM_PRODUCTION_PROVENANCE_FILE", "production_image_provenance.json")
    payload = _load_json(path) if path.is_file() else None
    images = payload.get("images", {}) if payload else {}
    manifest_schema_valid = bool(payload and payload.get("schema_version") == EVIDENCE_SCHEMA_VERSION)
    required_metadata = ("registry", "attestation_uri", "attestation_sha256", "signed_by", "verification_record", "deployment_binding")
    metadata_valid = bool(payload) and all(payload.get(key) not in (None, "") for key in required_metadata)
    metadata_valid = metadata_valid and bool(SHA256_RE.fullmatch(str(payload.get("attestation_sha256", ""))))
    images_valid = isinstance(images, dict) and all(_valid_image_reference(images.get(key)) for key in IMAGE_KEYS)
    valid = metadata_valid and images_valid and manifest_schema_valid
    return {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "service": "AURUM production image provenance intake",
        "generated_at_utc": _utc_now(),
        "source": source,
        "manifest_present": path.is_file(),
        "manifest_schema_valid": manifest_schema_valid,
        "manifest_path": str(path) if source == "ENVIRONMENT" else "config/production_image_provenance.json",
        "status": "EVIDENCED" if valid else "REQUIRED",
        "images": {key: images.get(key) for key in IMAGE_KEYS} if isinstance(images, dict) else {},
        "metadata_checks": {
            "required_attestation_metadata": metadata_valid,
            "all_images_pinned_by_sha256": images_valid,
            "deployment_binding_present": bool(payload and payload.get("deployment_binding")),
        },
        "claim_boundary": "Image references and attestation metadata are shape-validated locally; registry signatures and deployment binding require external verification.",
    }
