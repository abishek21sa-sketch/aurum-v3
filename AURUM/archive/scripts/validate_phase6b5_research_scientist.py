from pathlib import Path
import importlib
import json

from src.research_scientist.research_scientist_agent import ResearchScientistAgent


def check(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        print(f"[PASS] {label}")
        if detail:
            print(f"       {detail}")
    else:
        print(f"[FAIL] {label}")
        if detail:
            print(f"       {detail}")
        raise SystemExit(1)


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 6B.5 AI RESEARCH SCIENTIST VALIDATION")
    print("=" * 80)

    importlib.import_module("src.research_scientist.research_review_engine")
    importlib.import_module("src.research_scientist.hypothesis_generator")
    importlib.import_module("src.research_scientist.research_scientist_agent")
    check(True, "research scientist modules import")

    report = ResearchScientistAgent().run()

    required_paths = [
        Path("results/research_scientist/alpha_review.json"),
        Path("results/research_scientist/research_hypotheses.json"),
        Path("results/research_scientist/research_scientist_agent.json"),
        Path("results/research_scientist/research_scientist_report.txt"),
    ]

    for path in required_paths:
        check(path.exists(), f"{path} exists")

    review = json.loads(
        Path("results/research_scientist/alpha_review.json").read_text(encoding="utf-8")
    )

    hypotheses = json.loads(
        Path("results/research_scientist/research_hypotheses.json").read_text(encoding="utf-8")
    )

    check(review["alpha_count"] >= 6, "research scientist reviewed alpha scorecard", str(review["alpha_count"]))
    check(review["top_alpha"] is not None, "top alpha identified")
    check(len(review["observations"]) >= 1, "research observations generated")

    check(hypotheses["hypothesis_count"] >= 3, "at least 3 hypotheses generated", str(hypotheses["hypothesis_count"]))

    for hyp in hypotheses["hypotheses"]:
        check(hyp.get("hypothesis_id"), "hypothesis has id")
        check(hyp.get("hypothesis"), f"{hyp['hypothesis_id']} has hypothesis")
        check(hyp.get("test_design"), f"{hyp['hypothesis_id']} has test design")
        check(hyp.get("priority") in {"low", "medium", "high"}, f"{hyp['hypothesis_id']} has valid priority")

    check("scientist_conclusion" in report, "scientist conclusion generated")

    print("=" * 80)
    print("[PASS] PHASE 6B.5 AI RESEARCH SCIENTIST COMPLETE")
    print("AURUM now reviews alpha results and generates new research hypotheses.")
    print("=" * 80)


if __name__ == "__main__":
    main()