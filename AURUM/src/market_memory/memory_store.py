from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


MEMORY_DIR = Path("results/memory")
MEMORY_DB_PATH = MEMORY_DIR / "institutional_memory.jsonl"
MEMORY_INDEX_PATH = MEMORY_DIR / "institutional_memory_index.json"


VALID_MEMORY_TYPES = {
    "REGIME",
    "CRISIS",
    "ALLOCATION",
    "DECISION",
    "COMMITTEE",
    "OUTCOME",
    "DIGITAL_TWIN",
}


@dataclass
class MemoryRecord:
    memory_id: str
    timestamp: str
    memory_type: str
    title: str
    description: str

    regime: Optional[str] = None
    market_features: Dict[str, Any] = field(default_factory=dict)
    decision: Dict[str, Any] = field(default_factory=dict)
    allocation: Dict[str, Any] = field(default_factory=dict)
    risk_metrics: Dict[str, Any] = field(default_factory=dict)
    committee_vote: Dict[str, Any] = field(default_factory=dict)
    outcome: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class InstitutionalMemoryStore:
    """
    Append-only institutional memory store for AURUM.

    This is the permanent memory layer.

    It stores:
    - regimes
    - crises
    - allocations
    - AI decisions
    - committee votes
    - outcomes
    - digital twin states

    Database:
        results/memory/institutional_memory.jsonl

    Index:
        results/memory/institutional_memory_index.json
    """

    def __init__(
        self,
        memory_db_path: Path = MEMORY_DB_PATH,
        memory_index_path: Path = MEMORY_INDEX_PATH,
    ) -> None:
        self.memory_db_path = Path(memory_db_path)
        self.memory_index_path = Path(memory_index_path)
        self.memory_db_path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _stable_hash(payload: Dict[str, Any]) -> str:
        raw = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]

    def create_record(
        self,
        memory_type: str,
        title: str,
        description: str,
        regime: Optional[str] = None,
        market_features: Optional[Dict[str, Any]] = None,
        decision: Optional[Dict[str, Any]] = None,
        allocation: Optional[Dict[str, Any]] = None,
        risk_metrics: Optional[Dict[str, Any]] = None,
        committee_vote: Optional[Dict[str, Any]] = None,
        outcome: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[str] = None,
    ) -> MemoryRecord:
        memory_type = memory_type.upper().strip()

        if memory_type not in VALID_MEMORY_TYPES:
            raise ValueError(
                f"Invalid memory_type={memory_type}. "
                f"Expected one of {sorted(VALID_MEMORY_TYPES)}"
            )

        ts = timestamp or self._utc_now()

        base_payload = {
            "timestamp": ts,
            "memory_type": memory_type,
            "title": title,
            "description": description,
            "regime": regime,
            "market_features": market_features or {},
            "decision": decision or {},
            "allocation": allocation or {},
            "risk_metrics": risk_metrics or {},
            "committee_vote": committee_vote or {},
            "outcome": outcome or {},
            "metadata": metadata or {},
        }

        memory_id = self._stable_hash(base_payload)

        return MemoryRecord(
            memory_id=memory_id,
            timestamp=ts,
            memory_type=memory_type,
            title=title,
            description=description,
            regime=regime,
            market_features=market_features or {},
            decision=decision or {},
            allocation=allocation or {},
            risk_metrics=risk_metrics or {},
            committee_vote=committee_vote or {},
            outcome=outcome or {},
            metadata=metadata or {},
        )

    def append_memory(self, record: MemoryRecord) -> Dict[str, Any]:
        self.memory_db_path.parent.mkdir(parents=True, exist_ok=True)

        payload = asdict(record)

        with self.memory_db_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, default=str) + "\n")

        self._update_index(payload)

        return payload

    def remember(
        self,
        memory_type: str,
        title: str,
        description: str,
        regime: Optional[str] = None,
        market_features: Optional[Dict[str, Any]] = None,
        decision: Optional[Dict[str, Any]] = None,
        allocation: Optional[Dict[str, Any]] = None,
        risk_metrics: Optional[Dict[str, Any]] = None,
        committee_vote: Optional[Dict[str, Any]] = None,
        outcome: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[str] = None,
    ) -> Dict[str, Any]:
        record = self.create_record(
            memory_type=memory_type,
            title=title,
            description=description,
            regime=regime,
            market_features=market_features,
            decision=decision,
            allocation=allocation,
            risk_metrics=risk_metrics,
            committee_vote=committee_vote,
            outcome=outcome,
            metadata=metadata,
            timestamp=timestamp,
        )

        return self.append_memory(record)

    def load_all(self) -> List[Dict[str, Any]]:
        if not self.memory_db_path.exists():
            return []

        records: List[Dict[str, Any]] = []

        with self.memory_db_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        return records

    def _update_index(self, record: Dict[str, Any]) -> None:
        index = self.load_index()

        memory_type = record.get("memory_type", "UNKNOWN")
        regime = record.get("regime") or "UNKNOWN"

        index["total_records"] = int(index.get("total_records", 0)) + 1
        index["last_updated"] = self._utc_now()

        index.setdefault("by_type", {})
        index["by_type"][memory_type] = int(index["by_type"].get(memory_type, 0)) + 1

        index.setdefault("by_regime", {})
        index["by_regime"][regime] = int(index["by_regime"].get(regime, 0)) + 1

        index.setdefault("latest_records", [])
        index["latest_records"].append(
            {
                "memory_id": record.get("memory_id"),
                "timestamp": record.get("timestamp"),
                "memory_type": memory_type,
                "title": record.get("title"),
                "regime": regime,
            }
        )

        index["latest_records"] = index["latest_records"][-25:]

        with self.memory_index_path.open("w", encoding="utf-8") as f:
            json.dump(index, f, indent=2)

    def load_index(self) -> Dict[str, Any]:
        if not self.memory_index_path.exists():
            return {
                "total_records": 0,
                "last_updated": None,
                "by_type": {},
                "by_regime": {},
                "latest_records": [],
            }

        try:
            with self.memory_index_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {
                "total_records": 0,
                "last_updated": None,
                "by_type": {},
                "by_regime": {},
                "latest_records": [],
            }


def seed_demo_memory() -> Dict[str, Any]:
    store = InstitutionalMemoryStore()

    record = store.remember(
        memory_type="REGIME",
        title="Demo Memory: Defensive Market State",
        description=(
            "AURUM observed a defensive market state with elevated risk, "
            "higher cash preference, and reduced equity allocation."
        ),
        regime="defensive",
        market_features={
            "volatility": 0.0836,
            "stress_score": 0.40,
            "liquidity_state": "healthy",
            "breadth": 0.40,
        },
        decision={
            "recommended_posture": "reduce_risk",
            "execution_permission": "blocked",
            "confidence": 0.82,
        },
        allocation={
            "SPY": 0.1905,
            "QQQ": 0.1820,
            "DIA": 0.1330,
            "TLT": 0.2095,
            "GLD": 0.1425,
            "CASH": 0.1425,
        },
        risk_metrics={
            "projected_var95": 0.1300,
            "projected_cvar95": 0.0745,
            "projected_drawdown": -0.0641,
        },
        metadata={
            "phase": "5C",
            "source": "demo_seed",
        },
    )

    return record


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 5C MEMORY STORE")
    print("=" * 80)

    store = InstitutionalMemoryStore()
    record = seed_demo_memory()
    index = store.load_index()

    print(f"Saved Memory ID: {record['memory_id']}")
    print(f"Memory Type:     {record['memory_type']}")
    print(f"Regime:          {record['regime']}")
    print(f"Database:        {MEMORY_DB_PATH}")
    print(f"Index:           {MEMORY_INDEX_PATH}")
    print("-" * 80)
    print(f"Total Records:   {index.get('total_records')}")
    print(f"By Type:         {index.get('by_type')}")
    print(f"By Regime:       {index.get('by_regime')}")
    print("=" * 80)


if __name__ == "__main__":
    main()