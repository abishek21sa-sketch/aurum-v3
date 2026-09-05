from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List
import json


RESULTS_DIR = Path("results/alpha_ranking")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: str | Path, default: Any = None) -> Any:
    if default is None:
        default = {}

    path = Path(path)

    try:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


class InstitutionalAlphaScorecard:
    def load_inputs(self) -> Dict:
        return {
            "alpha_scorecard": load_json("results/alpha/alpha_scorecard.json", {"scorecard": []}),
            "top_alpha_rankings": load_json("results/alpha/top_alpha_rankings.json", {}),
            "factor_rotation": load_json("results/factors/factor_rotation_signal.json", {}),
            "autonomous_research": load_json("results/autonomous_research/autonomous_research_loop.json", {}),
            "cio_directive": load_json("results/cio/cio_portfolio_directive.json", {}),
            "cio_thesis": load_json("results/cio/cio_market_thesis.json", {}),
        }

    def cio_relevance_bonus(self, alpha: Dict, inputs: Dict) -> float:
        cio = inputs.get("cio_thesis", {})
        top_alpha = cio.get("top_alpha", "")

        if alpha["alpha_id"] == top_alpha:
            return 8.0

        preferred_factors = set(cio.get("preferred_factors", []))
        category = alpha.get("category", "")

        if category in preferred_factors:
            return 4.0

        if category == "quality" and "quality" in preferred_factors:
            return 4.0

        if category == "momentum" and "momentum" in preferred_factors:
            return 4.0

        return 0.0

    def research_status_bonus(self, alpha: Dict, inputs: Dict) -> float:
        loop = inputs.get("autonomous_research", {})
        queue = loop.get("next_research_queue", {}).get("queue", [])

        if not queue:
            return 0.0

        if alpha["alpha_id"] == "ALPHA_MOMENTUM_001":
            return 5.0

        return 0.0

    def institutional_score(self, alpha: Dict, inputs: Dict) -> float:
        base_score = float(alpha.get("alpha_score", 0))
        cio_bonus = self.cio_relevance_bonus(alpha, inputs)
        research_bonus = self.research_status_bonus(alpha, inputs)

        risk_penalty = 0.0

        if alpha.get("max_drawdown", 0) > 0.15:
            risk_penalty += 3.0

        if alpha.get("cvar", 0) > 0.12:
            risk_penalty += 2.0

        return round(base_score + cio_bonus + research_bonus - risk_penalty, 2)

    def build_scorecard(self) -> Dict:
        inputs = self.load_inputs()
        alpha_rows = inputs["alpha_scorecard"].get("scorecard", [])

        ranked = []

        for alpha in alpha_rows:
            institutional_score = self.institutional_score(alpha, inputs)

            ranked.append(
                {
                    **alpha,
                    "institutional_score": institutional_score,
                    "cio_relevance_bonus": self.cio_relevance_bonus(alpha, inputs),
                    "research_status_bonus": self.research_status_bonus(alpha, inputs),
                    "ranking_basis": [
                        "alpha_score",
                        "sharpe",
                        "cvar",
                        "max_drawdown",
                        "consistency",
                        "cio_relevance",
                        "research_promotion_status",
                    ],
                }
            )

        ranked = sorted(ranked, key=lambda row: row["institutional_score"], reverse=True)

        result = {
            "timestamp": utc_now(),
            "scorecard": "institutional_alpha_scorecard",
            "alpha_count": len(ranked),
            "ranked_alphas": ranked,
            "best_alpha": ranked[0] if ranked else None,
        }

        (RESULTS_DIR / "institutional_alpha_scorecard.json").write_text(
            json.dumps(result, indent=2),
            encoding="utf-8",
        )

        return result


def main() -> None:
    result = InstitutionalAlphaScorecard().build_scorecard()
    best = result["best_alpha"]

    print("=" * 80)
    print("AURUM PHASE 6B.9 INSTITUTIONAL ALPHA SCORECARD")
    print("=" * 80)
    print(f"Alpha Count: {result['alpha_count']}")
    if best:
        print(f"Best Alpha:  {best['alpha_id']} | {best['name']}")
        print(f"Score:       {best['institutional_score']}")
    print("=" * 80)


if __name__ == "__main__":
    main()