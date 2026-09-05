from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List
import json


RESULTS_DIR = Path("results/portfolio_lab_2")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ScenarioLibrary:
    def scenarios(self) -> List[Dict]:
        return [
            {
                "scenario_id": "SCENARIO_INFLATION_SPIKE",
                "name": "Inflation Spike",
                "question": "What if inflation spikes?",
                "shock_type": "macro_inflation",
                "asset_shocks": {
                    "SPY": -0.05,
                    "QQQ": -0.08,
                    "DIA": -0.03,
                    "IWM": -0.06,
                    "TLT": -0.10,
                    "IEF": -0.05,
                    "SHY": -0.01,
                    "GLD": 0.04,
                    "DBC": 0.07,
                    "WTI": 0.10,
                    "COPPER": 0.05,
                    "BTC-USD": -0.04,
                    "ETH-USD": -0.06,
                    "VIX": 0.25,
                },
                "institutional_logic": "Inflation pressure hurts duration assets and growth equities while supporting commodities and volatility.",
            },
            {
                "scenario_id": "SCENARIO_RATES_UP_100BPS",
                "name": "Rates Rise 100 bps",
                "question": "What if rates rise 100 bps?",
                "shock_type": "rates_shock",
                "asset_shocks": {
                    "SPY": -0.04,
                    "QQQ": -0.09,
                    "DIA": -0.03,
                    "IWM": -0.05,
                    "TLT": -0.14,
                    "IEF": -0.07,
                    "SHY": -0.015,
                    "GLD": -0.03,
                    "BTC-USD": -0.08,
                    "ETH-USD": -0.10,
                    "VIX": 0.20,
                },
                "institutional_logic": "Higher rates pressure long-duration bonds, growth equities, and speculative assets.",
            },
            {
                "scenario_id": "SCENARIO_NVDA_DOWN_30",
                "name": "Mega-Cap AI Shock",
                "question": "What if NVDA falls 30%?",
                "shock_type": "single_name_growth_proxy",
                "asset_shocks": {
                    "QQQ": -0.08,
                    "SPY": -0.04,
                    "IWM": -0.02,
                    "DIA": -0.015,
                    "BTC-USD": -0.04,
                    "ETH-USD": -0.05,
                    "VIX": 0.18,
                    "TLT": 0.03,
                    "GLD": 0.02,
                },
                "institutional_logic": "A large AI-leadership selloff can pressure growth, tech, crypto beta, and increase volatility.",
            },
            {
                "scenario_id": "SCENARIO_LIQUIDITY_DISAPPEARS",
                "name": "Liquidity Disappears",
                "question": "What if liquidity disappears?",
                "shock_type": "liquidity_crisis",
                "asset_shocks": {
                    "SPY": -0.09,
                    "QQQ": -0.12,
                    "DIA": -0.07,
                    "IWM": -0.14,
                    "EEM": -0.13,
                    "TLT": 0.04,
                    "SHY": 0.01,
                    "GLD": 0.03,
                    "BTC-USD": -0.18,
                    "ETH-USD": -0.22,
                    "VIX": 0.45,
                },
                "institutional_logic": "Liquidity shocks punish risky and speculative assets while favoring cash-like and defensive exposures.",
            },
            {
                "scenario_id": "SCENARIO_CRYPTO_CRASH",
                "name": "Crypto Crash",
                "question": "What if crypto crashes?",
                "shock_type": "crypto_crash",
                "asset_shocks": {
                    "BTC-USD": -0.30,
                    "ETH-USD": -0.38,
                    "QQQ": -0.04,
                    "SPY": -0.025,
                    "IWM": -0.035,
                    "VIX": 0.12,
                    "GLD": 0.01,
                    "TLT": 0.015,
                },
                "institutional_logic": "Crypto crashes directly damage crypto exposures and can spill into speculative growth assets.",
            },
            {
                "scenario_id": "SCENARIO_USD_SURGE",
                "name": "US Dollar Surge",
                "question": "What if the US dollar surges?",
                "shock_type": "fx_tightening",
                "asset_shocks": {
                    "EURUSD": -0.06,
                    "GBPUSD": -0.05,
                    "USDJPY": 0.05,
                    "USDCAD": 0.04,
                    "EEM": -0.08,
                    "DBC": -0.05,
                    "GLD": -0.04,
                    "COPPER": -0.06,
                    "SPY": -0.025,
                    "QQQ": -0.03,
                    "VIX": 0.12,
                },
                "institutional_logic": "A strong dollar tightens global financial conditions and pressures commodities and emerging markets.",
            },
        ]

    def save(self) -> Dict:
        payload = {
            "timestamp": utc_now(),
            "scenario_count": len(self.scenarios()),
            "scenarios": self.scenarios(),
        }

        (RESULTS_DIR / "scenario_library.json").write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )

        return payload


def main() -> None:
    payload = ScenarioLibrary().save()

    print("=" * 80)
    print("AURUM PORTFOLIO LAB 2.0 SCENARIO LIBRARY")
    print("=" * 80)
    print(f"Scenarios: {payload['scenario_count']}")
    for scenario in payload["scenarios"]:
        print(f"- {scenario['scenario_id']} | {scenario['name']}")
    print("=" * 80)


if __name__ == "__main__":
    main()