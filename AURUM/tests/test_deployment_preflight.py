from pathlib import Path

from fastapi.testclient import TestClient

from src.api.main import app
from src.institutional.deployment_preflight import build_deployment_preflight


ROOT = Path(__file__).resolve().parents[1]


def test_deployment_preflight_preserves_research_boundary_and_reports_production_gaps():
    payload = build_deployment_preflight(ROOT)

    assert payload["research_gate"] == "PASS"
    assert payload["production_gate"] == "BLOCKED"
    assert payload["execution_enabled"] is False
    assert "deployment.image_provenance_pinned" in payload["blockers"]
    assert "deployment.external_secret_injection" not in payload["blockers"]
    assert "deployment.non_root_containers" not in payload["blockers"]
    assert "deployment.api_healthcheck" not in payload["blockers"]
    assert "deployment.ingress_boundary" not in payload["blockers"]
    assert "deployment.container_hardening" not in payload["blockers"]
    weak_default = next(check for check in payload["checks"] if check["check_id"] == "security.weak_default_credentials")
    assert weak_default["status"] == "PASS"


def test_deployment_preflight_endpoint_is_machine_readable():
    response = TestClient(app).get("/v1/platform/deployment-preflight")

    assert response.status_code == 200
    payload = response.json()
    assert payload["service"] == "AURUM deployment boundary"
    assert payload["research_promotion"] == "RESEARCH_ONLY"
