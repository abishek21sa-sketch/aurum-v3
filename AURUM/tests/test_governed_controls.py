from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.institutional.live_data_contract import validate_snapshot_rows
from src.institutional.model_validation import build_model_validation
from src.institutional.enterprise_platform import build_enterprise_platform_status
from src.institutional.ai_evaluation import build_ai_evaluation


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
