from __future__ import annotations

from typing import Any, Dict, Optional

from src.market_memory.memory_store import InstitutionalMemoryStore


class CrisisMemoryEngine:
    """
    Stores crisis and stress-event memories into AURUM institutional memory.
    """

    def __init__(self) -> None:
        self.store = InstitutionalMemoryStore()

    def remember_crisis(
        self,
        crisis_name: str,
        regime: str,
        drawdown: float,
        var95: float,
        cvar95: float,
        stress_score: float,
        volatility: float,
        liquidity_state: str,
        outcome_label: str,
        best_response: Optional[str] = None,
        source: str = "crisis_memory_engine",
    ) -> Dict[str, Any]:
        crisis_key = crisis_name.lower().strip().replace(" ", "_")
        regime = regime.lower().strip()

        title = f"Crisis Memory: {crisis_name}"

        description = (
            f"AURUM recorded crisis event '{crisis_name}' under {regime} regime. "
            f"Observed drawdown={drawdown}, VaR95={var95}, CVaR95={cvar95}, "
            f"stress_score={stress_score}, volatility={volatility}, "
            f"liquidity_state={liquidity_state}."
        )

        return self.store.remember(
            memory_type="CRISIS",
            title=title,
            description=description,
            regime=regime,
            market_features={
                "crisis_name": crisis_key,
                "volatility": volatility,
                "stress_score": stress_score,
                "liquidity_state": liquidity_state,
            },
            risk_metrics={
                "projected_drawdown": drawdown,
                "projected_var95": var95,
                "projected_cvar95": cvar95,
            },
            outcome={
                "outcome_label": outcome_label,
                "best_response": best_response,
            },
            metadata={
                "source": source,
                "phase": "5C",
            },
        )


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 5C CRISIS MEMORY ENGINE")
    print("=" * 80)

    engine = CrisisMemoryEngine()

    record = engine.remember_crisis(
        crisis_name="Global Contagion Stress",
        regime="stressed",
        drawdown=-0.1933,
        var95=0.2100,
        cvar95=0.2900,
        stress_score=0.91,
        volatility=0.4200,
        liquidity_state="fragile",
        outcome_label="severe_drawdown",
        best_response="Raise cash, reduce equity beta, increase TLT/GLD hedge sleeve.",
    )

    print(f"Saved Memory ID: {record['memory_id']}")
    print(f"Type:            {record['memory_type']}")
    print(f"Title:           {record['title']}")
    print(f"Regime:          {record['regime']}")
    print(f"Outcome:         {record['outcome'].get('outcome_label')}")
    print("=" * 80)


if __name__ == "__main__":
    main()