from pathlib import Path
import importlib
import json

from src.universe.asset_universe import AssetUniverse


REQUIRED_CLASSES = {
    "equities",
    "rates",
    "commodities",
    "fx",
    "crypto",
    "volatility",
}


def check(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        print(f"[PASS] {label}")
        if detail:
            print(f"       {detail}")
    else:
        print(f"[FAIL] {label}")
        if detail:
            print(f"       {detail}")
        raise SystemExit(1)


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 6B.1 MULTI-ASSET UNIVERSE VALIDATION")
    print("=" * 80)

    importlib.import_module("src.universe.asset_universe")
    importlib.import_module("src.universe.universe_report_generator")

    check(True, "universe modules import")

    summary = AssetUniverse().save()

    check(summary["asset_count"] >= 20, "universe has at least 20 assets", str(summary["asset_count"]))

    classes = set(summary["asset_classes"])
    for asset_class in REQUIRED_CLASSES:
        check(asset_class in classes, f"{asset_class} asset class exists")

    for path in [
        Path("results/universe/institutional_asset_universe.json"),
        Path("results/universe/universe_summary.json"),
        Path("results/universe/asset_class_breakdown.json"),
    ]:
        check(path.exists(), f"{path} exists")

    universe = json.loads(
        Path("results/universe/institutional_asset_universe.json").read_text(encoding="utf-8")
    )["universe"]

    tickers = {asset["ticker"] for asset in universe}

    for ticker in ["SPY", "QQQ", "TLT", "GLD", "BTC-USD", "ETH-USD", "VIX", "EURUSD", "USDJPY", "WTI", "COPPER"]:
        check(ticker in tickers, f"{ticker} included")

    print("=" * 80)
    print("[PASS] PHASE 6B.1 MULTI-ASSET UNIVERSE COMPLETE")
    print("AURUM now has an institutional multi-asset universe foundation.")
    print("=" * 80)


if __name__ == "__main__":
    main()