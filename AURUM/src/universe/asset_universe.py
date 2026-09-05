from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List
from datetime import datetime, timezone
import json


RESULTS_DIR = Path("results/universe")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class Asset:
    ticker: str
    name: str
    asset_class: str
    region: str
    currency: str
    data_provider_symbol: str
    role: str


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def institutional_universe() -> List[Asset]:
    return [
        Asset("SPY", "S&P 500 ETF", "equities", "US", "USD", "SPY", "us_large_cap"),
        Asset("QQQ", "Nasdaq 100 ETF", "equities", "US", "USD", "QQQ", "us_growth"),
        Asset("DIA", "Dow Jones ETF", "equities", "US", "USD", "DIA", "us_blue_chip"),
        Asset("IWM", "Russell 2000 ETF", "equities", "US", "USD", "IWM", "us_small_cap"),
        Asset("EFA", "Developed Markets ETF", "equities", "International", "USD", "EFA", "developed_ex_us"),
        Asset("EEM", "Emerging Markets ETF", "equities", "International", "USD", "EEM", "emerging_markets"),

        Asset("TLT", "20+ Year Treasury ETF", "rates", "US", "USD", "TLT", "long_duration"),
        Asset("IEF", "7-10 Year Treasury ETF", "rates", "US", "USD", "IEF", "intermediate_duration"),
        Asset("SHY", "1-3 Year Treasury ETF", "rates", "US", "USD", "SHY", "short_duration"),
        Asset("US10Y", "US 10Y Treasury Yield", "rates", "US", "USD", "^TNX", "benchmark_yield"),
        Asset("US2Y", "US 2Y Treasury Yield", "rates", "US", "USD", "^IRX", "front_end_yield"),

        Asset("GLD", "Gold ETF", "commodities", "Global", "USD", "GLD", "gold"),
        Asset("SLV", "Silver ETF", "commodities", "Global", "USD", "SLV", "silver"),
        Asset("DBC", "Commodity Basket ETF", "commodities", "Global", "USD", "DBC", "commodity_basket"),
        Asset("WTI", "Crude Oil", "commodities", "Global", "USD", "CL=F", "oil"),
        Asset("COPPER", "Copper", "commodities", "Global", "USD", "HG=F", "industrial_metal"),

        Asset("EURUSD", "Euro / US Dollar", "fx", "Global", "USD", "EURUSD=X", "developed_fx"),
        Asset("USDJPY", "US Dollar / Japanese Yen", "fx", "Global", "JPY", "JPY=X", "safe_haven_fx"),
        Asset("GBPUSD", "British Pound / US Dollar", "fx", "Global", "USD", "GBPUSD=X", "developed_fx"),
        Asset("USDCAD", "US Dollar / Canadian Dollar", "fx", "Global", "CAD", "CAD=X", "commodity_fx"),

        Asset("BTC-USD", "Bitcoin", "crypto", "Global", "USD", "BTC-USD", "crypto_beta"),
        Asset("ETH-USD", "Ethereum", "crypto", "Global", "USD", "ETH-USD", "crypto_platform"),

        Asset("VIX", "CBOE Volatility Index", "volatility", "US", "USD", "^VIX", "equity_volatility"),
    ]


class AssetUniverse:
    def __init__(self) -> None:
        self.assets = institutional_universe()

    def to_records(self) -> List[Dict]:
        return [asdict(asset) for asset in self.assets]

    def by_asset_class(self) -> Dict[str, List[Dict]]:
        grouped: Dict[str, List[Dict]] = {}
        for asset in self.to_records():
            grouped.setdefault(asset["asset_class"], []).append(asset)
        return grouped

    def summary(self) -> Dict:
        grouped = self.by_asset_class()
        return {
            "timestamp": utc_now(),
            "universe_name": "AURUM_INSTITUTIONAL_MULTI_ASSET_UNIVERSE",
            "asset_count": len(self.assets),
            "asset_classes": sorted(grouped.keys()),
            "asset_class_counts": {
                asset_class: len(items)
                for asset_class, items in grouped.items()
            },
        }

    def save(self) -> Dict:
        universe = {
            "timestamp": utc_now(),
            "universe": self.to_records(),
        }

        summary = self.summary()
        breakdown = self.by_asset_class()

        (RESULTS_DIR / "institutional_asset_universe.json").write_text(
            json.dumps(universe, indent=2),
            encoding="utf-8",
        )

        (RESULTS_DIR / "universe_summary.json").write_text(
            json.dumps(summary, indent=2),
            encoding="utf-8",
        )

        (RESULTS_DIR / "asset_class_breakdown.json").write_text(
            json.dumps(breakdown, indent=2),
            encoding="utf-8",
        )

        return summary


def main() -> None:
    summary = AssetUniverse().save()

    print("=" * 80)
    print("AURUM PHASE 6B.1 MULTI-ASSET UNIVERSE")
    print("=" * 80)
    print(f"Universe: {summary['universe_name']}")
    print(f"Assets:   {summary['asset_count']}")
    print(f"Classes:  {', '.join(summary['asset_classes'])}")
    print("-" * 80)

    for asset_class, count in summary["asset_class_counts"].items():
        print(f"{asset_class.upper():15} {count}")

    print("=" * 80)


if __name__ == "__main__":
    main()