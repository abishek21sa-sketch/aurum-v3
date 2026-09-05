from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List
import json


ALPHA_SCORECARD_PATH = Path("results/alpha/alpha_scorecard.json")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ResearchReviewEngine:
    def load_alpha_scorecard(self) -> Dict:
        if not ALPHA_SCORECARD_PATH.exists():
            return {"scorecard": []}

        return json.loads(ALPHA_SCORECARD_PATH.read_text(encoding="utf-8"))

    def review(self) -> Dict:
        scorecard = self.load_alpha_scorecard().get("scorecard", [])

        ranked = sorted(
            scorecard,
            key=lambda row: row.get("alpha_score", 0),
            reverse=True,
        )

        top_alpha = ranked[0] if ranked else None
        weak_alphas = [
            row for row in ranked
            if row.get("alpha_score", 0) < 68
        ]

        strong_alphas = [
            row for row in ranked
            if row.get("alpha_score", 0) >= 72
        ]

        observations: List[str] = []

        if top_alpha:
            observations.append(
                f"Top alpha is {top_alpha['alpha_id']} with score {top_alpha['alpha_score']}."
            )

        if strong_alphas:
            observations.append(
                f"{len(strong_alphas)} alpha candidates show institutional promise."
            )

        if weak_alphas:
            observations.append(
                f"{len(weak_alphas)} alpha candidates require repair, filtering, or retirement review."
            )

        if not observations:
            observations.append("No alpha scorecard available for review.")

        return {
            "timestamp": utc_now(),
            "review_engine": "research_review_engine",
            "alpha_count": len(ranked),
            "top_alpha": top_alpha,
            "strong_alphas": strong_alphas,
            "weak_alphas": weak_alphas,
            "observations": observations,
        }