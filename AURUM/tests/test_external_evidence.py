import json
from pathlib import Path

from fastapi.testclient import TestClient

from src.api.main import app
from src.institutional.external_evidence import (
    CUSTOMER_CONTROL_DEFINITIONS,
    IMAGE_KEYS,
    build_customer_evidence_status,
    build_production_image_provenance,
)


ROOT = Path(__file__).resolve().parents[1]


def _customer_manifest() -> dict:
    return {
        "schema_version": "1.0",
        "controls": {
            control_id: {
                "owner": owner,
                "evidence_uri": f"https://customer.example/evidence/{control_id}",
                "evidence_sha256": "a" * 64,
                "approved_by": "customer-security-committee",
                "approved_at_utc": "2026-09-05T12:00:00Z",
                "verification_record": f"change-record-{index:02d}",
            }
            for index, (control_id, _label, owner) in enumerate(CUSTOMER_CONTROL_DEFINITIONS, start=1)
        },
    }


def _provenance_manifest() -> dict:
    return {
        "schema_version": "1.0",
        "registry": "registry.example.com/aurum",
        "attestation_uri": "https://customer.example/attestations/aurum-release",
        "attestation_sha256": "b" * 64,
        "signed_by": "release-security",
        "verification_record": "release-verification-2026-09-05",
        "deployment_binding": "docker-compose.production.yml",
        "images": {key: f"registry.example.com/aurum/{key.lower()}@sha256:{'c' * 64}" for key in IMAGE_KEYS},
    }


def test_missing_external_manifests_remain_fail_closed(tmp_path):
    customer = build_customer_evidence_status(tmp_path)
    provenance = build_production_image_provenance(tmp_path)

    assert customer["status"] == "REQUIRED"
    assert customer["coverage"] == {"passed": 0, "total": 5, "percent": 0.0}
    assert provenance["status"] == "REQUIRED"
    assert provenance["metadata_checks"]["all_images_pinned_by_sha256"] is False


def test_valid_external_manifests_close_only_their_shape_contracts(tmp_path, monkeypatch):
    customer_path = tmp_path / "customer-evidence.json"
    provenance_path = tmp_path / "image-provenance.json"
    customer_path.write_text(json.dumps(_customer_manifest()), encoding="utf-8")
    provenance_path.write_text(json.dumps(_provenance_manifest()), encoding="utf-8")
    monkeypatch.setenv("AURUM_CUSTOMER_EVIDENCE_FILE", str(customer_path))
    monkeypatch.setenv("AURUM_PRODUCTION_PROVENANCE_FILE", str(provenance_path))

    customer = build_customer_evidence_status(ROOT)
    provenance = build_production_image_provenance(ROOT)

    assert customer["status"] == "EVIDENCED"
    assert customer["coverage"] == {"passed": 5, "total": 5, "percent": 100.0}
    assert provenance["status"] == "EVIDENCED"
    assert provenance["metadata_checks"]["all_images_pinned_by_sha256"] is True


def test_invalid_approval_and_digest_do_not_close_controls(tmp_path, monkeypatch):
    customer = _customer_manifest()
    customer["controls"]["identity.sso"]["approved_by"] = ""
    provenance = _provenance_manifest()
    provenance["images"]["AURUM_API_IMAGE"] = "registry.example.com/aurum/api:latest"
    customer_path = tmp_path / "customer-evidence.json"
    provenance_path = tmp_path / "image-provenance.json"
    customer_path.write_text(json.dumps(customer), encoding="utf-8")
    provenance_path.write_text(json.dumps(provenance), encoding="utf-8")
    monkeypatch.setenv("AURUM_CUSTOMER_EVIDENCE_FILE", str(customer_path))
    monkeypatch.setenv("AURUM_PRODUCTION_PROVENANCE_FILE", str(provenance_path))

    assert build_customer_evidence_status(ROOT)["controls"][0]["status"] == "REQUIRED"
    assert build_production_image_provenance(ROOT)["status"] == "REQUIRED"


def test_manifest_schema_version_is_required(tmp_path, monkeypatch):
    customer = _customer_manifest()
    customer["schema_version"] = "0.9"
    customer_path = tmp_path / "customer-evidence.json"
    customer_path.write_text(json.dumps(customer), encoding="utf-8")
    monkeypatch.setenv("AURUM_CUSTOMER_EVIDENCE_FILE", str(customer_path))

    result = build_customer_evidence_status(ROOT)

    assert result["manifest_schema_valid"] is False
    assert result["status"] == "REQUIRED"


def test_external_evidence_api_endpoints_are_read_only_and_fail_closed():
    client = TestClient(app)
    customer = client.get("/v1/platform/customer-evidence")
    provenance = client.get("/v1/platform/image-provenance")

    assert customer.status_code == 200
    assert customer.json()["status"] in {"REQUIRED", "EVIDENCED"}
    assert provenance.status_code == 200
    assert provenance.json()["status"] in {"REQUIRED", "EVIDENCED"}
