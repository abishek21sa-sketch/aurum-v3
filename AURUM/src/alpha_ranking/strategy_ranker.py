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


class StrategyRanker:
    def build_rankings(self) -> Dict:
        alpha_scorecard = load_json(
            "results/alpha_ranking/institutional_alpha_scorecard.json",
            {"ranked_alphas": []},
        )

        factor_rotation = load_json("results/factors/factor_rotation_signal.json", {})
        cio_directive = load_json("results/cio/cio_portfolio_directive.json", {})
        research_loop = load_json("results/autonomous_research/research_learning_summary.json", {})

        entities: List[Dict] = []

        for alpha in alpha_scorecard.get("ranked_alphas", []):
            entities.append(
                {
                    "entity_type": "signal",
                    "entity_id": alpha["alpha_id"],
                    "name": alpha["name"],
                    "score": alpha["institutional_score"],
                    "basis": "alpha_scorecard",
                }
            )

        preferred_factors = factor_rotation.get("preferred_factors", [])
        for factor in preferred_factors:
            entities.append(
                {
                    "entity_type": "factor",
                    "entity_id": f"FACTOR_{factor.upper()}",
                    "name": factor,
                    "score": 72.0,
                    "basis": "factor_rotation_preference",
                }
            )

        entities.append(
            {
                "entity_type": "agent",
                "entity_id": "AI_CIO",
                "name": "AI Chief Investment Officer",
                "score": round(float(cio_directive.get("confidence", 0.0)) * 100, 2),
                "basis": "cio_confidence",
            }
        )

        entities.append(
            {
                "entity_type": "strategy",
                "entity_id": "AUTONOMOUS_RESEARCH_LOOP",
                "name": "Autonomous Research Loop",
                "score": float(research_loop.get("average_score", 0.0)),
                "basis": "research_loop_average_score",
            }
        )

        ranked = sorted(entities, key=lambda row: row["score"], reverse=True)

        result = {
            "timestamp": utc_now(),
            "ranking_system": "aurum_institutional_research_ranking",
            "entity_count": len(ranked),
            "ranked_entities": ranked,
            "top_entity": ranked[0] if ranked else None,
            "entity_type_counts": self.entity_counts(ranked),
        }

        (RESULTS_DIR / "institutional_research_rankings.json").write_text(
            json.dumps(result, indent=2),
            encoding="utf-8",
        )

        return result

    def entity_counts(self, entities: List[Dict]) -> Dict[str, int]:
        counts: Dict[str, int] = {}

        for entity in entities:
            entity_type = entity["entity_type"]
            counts[entity_type] = counts.get(entity_type, 0) + 1

        return counts


def main() -> None:
    result = StrategyRanker().build_rankings()
    top = result["top_entity"]

    print("=" * 80)
    print("AURUM PHASE 6B.9 INSTITUTIONAL RESEARCH RANKINGS")
    print("=" * 80)
    print(f"Entities:   {result['entity_count']}")
    if top:
        print(f"Top Entity: {top['entity_type']} | {top['entity_id']} | score={top['score']}")
    print(f"Counts:     {result['entity_type_counts']}")
    print("=" * 80)


if __name__ == "__main__":
    main()