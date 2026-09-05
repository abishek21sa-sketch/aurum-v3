from __future__ import annotations

from typing import Any, Dict

from src.market_memory.memory_store import InstitutionalMemoryStore


class AllocationMemoryEngine:
    """
    Stores portfolio allocation memories and their performance outcomes.
    """

    def __init__(self) -> None:
        self.store = InstitutionalMemoryStore()

    def remember_allocation(
        self,
        allocation_name: str,
        regime: str,
        allocation: Dict[str, float],
        expected_return: float,
        volatility: float,
        sharpe: float,
        max_drawdown: float,
        cvar: float,
        realized_30d_return: float | None = None,
        realized_90d_return: float | None = None,
        source: str = "allocation_memory_engine",
    ) -> Dict[str, Any]:
        regime = regime.lower().strip()

        title = f"Allocation Memory: {allocation_name}"

        description = (
            f"AURUM stored allocation '{allocation_name}' under {regime} regime. "
            f"Expected return={expected_return}, volatility={volatility}, "
            f"Sharpe={sharpe}, max_drawdown={max_drawdown}, CVaR={cvar}."
        )

        return self.store.remember(
            memory_type="ALLOCATION",
            title=title,
            description=description,
            regime=regime,
            allocation=allocation,
            risk_metrics={
                "expected_return": expected_return,
                "volatility": volatility,
                "sharpe": sharpe,
                "max_drawdown": max_drawdown,
                "cvar": cvar,
            },
            outcome={
                "realized_30d_return": realized_30d_return,
                "realized_90d_return": realized_90d_return,
                "sharpe": sharpe,
                "max_drawdown": max_drawdown,
            },
            metadata={
                "source": source,
                "phase": "5C",
                "allocation_name": allocation_name,
            },
        )


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 5C ALLOCATION MEMORY ENGINE")
    print("=" * 80)

    engine = AllocationMemoryEngine()

    record = engine.remember_allocation(
        allocation_name="Defensive Reoptimized Portfolio",
        regime="defensive",
        allocation={
            "SPY": 0.1905,
            "QQQ": 0.1820,
            "DIA": 0.1330,
            "TLT": 0.2095,
            "GLD": 0.1425,
            "CASH": 0.1425,
        },
        expected_return=0.0667,
        volatility=0.0767,
        sharpe=0.8696,
        max_drawdown=0.1699,
        cvar=0.1800,
        realized_30d_return=None,
        realized_90d_return=None,
    )

    print(f"Saved Memory ID: {record['memory_id']}")
    print(f"Type:            {record['memory_type']}")
    print(f"Title:           {record['title']}")
    print(f"Regime:          {record['regime']}")
    print(f"Sharpe:          {record['outcome'].get('sharpe')}")
    print("=" * 80)


if __name__ == "__main__":
    main()