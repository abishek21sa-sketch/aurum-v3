import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from src.institutional.public_data import build_public_data_status, build_public_market_validation


ROOT = Path(__file__).resolve().parents[1]


def _manifest(artifact: str, payload: bytes) -> dict:
    return {
        "schema_version": "1.0",
        "service": "AURUM public data evidence intake",
        "generated_at_utc": "2026-09-06T00:00:00Z",
        "status": "PASS",
        "data_class": "PUBLIC_AUTHORITATIVE_DATA",
        "external_fetch_performed": True,
        "optimizer_feed_enabled": False,
        "promotion_state": "RESEARCH_ONLY",
        "sources": [{
            "source_id": "fdic_institutions",
            "authority": "Federal Deposit Insurance Corporation",
            "source_type": "PUBLIC_BANK_REGULATORY_DATA",
            "source_url": "https://banks.data.fdic.gov/api/institutions",
            "artifact": artifact,
            "retrieved_at_utc": "2026-09-06T00:00:00Z",
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "record_count": 1,
            "status": "PASS",
        }],
        "errors": [],
        "claim_boundary": "Public snapshots support research and feature validation; they do not establish causal forecasts, customer approval, or realized investment performance.",
    }


def test_public_snapshot_integrity_is_read_only_and_fail_closed(tmp_path):
    data_dir = tmp_path / "artifacts" / "public_data"
    data_dir.mkdir(parents=True)
    artifact = data_dir / "fdic_institutions.json"
    payload = b'{"data":[{"NAME":"Example Bank"}]}\n'
    artifact.write_bytes(payload)
    (data_dir / "public_data_manifest.json").write_text(json.dumps(_manifest("artifacts/public_data/fdic_institutions.json", payload)), encoding="utf-8")

    status = build_public_data_status(tmp_path)

    assert status["status"] == "PASS"
    assert status["data_class"] == "PUBLIC_AUTHORITATIVE_DATA"
    assert status["external_fetch_performed"] is True
    assert status["optimizer_feed_enabled"] is False
    assert status["passed_sources"] == 1


def test_public_snapshot_hash_mismatch_fails_closed(tmp_path):
    data_dir = tmp_path / "artifacts" / "public_data"
    data_dir.mkdir(parents=True)
    artifact = data_dir / "fdic_institutions.json"
    payload = b'{"data":[{"NAME":"Example Bank"}]}\n'
    artifact.write_bytes(payload + b"tampered")
    (data_dir / "public_data_manifest.json").write_text(json.dumps(_manifest("artifacts/public_data/fdic_institutions.json", payload)), encoding="utf-8")

    status = build_public_data_status(tmp_path)

    assert status["status"] == "PARTIAL"
    assert status["passed_sources"] == 0
    assert status["artifact_integrity"][0]["sha256_matches"] is False


def test_public_manifest_schema_is_valid():
    schema = json.loads((ROOT / "schemas" / "aurum_public_data_manifest.schema.json").read_text(encoding="utf-8"))
    example = _manifest("artifacts/public_data/fdic_institutions.json", b"example")
    assert list(Draft202012Validator(schema).iter_errors(example)) == []


def test_public_market_math_validation_is_chronological(tmp_path):
    data_dir = tmp_path / "artifacts" / "public_data"
    data_dir.mkdir(parents=True)
    (data_dir / "market_prices.csv").write_text(
        "ticker,timestamp,open,high,low,close,volume,source\n"
        "SPY,2026-01-01T00:00:00Z,100,101,99,100,10,public\n"
        "SPY,2026-01-02T00:00:00Z,101,102,100,101,10,public\n"
        "SPY,2026-01-03T00:00:00Z,102,103,101,102,10,public\n"
        "SPY,2026-01-04T00:00:00Z,103,104,102,101,10,public\n",
        encoding="utf-8",
    )

    result = build_public_market_validation(tmp_path)

    assert result["status"] == "PASS"
    assert result["row_count"] == 4
    assert result["duplicate_rows"] == 0
    assert result["chronological_split"]["no_lookahead"] is True
    assert result["per_ticker"][0]["max_drawdown"] < 0
