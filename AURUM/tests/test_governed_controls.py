from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from src.institutional.live_data_contract import validate_snapshot_rows
from src.institutional.live_data_ingestion import build_ingestion_receipt, normalize_provider_rows
from src.institutional.model_validation import build_model_validation
from src.institutional.enterprise_platform import build_enterprise_platform_status
from src.institutional.ai_evaluation import build_ai_evaluation
from src.institutional.control_plane import build_control_plane
from src.institutional.operations_contract import build_operations_status


ROOT = Path(__file__).resolve().parents[1]


def _rows(timestamp: str):
    return [
        {"ticker": "SPY", "timestamp": timestamp, "open": "100", "high": "101", "low": "99", "close": "100.5"},
        {"ticker": "TLT", "timestamp": timestamp, "open": "100", "high": "101", "low": "99", "close": "100.5"},
    ]


def test_live_data_quality_rejects_missing_or_stale_inputs():
    now = datetime(2026, 9, 5, tzinfo=timezone.utc)
    result = validate_snapshot_rows(_rows("2026-09-05T10:00:00Z"), ["SPY", "TLT", "GLD"], now=now, freshness_minutes=30)

    assert result["status"] == "FAIL"
    assert result["missing_tickers"] == ["GLD"]
    assert result["checks"]["freshness_within_sla"] is False


def test_live_data_quality_accepts_complete_fresh_snapshot():
    now = datetime.now(timezone.utc)
    timestamp = (now - timedelta(minutes=2)).isoformat()
    result = validate_snapshot_rows(_rows(timestamp), ["SPY", "TLT"], now=now, freshness_minutes=30)

    assert result["status"] == "PASS"
    assert result["checks"]["numeric_prices_valid"] is True


def test_provider_rows_are_normalized_and_receipted_without_credentials():
    rows = [{"symbol": "SPY", "time": "2026-09-05T12:00:00Z", "o": 100, "h": 101, "l": 99, "c": 100.5}]

    normalized = normalize_provider_rows(rows)
    receipt = build_ingestion_receipt(normalized, provider="test-provider", request_id="req-123")

    assert normalized[0]["ticker"] == "SPY"
    assert normalized[0]["close"] == 100.5
    assert receipt["row_count"] == 1
    assert receipt["tickers"] == ["SPY"]
    assert len(receipt["payload_sha256"]) == 64
    assert receipt["credentials_in_receipt"] is False
    assert receipt["network_fetch_performed"] is False


def test_reference_data_status_exposes_a_replayable_receipt():
    from src.institutional.live_data_contract import build_live_data_status

    result = build_live_data_status(ROOT)

    assert result["status"] == "REFERENCE_ONLY"
    assert result["optimizer_feed_enabled"] is False
    assert result["snapshot_receipt"]["request_id"] == "reference-fixture"
    assert result["provider_contract"]["request_id_required_when_live"] is True


def test_model_validation_is_review_ready_but_not_independent_approval():
    result = build_model_validation(ROOT)

    assert result["status"] == "READY_FOR_INDEPENDENT_REVIEW"
    assert result["summary"]["failed_checks"] == 0
    assert result["independent_review_required"] is True
    assert result["promotion_state"] == "RESEARCH_ONLY"


def test_enterprise_platform_status_names_customer_owned_controls():
    result = build_enterprise_platform_status(ROOT)
    controls = {item["control_id"]: item for item in result["controls"]}

    assert result["execution_enabled"] is False
    assert controls["identity.sso"]["status"] == "DEPLOYMENT_REQUIRED"
    assert controls["tenancy.isolation"]["status"] == "RESEARCH_SINGLE_TENANT"
    assert controls["deployment.production_profile"]["status"] == "PASS"


def test_ai_evaluation_proves_grounding_and_safety_contract():
    result = build_ai_evaluation(ROOT)

    assert result["status"] == "PASS"
    assert result["summary"]["failed_checks"] == 0
    assert result["live_provider_evaluation"] == "SKIPPED_NO_EXPLICIT_LIVE_MODEL"
    assert result["execution_enabled"] is False


def test_control_plane_keeps_readiness_denominators_separate():
    result = build_control_plane(ROOT)

    assert result["status"] == "RESEARCH_READY_INTEGRATION_IN_PROGRESS"
    assert result["repository_control_coverage"] == {"passed": 6, "total": 6, "percent": 100.0}
    assert result["deployment_preflight_coverage"]["total"] == 14
    assert result["customer_acceptance_coverage"]["passed"] == 0
    assert result["production_blocked"] is True


def test_operations_contract_is_explicitly_customer_configured():
    result = build_operations_status(ROOT)

    assert result["status"] == "CUSTOMER_CONFIGURATION_REQUIRED"
    assert result["customer_configuration_complete"] is False
    assert result["execution_enabled"] is False
    assert len(result["required_customer_evidence"]) == 5


def test_governed_payloads_validate_against_public_schemas():
    payloads = {
        "aurum_live_data.schema.json": __import__("src.institutional.live_data_contract", fromlist=["build_live_data_status"]).build_live_data_status(ROOT),
        "aurum_control_plane.schema.json": build_control_plane(ROOT),
        "aurum_operations.schema.json": build_operations_status(ROOT),
    }
    for filename, payload in payloads.items():
        schema = json.loads((ROOT / "schemas" / filename).read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        errors = list(Draft202012Validator(schema).iter_errors(payload))
        assert errors == [], f"{filename}: {errors}"
