from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple

from src.market_memory.memory_retriever import InstitutionalMemoryRetriever


DEFAULT_FEATURE_WEIGHTS = {
    "volatility": 0.25,
    "stress_score": 0.30,
    "breadth": 0.15,
    "projected_var95": 0.15,
    "projected_drawdown": 0.15,
}


class MarketMemorySimilarityEngine:
    """
    Finds historical AURUM memories similar to the current market state.

    Similarity is based on weighted numeric feature distance.
    """

    def __init__(self) -> None:
        self.retriever = InstitutionalMemoryRetriever()

    @staticmethod
    def _extract_feature(record: Dict[str, Any], feature: str) -> float:
        search_blocks = [
            record.get("market_features", {}) or {},
            record.get("risk_metrics", {}) or {},
            record.get("decision", {}) or {},
            record.get("outcome", {}) or {},
            record.get("metadata", {}) or {},
        ]

        for block in search_blocks:
            if feature in block:
                try:
                    return float(block[feature])
                except Exception:
                    return 0.0

        return 0.0

    @staticmethod
    def _normalize_distance(distance: float) -> float:
        return 1.0 / (1.0 + distance)

    def weighted_similarity(
        self,
        current_state: Dict[str, Any],
        memory_record: Dict[str, Any],
        weights: Dict[str, float] | None = None,
    ) -> Tuple[float, Dict[str, float]]:
        weights = weights or DEFAULT_FEATURE_WEIGHTS

        weighted_distance = 0.0
        feature_diffs: Dict[str, float] = {}

        for feature, weight in weights.items():
            try:
                current_value = float(current_state.get(feature, 0.0))
            except Exception:
                current_value = 0.0

            memory_value = self._extract_feature(memory_record, feature)

            diff = abs(current_value - memory_value)
            feature_diffs[feature] = diff
            weighted_distance += weight * diff

        similarity = self._normalize_distance(weighted_distance)

        return similarity, feature_diffs

    def cosine_similarity(
        self,
        current_state: Dict[str, Any],
        memory_record: Dict[str, Any],
        features: List[str] | None = None,
    ) -> float:
        features = features or list(DEFAULT_FEATURE_WEIGHTS.keys())

        current_vector = []
        memory_vector = []

        for feature in features:
            try:
                current_vector.append(float(current_state.get(feature, 0.0)))
            except Exception:
                current_vector.append(0.0)

            memory_vector.append(self._extract_feature(memory_record, feature))

        dot = sum(a * b for a, b in zip(current_vector, memory_vector))
        norm_a = math.sqrt(sum(a * a for a in current_vector))
        norm_b = math.sqrt(sum(b * b for b in memory_vector))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot / (norm_a * norm_b)

    def find_similar_memories(
        self,
        current_state: Dict[str, Any],
        limit: int = 5,
        memory_types: List[str] | None = None,
    ) -> List[Dict[str, Any]]:
        records = self.retriever.load_all()

        if memory_types:
            allowed = {m.upper() for m in memory_types}
            records = [
                r for r in records
                if str(r.get("memory_type", "")).upper() in allowed
            ]

        scored = []

        for record in records:
            weighted_score, feature_diffs = self.weighted_similarity(
                current_state=current_state,
                memory_record=record,
            )
            cosine_score = self.cosine_similarity(
                current_state=current_state,
                memory_record=record,
            )

            combined_score = (0.70 * weighted_score) + (0.30 * cosine_score)

            scored.append(
                {
                    "memory_id": record.get("memory_id"),
                    "title": record.get("title"),
                    "timestamp": record.get("timestamp"),
                    "memory_type": record.get("memory_type"),
                    "regime": record.get("regime"),
                    "similarity": round(combined_score, 4),
                    "similarity_percent": round(combined_score * 100, 2),
                    "weighted_similarity": round(weighted_score, 4),
                    "cosine_similarity": round(cosine_score, 4),
                    "feature_diffs": feature_diffs,
                    "record": record,
                }
            )

        return sorted(scored, key=lambda x: x["similarity"], reverse=True)[:limit]

    def current_market_resemblance_report(
        self,
        current_state: Dict[str, Any],
        limit: int = 5,
    ) -> Dict[str, Any]:
        matches = self.find_similar_memories(current_state=current_state, limit=limit)

        best = matches[0] if matches else None

        return {
            "question": "Have we seen this before?",
            "current_state": current_state,
            "best_match": best,
            "top_matches": matches,
            "memory_count_checked": len(self.retriever.load_all()),
        }


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 5C MEMORY SIMILARITY ENGINE")
    print("=" * 80)

    current_state = {
        "volatility": 0.0836,
        "stress_score": 0.40,
        "breadth": 0.40,
        "projected_var95": 0.1300,
        "projected_drawdown": -0.0641,
    }

    engine = MarketMemorySimilarityEngine()
    report = engine.current_market_resemblance_report(current_state=current_state)

    print("QUESTION: Have we seen this before?")
    print("-" * 80)
    print(f"Memory Count Checked: {report['memory_count_checked']}")

    best = report["best_match"]

    if best:
        print(f"Best Match:           {best['title']}")
        print(f"Regime:               {best['regime']}")
        print(f"Similarity:           {best['similarity_percent']}%")
        print(f"Memory Type:          {best['memory_type']}")
        print(f"Timestamp:            {best['timestamp']}")
    else:
        print("Best Match:           None")

    print("=" * 80)


if __name__ == "__main__":
    main()