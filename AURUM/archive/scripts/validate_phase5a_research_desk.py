from __future__ import annotations

import importlib
import json
import traceback
from pathlib import Path
from typing import Any, Dict, List, Tuple

from src.research.daily_research_packet_generator import DailyResearchPacketGenerator
from src.research.research_desk_orchestrator import ResearchDeskOrchestrator


REQUIRED_MODULES = [
    "src.research.base_research_agent",
    "src.research.macro_agent",
    "src.research.market_structure_agent",
    "src.research.regime_agent",
    "src.research.risk_agent",
    "src.research.portfolio_agent",
    "src.research.digital_twin_agent",
    "src.research.research_desk_orchestrator",
    "src.research.daily_research_packet_generator",
]

REQUIRED_ARTIFACTS = [
    Path("results/research/research_desk_orchestration.json"),
    Path("results/research/daily_research_packet.json"),
    Path("results/research/daily_research_packet.txt"),
]


def pass_line(message: str) -> None:
    print(f"[PASS] {message}")


def fail_line(message: str) -> None:
    print(f"[FAIL] {message}")


def validate_imports() -> Tuple[bool, List[str]]:
    errors: List[str] = []

    for module_name in REQUIRED_MODULES:
        try:
            importlib.import_module(module_name)
            pass_line(f"import {module_name}")
        except Exception as exc:
            fail_line(f"import {module_name}")
            errors.append(f"{module_name}: {exc}")

    return len(errors) == 0, errors


def validate_orchestrator() -> Tuple[bool, List[str], Dict[str, Any]]:
    errors: List[str] = []

    try:
        orchestrator = ResearchDeskOrchestrator()
        result = orchestrator.run()

        if not isinstance(result, dict):
            errors.append("orchestrator result is not a dictionary")
            return False, errors, {}

        required_top_fields = [
            "platform",
            "artifact",
            "generated_at",
            "research_desk_status",
            "agents",
            "synthesis",
        ]

        for field in required_top_fields:
            if field not in result:
                errors.append(f"missing orchestrator field: {field}")

        agents = result.get("agents", {})
        expected_agents = [
            "macro",
            "market_structure",
            "regime",
            "risk",
            "portfolio",
            "digital_twin",
        ]

        for agent_name in expected_agents:
            payload = agents.get(agent_name)

            if not isinstance(payload, dict):
                errors.append(f"missing agent payload: {agent_name}")
                continue

            if payload.get("status") != "success":
                errors.append(f"agent failed: {agent_name}")

            output = payload.get("output", {})

            for field in [
                "agent_name",
                "observations",
                "analysis",
                "recommendations",
                "explanation",
            ]:
                if field not in output:
                    errors.append(f"{agent_name} missing output field: {field}")

        synthesis = result.get("synthesis", {})

        required_synthesis_fields = [
            "overall_market_view",
            "investment_committee_view",
            "recommended_posture",
            "highest_priority_risk",
            "desk_risk_score",
            "research_desk_confidence",
            "key_scores",
            "agent_headlines",
        ]

        for field in required_synthesis_fields:
            if field not in synthesis:
                errors.append(f"missing synthesis field: {field}")

        if errors:
            fail_line("research desk orchestrator schema")
            return False, errors, result

        pass_line("research desk orchestrator run")
        pass_line("research desk orchestrator schema")
        return True, errors, result

    except Exception as exc:
        fail_line("research desk orchestrator run")
        errors.append(str(exc))
        traceback.print_exc()
        return False, errors, {}


def validate_packet() -> Tuple[bool, List[str], Dict[str, Any]]:
    errors: List[str] = []

    try:
        generator = DailyResearchPacketGenerator()
        packet = generator.generate()

        required_packet_fields = [
            "platform",
            "artifact",
            "generated_at",
            "executive_summary",
            "investment_committee_view",
            "recommended_posture",
            "highest_priority_risk",
            "research_desk_confidence",
            "key_scores",
            "agent_headlines",
            "specialist_analyst_views",
        ]

        for field in required_packet_fields:
            if field not in packet:
                errors.append(f"missing packet field: {field}")

        if not str(packet.get("investment_committee_view", "")).strip():
            errors.append("investment committee view is empty")

        if not str(packet.get("executive_summary", "")).strip():
            errors.append("executive summary is empty")

        if errors:
            fail_line("daily research packet schema")
            return False, errors, packet

        pass_line("daily research packet generation")
        pass_line("daily research packet schema")
        return True, errors, packet

    except Exception as exc:
        fail_line("daily research packet generation")
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


def validate_json_file(path: Path, required_fields: List[str]) -> Tuple[bool, List[str]]:
    errors: List[str] = []

    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        for field in required_fields:
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
    print("AURUM PHASE 5A AI RESEARCH DESK VALIDATION")
    print("=" * 80)

    all_errors: List[str] = []

    print()
    print("MODULE IMPORT CHECKS")
    print("-" * 80)
    ok, errors = validate_imports()
    all_errors.extend(errors)

    print()
    print("ORCHESTRATOR CHECKS")
    print("-" * 80)
    ok, errors, _ = validate_orchestrator()
    all_errors.extend(errors)

    print()
    print("DAILY PACKET CHECKS")
    print("-" * 80)
    ok, errors, _ = validate_packet()
    all_errors.extend(errors)

    print()
    print("ARTIFACT CHECKS")
    print("-" * 80)
    ok, errors = validate_artifacts()
    all_errors.extend(errors)

    print()
    print("JSON SCHEMA CHECKS")
    print("-" * 80)

    ok, errors = validate_json_file(
        Path("results/research/research_desk_orchestration.json"),
        [
            "platform",
            "artifact",
            "generated_at",
            "research_desk_status",
            "agents",
            "synthesis",
        ],
    )
    all_errors.extend(errors)

    ok, errors = validate_json_file(
        Path("results/research/daily_research_packet.json"),
        [
            "platform",
            "artifact",
            "generated_at",
            "executive_summary",
            "investment_committee_view",
            "recommended_posture",
            "highest_priority_risk",
            "specialist_analyst_views",
        ],
    )
    all_errors.extend(errors)

    print()
    print("=" * 80)

    if all_errors:
        print("PHASE 5A STATUS: FAILED")
        print("=" * 80)
        print()
        print("ERRORS")
        print("-" * 80)

        for error in all_errors:
            print(f"- {error}")

        raise SystemExit(1)

    print("PHASE 5A STATUS: COMPLETE")
    print("=" * 80)
    print()
    print("Validated Artifacts:")
    print("  results/research/research_desk_orchestration.json")
    print("  results/research/daily_research_packet.json")
    print("  results/research/daily_research_packet.txt")


if __name__ == "__main__":
    main()