from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Dict, List, Tuple


TRACE_JSON = Path("results/decision_intelligence/decision_trace.json")
REASONING_JSON = Path("results/decision_intelligence/decision_reasoning.json")
EXPLANATION_JSON = Path("results/decision_intelligence/decision_explanation.json")
EXPLANATION_TXT = Path("results/decision_intelligence/decision_explanation.txt")


MODULES = [
    "src.research.decision_trace_engine",
    "src.research.decision_reasoning_engine",
    "src.research.explanation_generator",
]


def print_result(name: str, passed: bool, detail: str = "") -> None:
    status = "[PASS]" if passed else "[FAIL]"
    print(f"{status} {name}")
    if detail:
        print(f"       {detail}")


def check_imports() -> List[Tuple[str, bool, str]]:
    results = []

    for module in MODULES:
        try:
            importlib.import_module(module)
            results.append((module, True, "import ok"))
        except Exception as exc:
            results.append((module, False, str(exc)))

    return results


def load_json(path: Path) -> Dict:
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_trace() -> Tuple[bool, str]:
    try:
        from src.research.decision_trace_engine import DecisionTraceEngine

        engine = DecisionTraceEngine()
        trace = engine.build_trace()

        stages = trace.get("decision_lineage", [])
        stage_names = [s.get("stage") for s in stages]

        required = [
            "market_data",
            "features",
            "regime",
            "risk",
            "optimization",
            "committee",
            "memory",
            "final_decision",
        ]

        missing = [s for s in required if s not in stage_names]

        if missing:
            return False, f"missing stages: {missing}"

        if not TRACE_JSON.exists():
            return False, "decision_trace.json missing"

        return True, f"trace valid with {len(stages)} stages"

    except Exception as exc:
        return False, str(exc)


def validate_reasoning() -> Tuple[bool, str]:
    try:
        from src.research.decision_reasoning_engine import DecisionReasoningEngine

        engine = DecisionReasoningEngine()
        reasoning = engine.generate_reasoning()

        answers = reasoning.get("answers", {})

        required_answers = [
            "why_are_we_defensive",
            "why_did_allocation_change",
            "why_is_risk_increasing",
            "why_execution_blocked",
            "have_we_seen_this_before",
        ]

        missing = [a for a in required_answers if a not in answers]

        if missing:
            return False, f"missing answers: {missing}"

        if not REASONING_JSON.exists():
            return False, "decision_reasoning.json missing"

        return True, "reasoning valid"

    except Exception as exc:
        return False, str(exc)


def validate_explanation() -> Tuple[bool, str]:
    try:
        from src.research.explanation_generator import DecisionExplanationGenerator

        generator = DecisionExplanationGenerator()
        explanation = generator.generate_explanation()

        if not EXPLANATION_JSON.exists():
            return False, "decision_explanation.json missing"

        if not EXPLANATION_TXT.exists():
            return False, "decision_explanation.txt missing"

        text = EXPLANATION_TXT.read_text(encoding="utf-8")

        required_phrases = [
            "AURUM DECISION EXPLANATION",
            "WHY ARE WE DEFENSIVE?",
            "WHY DID ALLOCATION CHANGE?",
            "WHY IS RISK INCREASING?",
            "HAVE WE SEEN THIS BEFORE?",
        ]

        missing = [p for p in required_phrases if p not in text]

        if missing:
            return False, f"missing explanation sections: {missing}"

        if explanation.get("final_decision", {}).get("decision") != "defensive_no_execution":
            return False, "unexpected final decision"

        return True, "explanation valid"

    except Exception as exc:
        return False, str(exc)


def validate_artifacts() -> List[Tuple[str, bool, str]]:
    return [
        ("decision trace json", TRACE_JSON.exists(), str(TRACE_JSON)),
        ("decision reasoning json", REASONING_JSON.exists(), str(REASONING_JSON)),
        ("decision explanation json", EXPLANATION_JSON.exists(), str(EXPLANATION_JSON)),
        ("decision explanation txt", EXPLANATION_TXT.exists(), str(EXPLANATION_TXT)),
    ]


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 5D DECISION INTELLIGENCE VALIDATION")
    print("=" * 80)

    overall_pass = True

    print()
    print("MODULE IMPORT CHECKS")
    print("-" * 80)

    for module, passed, detail in check_imports():
        print_result(module, passed, detail)
        overall_pass = overall_pass and passed

    print()
    print("FUNCTIONAL CHECKS")
    print("-" * 80)

    for name, validator in [
        ("decision trace engine", validate_trace),
        ("decision reasoning engine", validate_reasoning),
        ("explanation generator", validate_explanation),
    ]:
        passed, detail = validator()
        print_result(name, passed, detail)
        overall_pass = overall_pass and passed

    print()
    print("ARTIFACT CHECKS")
    print("-" * 80)

    for name, passed, detail in validate_artifacts():
        print_result(name, passed, detail)
        overall_pass = overall_pass and passed

    print()
    print("=" * 80)

    if overall_pass:
        print("[PASS] PHASE 5D DECISION INTELLIGENCE COMPLETE")
        print("AURUM decisions are now traceable, explainable, and memory-augmented.")
    else:
        print("[FAIL] PHASE 5D DECISION INTELLIGENCE NEEDS ATTENTION")

    print("=" * 80)

    if not overall_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()