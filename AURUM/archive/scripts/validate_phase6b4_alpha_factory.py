from pathlib import Path
import importlib
import json

from src.alpha.alpha_factory import AlphaFactory
from src.alpha.alpha_registry import AlphaRegistry


REQUIRED_ALPHA_IDS = {
    "ALPHA_MOMENTUM_001",
    "ALPHA_RATES_001",
    "ALPHA_VOL_001",
    "ALPHA_COMMODITY_001",
    "ALPHA_FX_001",
    "ALPHA_QUALITY_001",
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
    print("AURUM PHASE 6B.4 ALPHA RESEARCH FACTORY VALIDATION")
    print("=" * 80)

    importlib.import_module("src.alpha.alpha_factory")
    importlib.import_module("src.alpha.alpha_registry")
    importlib.import_module("src.alpha.alpha_report_generator")
    check(True, "alpha modules import")

    result = AlphaFactory().run()

    registry_path = Path("results/alpha/alpha_registry.json")
    scorecard_path = Path("results/alpha/alpha_scorecard.json")
    rankings_path = Path("results/alpha/top_alpha_rankings.json")

    for path in [registry_path, scorecard_path, rankings_path]:
        check(path.exists(), f"{path} exists")

    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    scorecard = json.loads(scorecard_path.read_text(encoding="utf-8"))
    rankings = json.loads(rankings_path.read_text(encoding="utf-8"))

    check(registry["alpha_count"] >= 6, "at least 6 alpha ideas registered", str(registry["alpha_count"]))

    alpha_ids = {alpha["alpha_id"] for alpha in registry["alphas"]}

    for alpha_id in REQUIRED_ALPHA_IDS:
        check(alpha_id in alpha_ids, f"{alpha_id} registered")

    for alpha in registry["alphas"]:
        check(alpha.get("hypothesis"), f"{alpha['alpha_id']} has hypothesis")
        check(alpha.get("universe"), f"{alpha['alpha_id']} has universe")
        check(alpha.get("metrics"), f"{alpha['alpha_id']} has metrics")
        check(alpha.get("alpha_score") is not None, f"{alpha['alpha_id']} has alpha score")

    scores = [row["alpha_score"] for row in scorecard["scorecard"]]
    check(scores == sorted(scores, reverse=True), "scorecard sorted descending")

    check(rankings["best_alpha"] is not None, "best alpha selected")
    check(len(rankings["top_alphas"]) >= 3, "top alpha rankings generated")

    registry_reader = AlphaRegistry()
    loaded_ids = set(registry_reader.list_alpha_ids())

    for alpha_id in REQUIRED_ALPHA_IDS:
        check(alpha_id in loaded_ids, f"{alpha_id} retrievable from registry")

    print("=" * 80)
    print("[PASS] PHASE 6B.4 ALPHA RESEARCH FACTORY COMPLETE")
    print("AURUM now generates, scores, stores, and ranks alpha research ideas.")
    print("=" * 80)


if __name__ == "__main__":
    main()