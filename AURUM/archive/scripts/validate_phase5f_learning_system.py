from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import List, Tuple


DECISION_SCORECARD_CSV = Path("results/learning/decision_scorecard.csv")
DECISION_EVALUATION_JSON = Path("results/learning/decision_evaluation_latest.json")
COMMITTEE_PERFORMANCE_JSON = Path("results/learning/committee_performance.json")
LEARNING_REPORT_TXT = Path("results/learning/learning_report.txt")
LEARNING_REPORT_JSON = Path("results/learning/learning_report.json")


MODULES = [
    "src.learning.decision_evaluator",
    "src.learning.committee_scorecard",
    "src.learning.learning_engine",
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


def validate_decision_evaluator() -> Tuple[bool, str]:
    try:
        from src.learning.decision_evaluator import DecisionEvaluator

        evaluator = DecisionEvaluator()
        result = evaluator.evaluate_decision(
            decision_id="validation_decision_5f",
            decision_type="portfolio_posture",
            recommendation="defensive_no_execution",
            predicted_regime="defensive",
            realized_regime="defensive",
            pre_decision_risk=0.1300,
            post_decision_risk=0.1000,
            avoided_drawdown=0.0210,
            allocation_sharpe=0.8696,
            committee_agreement=0.80,
        )

        if result["total_decision_score"] <= 0:
            return False, "decision score not positive"

        if result["grade"] not in {"EXCELLENT", "GOOD", "WATCH", "POOR"}:
            return False, "invalid grade"

        return True, f"decision evaluator working | score={result['total_decision_score']} grade={result['grade']}"

    except Exception as exc:
        return False, str(exc)


def validate_committee_scorecard() -> Tuple[bool, str]:
    try:
        from src.learning.committee_scorecard import CommitteeScorecard

        engine = CommitteeScorecard()

        scorecard = engine.score_committee(
            realized_outcome="defensive",
            agent_votes={
                "macro_agent": "neutral",
                "risk_agent": "defensive",
                "portfolio_agent": "defensive",
                "regime_agent": "normal",
                "digital_twin_agent": "defensive",
            },
            agent_confidences={
                "macro_agent": 0.70,
                "risk_agent": 0.88,
                "portfolio_agent": 0.82,
                "regime_agent": 0.76,
                "digital_twin_agent": 0.80,
            },
            risk_alignment={
                "macro_agent": 0.55,
                "risk_agent": 0.92,
                "portfolio_agent": 0.84,
                "regime_agent": 0.65,
                "digital_twin_agent": 0.86,
            },
        )

        if scorecard["committee_accuracy"] <= 0:
            return False, "committee accuracy not positive"

        if not scorecard["best_agent"]:
            return False, "best agent missing"

        return True, f"committee scorecard working | best_agent={scorecard['best_agent']}"

    except Exception as exc:
        return False, str(exc)


def validate_learning_engine() -> Tuple[bool, str]:
    try:
        from src.learning.learning_engine import LearningEngine

        engine = LearningEngine()
        report = engine.generate_learning_report()

        if report["system_learning"]["learning_status"] != "ACTIVE":
            return False, "learning status not active"

        if not report["system_learning"]["lessons"]:
            return False, "no lessons generated"

        return True, "learning engine generated active lessons"

    except Exception as exc:
        return False, str(exc)


def validate_artifacts() -> List[Tuple[str, bool, str]]:
    return [
        ("decision scorecard csv", DECISION_SCORECARD_CSV.exists(), str(DECISION_SCORECARD_CSV)),
        ("decision evaluation json", DECISION_EVALUATION_JSON.exists(), str(DECISION_EVALUATION_JSON)),
        ("committee performance json", COMMITTEE_PERFORMANCE_JSON.exists(), str(COMMITTEE_PERFORMANCE_JSON)),
        ("learning report txt", LEARNING_REPORT_TXT.exists(), str(LEARNING_REPORT_TXT)),
        ("learning report json", LEARNING_REPORT_JSON.exists(), str(LEARNING_REPORT_JSON)),
    ]


def validate_report_content() -> Tuple[bool, str]:
    if not LEARNING_REPORT_TXT.exists():
        return False, "learning_report.txt missing"

    text = LEARNING_REPORT_TXT.read_text(encoding="utf-8")

    required = [
        "AURUM PHASE 5F LEARNING REPORT",
        "DECISION LEARNING",
        "COMMITTEE LEARNING",
        "SYSTEM LEARNING",
        "Next Action",
    ]

    missing = [item for item in required if item not in text]

    if missing:
        return False, f"missing report sections: {missing}"

    return True, "learning report content valid"


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 5F LEARNING & EVALUATION VALIDATION")
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
        ("decision evaluator", validate_decision_evaluator),
        ("committee scorecard", validate_committee_scorecard),
        ("learning engine", validate_learning_engine),
        ("learning report content", validate_report_content),
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
        print("[PASS] PHASE 5F LEARNING & EVALUATION SYSTEM COMPLETE")
        print("AURUM now evaluates decisions, scores committees, and learns from outcomes.")
    else:
        print("[FAIL] PHASE 5F LEARNING & EVALUATION SYSTEM NEEDS ATTENTION")

    print("=" * 80)

    if not overall_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()