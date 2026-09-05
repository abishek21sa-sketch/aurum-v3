from __future__ import annotations

import importlib
import json
import traceback
from pathlib import Path
from typing import Any, Dict, List, Tuple

from src.research.ai_research_desk_orchestrator import AIResearchDeskOrchestrator
from src.research.ai_daily_research_packet_generator import (
    AIDailyResearchPacketGenerator,
)


REQUIRED_MODULES = [
    "src.research.llm_client",
    "src.research.ai_agent_base",
    "src.research.ai_macro_agent",
    "src.research.ai_market_structure_agent",
    "src.research.ai_regime_agent",
    "src.research.ai_risk_agent",
    "src.research.ai_portfolio_agent",
    "src.research.ai_digital_twin_agent",
    "src.research.ai_research_committee",
    "src.research.ai_research_desk_orchestrator",
    "src.research.ai_daily_research_packet_generator",
]

REQUIRED_ARTIFACTS = [
    Path("results/research/ai_research_committee.json"),
    Path("results/research/ai_research_desk.json"),
    Path("results/research/ai_daily_research_packet.json"),
    Path("results/research/ai_daily_research_packet.txt"),
]


def pass_line(message: str) -> None:
    print(f"[PASS] {message}")


def fail_line(message: str) -> None:
    print(f"[FAIL] {message}")


def validate_imports() -> Tuple[bool, List[str]]:
    errors: List[str] = []

    for module in REQUIRED_MODULES:
        try:
            importlib.import_module(module)
            pass_line(f"import {module}")
        except Exception as exc:
            fail_line(f"import {module}")
            errors.append(f"{module}: {exc}")

    return len(errors) == 0, errors


def validate_ai_desk() -> Tuple[bool, List[str], Dict[str, Any]]:
    errors: List[str] = []

    try:
        desk = AIResearchDeskOrchestrator()
        result = desk.run()

        required_fields = [
            "platform",
            "artifact",
            "generated_at",
            "ai_research_status",
            "analyst_outputs",
            "committee_analysis",
            "executive_summary",
            "recommended_posture",
            "highest_priority_risk",
            "research_confidence",
        ]

        for field in required_fields:
            if field not in result:
                errors.append(f"missing AI desk field: {field}")

        committee = result.get("committee_analysis", {})
        required_committee = [
            "committee_decision",
            "execution_permission",
            "base_case",
            "bull_case",
            "bear_case",
            "key_disagreements",
            "binding_constraint",
            "risk_controls",
            "final_recommendation",
            "committee_confidence",
            "decision_rationale",
        ]

        for field in required_committee:
            if field not in committee:
                errors.append(f"missing committee field: {field}")

        analysts = result.get("analyst_outputs", {})
        expected = [
            "macro",
            "market_structure",
            "regime",
            "risk",
            "portfolio",
            "digital_twin",
        ]

        for name in expected:
            payload = analysts.get(name, {})

            if payload.get("status") != "success":
                errors.append(f"AI analyst failed or missing: {name}")

            ai = payload.get("output", {}).get("ai_analysis", {})
            for field in [
                "thesis",
                "evidence",
                "contradictions",
                "risks",
                "recommendation",
                "confidence",
                "decision_rationale",
            ]:
                if field not in ai:
                    errors.append(f"{name} missing AI field: {field}")

        if errors:
            fail_line("AI research desk schema")
            return False, errors, result

        pass_line("AI research desk run")
        pass_line("AI research desk schema")
        return True, errors, result

    except Exception as exc:
        fail_line("AI research desk run")
        errors.append(str(exc))
        traceback.print_exc()
        return False, errors, {}


def validate_ai_packet() -> Tuple[bool, List[str], Dict[str, Any]]:
    errors: List[str] = []

    try:
        generator = AIDailyResearchPacketGenerator()
        packet = generator.generate()

        required_fields = [
            "platform",
            "artifact",
            "generated_at",
            "executive_summary",
            "committee_decision",
            "execution_permission",
            "base_case",
            "bull_case",
            "bear_case",
            "key_disagreements",
            "binding_constraint",
            "risk_controls",
            "final_recommendation",
            "committee_confidence",
            "decision_rationale",
        ]

        for field in required_fields:
            if field not in packet:
                errors.append(f"missing AI packet field: {field}")

        if not str(packet.get("final_recommendation", "")).strip():
            errors.append("AI packet final recommendation is empty")

        if errors:
            fail_line("AI daily research packet schema")
            return False, errors, packet

        pass_line("AI daily research packet generation")
        pass_line("AI daily research packet schema")
        return True, errors, packet

    except Exception as exc:
        fail_line("AI daily research packet generation")
        errors.append(str(exc))
        traceback.print_exc()
        return False, errors, {}


def validate_artifacts() -> Tuple[bool, List[str]]:
    errors: List[str] = []

    for path in REQUIRED_ARTIFACTS:
        if not path.exists():
            fail_line(f"artifact exists: {path}")
            errors.append(f"missing artifact: {path}")
            continue

        if path.stat().st_size <= 0:
            fail_line(f"artifact non-empty: {path}")
            errors.append(f"empty artifact: {path}")
            continue

        pass_line(f"artifact exists: {path}")
        pass_line(f"artifact non-empty: {path}")

    return len(errors) == 0, errors


def validate_json_schema(path: Path, fields: List[str]) -> Tuple[bool, List[str]]:
    errors: List[str] = []

    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        for field in fields:
            if field not in data:
                errors.append(f"{path} missing field: {field}")

        if errors:
            fail_line(f"json schema: {path}")
            return False, errors

        pass_line(f"json schema: {path}")
        return True, errors

    except Exception as exc:
        fail_line(f"json readable: {path}")
        errors.append(f"{path}: {exc}")
        return False, errors


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 5A TRUE AI LAYER VALIDATION")
    print("=" * 80)

    all_errors: List[str] = []

    print()
    print("MODULE IMPORT CHECKS")
    print("-" * 80)
    _, errors = validate_imports()
    all_errors.extend(errors)

    print()
    print("AI DESK CHECKS")
    print("-" * 80)
    _, errors, _ = validate_ai_desk()
    all_errors.extend(errors)

    print()
    print("AI PACKET CHECKS")
    print("-" * 80)
    _, errors, _ = validate_ai_packet()
    all_errors.extend(errors)

    print()
    print("ARTIFACT CHECKS")
    print("-" * 80)
    _, errors = validate_artifacts()
    all_errors.extend(errors)

    print()
    print("JSON SCHEMA CHECKS")
    print("-" * 80)

    _, errors = validate_json_schema(
        Path("results/research/ai_research_desk.json"),
        [
            "platform",
            "artifact",
            "generated_at",
            "ai_research_status",
            "analyst_outputs",
            "committee_analysis",
            "executive_summary",
        ],
    )
    all_errors.extend(errors)

    _, errors = validate_json_schema(
        Path("results/research/ai_daily_research_packet.json"),
        [
            "platform",
            "artifact",
            "generated_at",
            "committee_decision",
            "execution_permission",
            "final_recommendation",
            "committee_confidence",
        ],
    )
    all_errors.extend(errors)

    print()
    print("=" * 80)

    if all_errors:
        print("PHASE 5A AI LAYER STATUS: FAILED")
        print("=" * 80)
        print()
        for error in all_errors:
            print(f"- {error}")
        raise SystemExit(1)

    print("PHASE 5A AI LAYER STATUS: COMPLETE")
    print("=" * 80)
    print()
    print("Validated Artifacts:")
    print("  results/research/ai_research_committee.json")
    print("  results/research/ai_research_desk.json")
    print("  results/research/ai_daily_research_packet.json")
    print("  results/research/ai_daily_research_packet.txt")


if __name__ == "__main__":
    main()