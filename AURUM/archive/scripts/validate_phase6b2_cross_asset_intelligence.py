from pathlib import Path
import importlib
import json

from src.intelligence.cross_asset_engine import CrossAssetIntelligenceEngine


REQUIRED_RELATIONSHIPS = [
    "higher_rates_pressure_equity_valuations",
    "oil_and_commodity_prices_raise_inflation_pressure",
    "strong_usd_pressures_commodities",
    "higher_volatility_pressures_risk_assets",
    "growth_risk_appetite_supports_crypto",
]


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
    print("AURUM PHASE 6B.2 CROSS-ASSET INTELLIGENCE VALIDATION")
    print("=" * 80)

    importlib.import_module("src.intelligence.cross_asset_engine")
    check(True, "cross-asset engine imports")

    summary = CrossAssetIntelligenceEngine().run()

    check(summary["relationship_count"] >= 8, "at least 8 cross-asset relationships", str(summary["relationship_count"]))

    for asset_class in ["rates", "commodities", "fx", "volatility", "equities"]:
        check(
            asset_class in summary["source_asset_class_counts"],
            f"{asset_class} source relationships exist",
        )

    report_path = Path("results/intelligence/cross_asset_dependency_report.json")
    summary_path = Path("results/intelligence/cross_asset_summary.json")

    check(report_path.exists(), "cross_asset_dependency_report.json exists")
    check(summary_path.exists(), "cross_asset_summary.json exists")

    report = json.loads(report_path.read_text(encoding="utf-8"))
    relationship_names = {r["relationship"] for r in report["relationships"]}

    for relationship in REQUIRED_RELATIONSHIPS:
        check(relationship in relationship_names, f"{relationship} relationship exists")

    for rel in report["relationships"]:
        check("economic_logic" in rel and rel["economic_logic"], f"{rel['relationship']} has economic logic")
        check(rel["direction"] in {"positive", "negative"}, f"{rel['relationship']} has valid direction")
        check(rel["sensitivity"] in {"low", "medium", "high"}, f"{rel['relationship']} has valid sensitivity")

    print("=" * 80)
    print("[PASS] PHASE 6B.2 CROSS-ASSET INTELLIGENCE COMPLETE")
    print("AURUM now has a structured cross-asset dependency engine.")
    print("=" * 80)


if __name__ == "__main__":
    main()