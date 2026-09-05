from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.market_memory.memory_store import MEMORY_DB_PATH, InstitutionalMemoryStore


class InstitutionalMemoryRetriever:
    """
    Search and retrieve AURUM institutional memory records.
    """

    def __init__(self, memory_db_path: Path = MEMORY_DB_PATH) -> None:
        self.store = InstitutionalMemoryStore(memory_db_path=memory_db_path)

    def load_all(self) -> List[Dict[str, Any]]:
        return self.store.load_all()

    def get_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        records = self.load_all()
        return sorted(records, key=lambda x: x.get("timestamp", ""), reverse=True)[:limit]

    def get_by_type(self, memory_type: str) -> List[Dict[str, Any]]:
        memory_type = memory_type.upper().strip()
        return [
            r for r in self.load_all()
            if str(r.get("memory_type", "")).upper() == memory_type
        ]

    def get_by_regime(self, regime: str) -> List[Dict[str, Any]]:
        regime = regime.lower().strip()
        return [
            r for r in self.load_all()
            if str(r.get("regime", "")).lower() == regime
        ]

    def get_by_crisis(self, crisis_name: str) -> List[Dict[str, Any]]:
        crisis_name = crisis_name.lower().strip()

        results = []
        for r in self.load_all():
            text_blob = json.dumps(r, default=str).lower()
            if r.get("memory_type") == "CRISIS" and crisis_name in text_blob:
                results.append(r)

        return results

    def get_by_memory_id(self, memory_id: str) -> Optional[Dict[str, Any]]:
        memory_id = memory_id.strip()
        for r in self.load_all():
            if r.get("memory_id") == memory_id:
                return r
        return None

    def get_best_allocations(
        self,
        metric: str = "sharpe",
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        records = [
            r for r in self.load_all()
            if r.get("memory_type") == "ALLOCATION"
        ]

        def score(record: Dict[str, Any]) -> float:
            outcome = record.get("outcome", {}) or {}
            value = outcome.get(metric)
            try:
                return float(value)
            except Exception:
                return float("-inf")

        return sorted(records, key=score, reverse=True)[:limit]

    def get_worst_allocations(
        self,
        metric: str = "max_drawdown",
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        records = [
            r for r in self.load_all()
            if r.get("memory_type") == "ALLOCATION"
        ]

        def score(record: Dict[str, Any]) -> float:
            outcome = record.get("outcome", {}) or {}
            value = outcome.get(metric)
            try:
                return float(value)
            except Exception:
                return float("inf")

        return sorted(records, key=score)[:limit]

    def search_text(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        query = query.lower().strip()

        matches = []
        for r in self.load_all():
            text_blob = json.dumps(r, default=str).lower()
            if query in text_blob:
                matches.append(r)

        return matches[:limit]

    def summary(self) -> Dict[str, Any]:
        records = self.load_all()

        by_type: Dict[str, int] = {}
        by_regime: Dict[str, int] = {}

        for r in records:
            memory_type = r.get("memory_type", "UNKNOWN")
            regime = r.get("regime") or "UNKNOWN"

            by_type[memory_type] = by_type.get(memory_type, 0) + 1
            by_regime[regime] = by_regime.get(regime, 0) + 1

        return {
            "total_records": len(records),
            "by_type": by_type,
            "by_regime": by_regime,
            "latest": self.get_recent(limit=5),
        }


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 5C MEMORY RETRIEVER")
    print("=" * 80)

    retriever = InstitutionalMemoryRetriever()

    summary = retriever.summary()
    recent = retriever.get_recent(limit=5)
    defensive = retriever.get_by_regime("defensive")

    print(f"Total Records:       {summary['total_records']}")
    print(f"Records By Type:     {summary['by_type']}")
    print(f"Records By Regime:   {summary['by_regime']}")
    print("-" * 80)
    print(f"Recent Records:      {len(recent)}")
    print(f"Defensive Memories:  {len(defensive)}")

    if recent:
        latest = recent[0]
        print("-" * 80)
        print("LATEST MEMORY")
        print(f"ID:          {latest.get('memory_id')}")
        print(f"Type:        {latest.get('memory_type')}")
        print(f"Title:       {latest.get('title')}")
        print(f"Regime:      {latest.get('regime')}")
        print(f"Timestamp:   {latest.get('timestamp')}")

    print("=" * 80)


if __name__ == "__main__":
    main()