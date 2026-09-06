from pathlib import Path

from scripts.product_adapter import compute
from src.institutional.research_operations import (
    HYPOTHESIS_ID,
    build_research_memory,
    build_research_operations,
    write_research_operations,
)


ROOT = Path(__file__).resolve().parents[1]


def test_research_operations_is_grounded_and_fail_closed():
    payload = build_research_operations(ROOT, compute())

    assert payload["service"] == "AURUM Research Operations"
    assert payload["mode"] == "DETERMINISTIC_GOVERNED_FIXTURE"
    assert payload["execution_enabled"] is False
    assert payload["research_promotion"] == "RESEARCH_ONLY"
    assert payload["hypotheses"][0]["hypothesis_id"] == HYPOTHESIS_ID
    assert payload["committee"]["judge_engaged_bear_objection"] is True
    assert payload["learning"]["paper_trading_enabled"] is False
    assert payload["digital_twin"]["evidence_class"] == "SIMULATED_REFERENCE_SCENARIO"


def test_research_validation_does_not_promote_equal_baseline():
    payload = build_research_operations(ROOT, compute())
    validation = payload["validation"]
    baseline_check = next(item for item in validation["checks"] if item["id"] == "baseline_uplift")

    assert baseline_check["status"] == "REVIEW"
    assert validation["promotion_safe"] is False
    assert payload["committee"]["decision"] == "RESEARCH_ONLY"


def test_research_memory_is_structured_and_downloadable(tmp_path):
    payload = write_research_operations(tmp_path, compute())
    memory = build_research_memory(tmp_path, compute())

    assert (tmp_path / "artifacts" / "research_operations" / "latest_research_operations.json").is_file()
    assert payload["artifact_integrity"]["content_sha256"]
    assert memory["count"] == 3
    assert all(item["structured_constraint"] for item in memory["memories"])
