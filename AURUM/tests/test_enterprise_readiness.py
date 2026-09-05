from pathlib import Path

from fastapi.testclient import TestClient

from src.api.main import app
from src.institutional.enterprise_readiness import (
    build_enterprise_readiness,
)
from src.institutional.mars_cvar_product import build_reference_product_evidence


ROOT = Path(__file__).resolve().parents[1]


def test_enterprise_readiness_contract_is_ready_for_human_review():
    evidence = build_reference_product_evidence(ROOT)
    payload = build_enterprise_readiness(ROOT, evidence)

    assert payload["overall_status"] == "READY_FOR_HUMAN_REVIEW"
    assert payload["release_gate"] == "PASS"
    assert payload["summary"]["failed_checks"] == 0
    assert payload["research_promotion"] == "RESEARCH_ONLY"
    assert payload["execution_enabled"] is False
    assert payload["audit_lineage"]["hash_algorithm"] == "SHA-256"
    assert payload["audit_lineage"]["root_hash"]
    assert len(payload["audit_lineage"]["nodes"]) == 4


def test_enterprise_role_policy_keeps_execution_out_of_research_roles():
    payload = build_enterprise_readiness(ROOT)
    roles = payload["role_policy"]["roles"]
    assert "enable_execution" in roles["researcher"]["deny"]
    assert "enable_execution" in roles["risk_officer"]["deny"]
    assert "deployment_owned_authentication" in payload["role_policy"]["required_controls"]


def test_platform_control_endpoints_expose_machine_contracts():
    client = TestClient(app)
    readiness = client.get("/v1/platform/readiness")
    observability = client.get("/v1/platform/observability")
    policy = client.get("/v1/platform/role-policy")
    lineage = client.get("/v1/platform/audit/lineage")

    assert readiness.status_code == 200
    assert readiness.json()["release_gate"] == "PASS"
    assert observability.status_code == 200
    assert observability.json()["no_secrets"] is True
    assert policy.status_code == 200
    assert policy.json()["schema_version"] == "1.0"
    assert lineage.status_code == 200
    assert lineage.json()["root_hash"]
