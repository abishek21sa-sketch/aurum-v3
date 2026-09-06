import json
from pathlib import Path

from jsonschema import Draft202012Validator

from src.institutional.synthetic_ml import (
    DEFAULT_ROW_COUNT,
    build_synthetic_dataset_status,
    generate_synthetic_dataset,
    run_synthetic_ml_validation,
    validate_synthetic_dataset,
    write_synthetic_ml_validation,
)


ROOT = Path(__file__).resolve().parents[1]


def test_synthetic_dataset_is_exactly_10000_rows_and_covers_all_cases(tmp_path):
    manifest = generate_synthetic_dataset(tmp_path)
    dataset = tmp_path / "artifacts" / "synthetic" / "synthetic_ml_dataset.csv"
    result = validate_synthetic_dataset(dataset)

    assert manifest["actual_rows"] == DEFAULT_ROW_COUNT
    assert manifest["data_class"] == "SIMULATED_SYNTHETIC_DATA"
    assert result["status"] == "PASS"
    assert result["row_count"] == DEFAULT_ROW_COUNT
    assert set(result["case_counts"]) >= {
        "clean", "sparse_history", "regime_boundary", "liquidity_shock", "outlier_return",
        "missing_feature", "stale_timestamp", "duplicate_observation", "nonpositive_price",
        "label_noise", "schema_drift",
    }


def test_synthetic_ml_validation_is_chronological_and_research_only(tmp_path):
    generate_synthetic_dataset(tmp_path)
    result = write_synthetic_ml_validation(tmp_path)

    assert result["split"]["method"] == "chronological"
    assert result["split"]["train_rows"] > 0
    assert result["split"]["test_rows"] > 0
    assert result["checks"]["no_external_fetch"] is True
    assert result["checks"]["optimizer_feed_enabled"] is False
    assert result["promotion_state"] == "RESEARCH_ONLY"
    assert result["regression"]["mse"] >= 0
    assert 0 <= result["classification"]["accuracy"] <= 1
    assert result["classification"]["majority_baseline_accuracy"] >= 0
    assert set(result["classification"]["unseen_test_labels"]).issubset(result["classification"]["test_labels"])
    assert set(result["classification"]["unseen_test_labels"]).isdisjoint(result["classification"]["labels"])


def test_synthetic_outputs_validate_against_public_schemas(tmp_path):
    manifest = generate_synthetic_dataset(tmp_path)
    validation = write_synthetic_ml_validation(tmp_path)
    manifest_schema = json.loads((ROOT / "schemas" / "aurum_synthetic_dataset_manifest.schema.json").read_text(encoding="utf-8"))
    validation_schema = json.loads((ROOT / "schemas" / "aurum_synthetic_ml_validation.schema.json").read_text(encoding="utf-8"))

    assert list(Draft202012Validator(manifest_schema).iter_errors(manifest)) == []
    assert list(Draft202012Validator(validation_schema).iter_errors(validation)) == []


def test_synthetic_status_exposes_non_market_boundary(tmp_path):
    generate_synthetic_dataset(tmp_path)
    status = build_synthetic_dataset_status(tmp_path)

    assert status["status"] == "PASS"
    assert status["data_class"] == "SIMULATED_SYNTHETIC_DATA"
    assert status["optimizer_feed_enabled"] is False
