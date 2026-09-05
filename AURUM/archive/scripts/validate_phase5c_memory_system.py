from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Dict, List, Tuple


MEMORY_DB = Path("results/memory/institutional_memory.jsonl")
MEMORY_INDEX = Path("results/memory/institutional_memory_index.json")
MEMORY_REPORT_JSON = Path("results/memory/institutional_memory_report.json")
MEMORY_REPORT_TXT = Path("results/memory/institutional_memory_report.txt")


MODULES = [
    "src.market_memory.memory_store",
    "src.market_memory.memory_retriever",
    "src.market_memory.memory_similarity_engine",
    "src.market_memory.regime_memory_engine",
    "src.market_memory.crisis_memory_engine",
    "src.market_memory.allocation_memory_engine",
    "src.market_memory.committee_memory_engine",
    "src.market_memory.outcome_memory_engine",
    "src.market_memory.memory_report_generator",
]


def check_imports() -> List[Tuple[str, bool, str]]:
    results = []

    for module in MODULES:
        try:
            importlib.import_module(module)
            results.append((module, True, "import ok"))
        except Exception as exc:
            results.append((module, False, str(exc)))

    return results


def load_memory_records() -> List[Dict]:
    if not MEMORY_DB.exists():
        return []

    records = []

    with MEMORY_DB.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))

    return records


def validate_memory_schema(records: List[Dict]) -> Tuple[bool, str]:
    required = {
        "memory_id",
        "timestamp",
        "memory_type",
        "title",
        "description",
        "regime",
        "market_features",
        "decision",
        "allocation",
        "risk_metrics",
        "committee_vote",
        "outcome",
        "metadata",
    }

    if not records:
        return False, "no memory records found"

    for record in records:
        missing = required - set(record.keys())
        if missing:
            return False, f"record missing fields: {missing}"

    return True, "schema valid"


def validate_required_memory_types(records: List[Dict]) -> Tuple[bool, str]:
    required_types = {
        "REGIME",
        "CRISIS",
        "ALLOCATION",
        "COMMITTEE",
        "OUTCOME",
    }

    found = {r.get("memory_type") for r in records}
    missing = required_types - found

    if missing:
        return False, f"missing memory types: {sorted(missing)}"

    return True, f"required memory types present: {sorted(required_types)}"


def validate_retriever() -> Tuple[bool, str]:
    try:
        from src.market_memory.memory_retriever import InstitutionalMemoryRetriever

        retriever = InstitutionalMemoryRetriever()
        summary = retriever.summary()

        if summary["total_records"] < 5:
            return False, "retriever found fewer than 5 records"

        if not retriever.get_by_regime("defensive"):
            return False, "retriever could not find defensive regime"

        return True, "retriever working"

    except Exception as exc:
        return False, str(exc)


def validate_similarity() -> Tuple[bool, str]:
    try:
        from src.market_memory.memory_similarity_engine import MarketMemorySimilarityEngine

        engine = MarketMemorySimilarityEngine()

        report = engine.current_market_resemblance_report(
            current_state={
                "volatility": 0.0836,
                "stress_score": 0.40,
                "breadth": 0.40,
                "projected_var95": 0.1300,
                "projected_drawdown": -0.0641,
            }
        )

        if report["memory_count_checked"] < 5:
            return False, "similarity checked fewer than 5 memories"

        if not report["best_match"]:
            return False, "no best match returned"

        return True, "similarity engine working"

    except Exception as exc:
        return False, str(exc)


def validate_report() -> Tuple[bool, str]:
    try:
        from src.market_memory.memory_report_generator import (
            InstitutionalMemoryReportGenerator,
        )

        generator = InstitutionalMemoryReportGenerator()
        report = generator.generate_report()

        if not MEMORY_REPORT_JSON.exists():
            return False, "memory report json missing"

        if not MEMORY_REPORT_TXT.exists():
            return False, "memory report txt missing"

        if report["memory_summary"]["total_records"] < 5:
            return False, "report has fewer than 5 records"

        return True, "memory report generated"

    except Exception as exc:
        return False, str(exc)


def validate_artifacts(records: List[Dict]) -> List[Tuple[str, bool, str]]:
    checks = []

    checks.append(
        (
            "institutional memory database",
            MEMORY_DB.exists(),
            str(MEMORY_DB),
        )
    )

    checks.append(
        (
            "institutional memory index",
            MEMORY_INDEX.exists(),
            str(MEMORY_INDEX),
        )
    )

    checks.append(
        (
            "institutional memory report json",
            MEMORY_REPORT_JSON.exists(),
            str(MEMORY_REPORT_JSON),
        )
    )

    checks.append(
        (
            "institutional memory report txt",
            MEMORY_REPORT_TXT.exists(),
            str(MEMORY_REPORT_TXT),
        )
    )

    schema_ok, schema_msg = validate_memory_schema(records)
    checks.append(("memory schema", schema_ok, schema_msg))

    type_ok, type_msg = validate_required_memory_types(records)
    checks.append(("required memory types", type_ok, type_msg))

    return checks


def print_result(name: str, passed: bool, detail: str = "") -> None:
    status = "[PASS]" if passed else "[FAIL]"
    print(f"{status} {name}")
    if detail:
        print(f"       {detail}")


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 5C MARKET MEMORY SYSTEM VALIDATION")
    print("=" * 80)

    overall_pass = True

    print()
    print("MODULE IMPORT CHECKS")
    print("-" * 80)

    for module, passed, detail in check_imports():
        print_result(module, passed, detail)
        overall_pass = overall_pass and passed

    records = load_memory_records()

    print()
    print("ARTIFACT AND SCHEMA CHECKS")
    print("-" * 80)

    for name, passed, detail in validate_artifacts(records):
        print_result(name, passed, detail)
        overall_pass = overall_pass and passed

    print()
    print("FUNCTIONAL CHECKS")
    print("-" * 80)

    for name, validator in [
        ("memory retriever", validate_retriever),
        ("memory similarity engine", validate_similarity),
        ("memory report generator", validate_report),
    ]:
        passed, detail = validator()
        print_result(name, passed, detail)
        overall_pass = overall_pass and passed

    print()
    print("=" * 80)

    if overall_pass:
        print("[PASS] PHASE 5C MARKET MEMORY SYSTEM COMPLETE")
        print("AURUM now has institutional memory.")
    else:
        print("[FAIL] PHASE 5C MARKET MEMORY SYSTEM NEEDS ATTENTION")

    print("=" * 80)

    if not overall_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()