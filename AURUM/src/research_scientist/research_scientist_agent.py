from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
from typing import Dict
import json

from src.research_scientist.research_review_engine import ResearchReviewEngine
from src.research_scientist.hypothesis_generator import HypothesisGenerator


RESULTS_DIR = Path("results/research_scientist")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ResearchScientistAgent:
    def run(self) -> Dict:
        review = ResearchReviewEngine().review()
        hypotheses = HypothesisGenerator().generate(review)

        report = {
            "timestamp": utc_now(),
            "agent": "aurum_ai_research_scientist",
            "mission": (
                "Review alpha research performance and generate new institutional "
                "research hypotheses."
            ),
            "alpha_review": review,
            "research_hypotheses": hypotheses,
            "scientist_conclusion": self._conclusion(review, hypotheses),
        }

        (RESULTS_DIR / "alpha_review.json").write_text(
            json.dumps(review, indent=2),
            encoding="utf-8",
        )

        (RESULTS_DIR / "research_hypotheses.json").write_text(
            json.dumps(hypotheses, indent=2),
            encoding="utf-8",
        )

        (RESULTS_DIR / "research_scientist_agent.json").write_text(
            json.dumps(report, indent=2),
            encoding="utf-8",
        )

        (RESULTS_DIR / "research_scientist_report.txt").write_text(
            self._text_report(report),
            encoding="utf-8",
        )

        return report

    def _conclusion(self, review: Dict, hypotheses: Dict) -> str:
        top_alpha = review.get("top_alpha")
        hypothesis_count = hypotheses.get("hypothesis_count", 0)

        if top_alpha:
            return (
                f"The strongest current research candidate is {top_alpha['alpha_id']}. "
                f"The scientist generated {hypothesis_count} new hypotheses for the next research loop."
            )

        return (
            f"No valid alpha leader was found. The scientist generated {hypothesis_count} "
            "hypotheses to rebuild the research pipeline."
        )

    def _text_report(self, report: Dict) -> str:
        review = report["alpha_review"]
        hypotheses = report["research_hypotheses"]

        lines = []
        lines.append("=" * 80)
        lines.append("AURUM AI RESEARCH SCIENTIST REPORT")
        lines.append("=" * 80)
        lines.append(f"Alpha Count: {review['alpha_count']}")
        lines.append("")

        lines.append("OBSERVATIONS")
        lines.append("-" * 80)
        for obs in review["observations"]:
            lines.append(f"- {obs}")

        lines.append("")
        lines.append("RESEARCH HYPOTHESES")
        lines.append("-" * 80)
        for hyp in hypotheses["hypotheses"]:
            lines.append(f"{hyp['hypothesis_id']} | priority={hyp['priority']}")
            lines.append(f"Theme: {hyp['theme']}")
            lines.append(f"Hypothesis: {hyp['hypothesis']}")
            lines.append(f"Test: {hyp['test_design']}")
            lines.append("")

        lines.append("CONCLUSION")
        lines.append("-" * 80)
        lines.append(report["scientist_conclusion"])
        lines.append("=" * 80)

        return "\n".join(lines)


def main() -> None:
    report = ResearchScientistAgent().run()

    print("=" * 80)
    print("AURUM PHASE 6B.5 AI RESEARCH SCIENTIST")
    print("=" * 80)
    print(f"Alpha Count:       {report['alpha_review']['alpha_count']}")
    print(f"Hypotheses:        {report['research_hypotheses']['hypothesis_count']}")
    print(f"Conclusion:        {report['scientist_conclusion']}")
    print("=" * 80)


if __name__ == "__main__":
    main()