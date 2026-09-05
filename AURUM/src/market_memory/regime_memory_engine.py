from __future__ import annotations

from typing import Any, Dict, Optional

from src.market_memory.memory_store import InstitutionalMemoryStore


class RegimeMemoryEngine:
    """
    Stores market regime memories into AURUM institutional memory.
    """

    def __init__(self) -> None:
        self.store = InstitutionalMemoryStore()

    def remember_regime(
        self,
        regime: str,
        volatility: float,
        stress_score: float,
        liquidity_state: str,
        breadth: float,
        confidence: float,
        transition_risk: Optional[float] = None,
        source: str = "regime_memory_engine",
    ) -> Dict[str, Any]:
        regime = regime.lower().strip()

        title = f"Regime Memory: {regime.upper()}"

        description = (
            f"AURUM observed a {regime} regime with volatility={volatility}, "
            f"stress_score={stress_score}, liquidity_state={liquidity_state}, "
            f"breadth={breadth}, and confidence={confidence}."
        )

        return self.store.remember(
            memory_type="REGIME",
            title=title,
            description=description,
            regime=regime,
            market_features={
                "volatility": volatility,
                "stress_score": stress_score,
                "liquidity_state": liquidity_state,
                "breadth": breadth,
                "transition_risk": transition_risk,
            },
            decision={
                "regime_confidence": confidence,
            },
            metadata={
                "source": source,
                "phase": "5C",
            },
        )


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 5C REGIME MEMORY ENGINE")
    print("=" * 80)

    engine = RegimeMemoryEngine()

    record = engine.remember_regime(
        regime="normal",
        volatility=0.0766,
        stress_score=0.1636,
        liquidity_state="healthy",
        breadth=0.40,
        confidence=0.82,
        transition_risk=0.1636,
    )

    print(f"Saved Memory ID: {record['memory_id']}")
    print(f"Type:            {record['memory_type']}")
    print(f"Title:           {record['title']}")
    print(f"Regime:          {record['regime']}")
    print("=" * 80)


if __name__ == "__main__":
    main()