from pathlib import Path
import importlib
import json

from src.factors.factor_engine import InstitutionalFactorEngine


REQUIRED_FACTORS = {
    "value",
    "momentum",
    "quality",
    "growth",
    "carry",
    "low_volatility",
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
    print("AURUM PHASE 6B.3 INSTITUTIONAL FACTOR PLATFORM VALIDATION")
    print("=" * 80)

    importlib.import_module("src.factors.factor_engine")
    importlib.import_module("src.factors.factor_report_generator")
    check(True, "factor modules import")

    result = InstitutionalFactorEngine().run(regime="normal")

    definitions_path = Path("results/factors/factor_definitions.json")
    attribution_path = Path("results/factors/factor_attribution_report.json")
    rotation_path = Path("results/factors/factor_rotation_signal.json")

    for path in [definitions_path, attribution_path, rotation_path]:
        check(path.exists(), f"{path} exists")

    definitions = json.loads(definitions_path.read_text(encoding="utf-8"))
    attribution = json.loads(attribution_path.read_text(encoding="utf-8"))
    rotation = json.loads(rotation_path.read_text(encoding="utf-8"))

    factor_names = {factor["factor"] for factor in definitions["factors"]}

    for factor in REQUIRED_FACTORS:
        check(factor in factor_names, f"{factor} factor defined")

    for factor in definitions["factors"]:
        check(factor.get("economic_logic"), f"{factor['factor']} has economic logic")
        check(factor.get("risk"), f"{factor['factor']} has risk description")

    attribution_factors = {row["factor"] for row in attribution["factor_attribution"]}

    for factor in REQUIRED_FACTORS:
        check(factor in attribution_factors, f"{factor} has attribution mapping")

    check(len(rotation["preferred_factors"]) >= 1, "factor rotation has preferred factors")
    check(rotation["factor_posture"] in {
        "defensive_factor_posture",
        "pro_risk_factor_posture",
        "income_oriented_factor_posture",
        "balanced_factor_posture",
    }, "factor posture is valid", rotation["factor_posture"])

    print("=" * 80)
    print("[PASS] PHASE 6B.3 INSTITUTIONAL FACTOR PLATFORM COMPLETE")
    print("AURUM now has an institutional factor intelligence foundation.")
    print("=" * 80)


if __name__ == "__main__":
    main()