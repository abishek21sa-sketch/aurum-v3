from pathlib import Path
import json
import pandas as pd


GOVERNANCE_DIR = Path("results/governance")
EXECUTION_DIR = Path("results/execution")

PORTFOLIO_PATH = EXECUTION_DIR / "current_portfolio_state.json"

OUTPUT_REPORT_PATH = GOVERNANCE_DIR / "concentration_report.csv"
OUTPUT_SUMMARY_PATH = GOVERNANCE_DIR / "concentration_summary.json"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def extract_weights(portfolio: dict) -> dict:
    if "positions" in portfolio and isinstance(portfolio["positions"], dict):
        return {
            asset: float(weight)
            for asset, weight in portfolio["positions"].items()
            if isinstance(weight, (int, float))
        }

    for key in ["weights", "portfolio_weights", "target_weights", "current_weights"]:
        if key in portfolio and isinstance(portfolio[key], dict):
            return {
                asset: float(weight)
                for asset, weight in portfolio[key].items()
                if isinstance(weight, (int, float))
            }

    raise ValueError("Could not extract portfolio weights.")


def classify_concentration(hhi: float, effective_positions: float, top_3_exposure: float) -> str:
    if hhi >= 0.25 or effective_positions <= 4 or top_3_exposure >= 0.80:
        return "HIGH_CONCENTRATION"
    elif hhi >= 0.15 or effective_positions <= 6 or top_3_exposure >= 0.65:
        return "MODERATE_CONCENTRATION"
    else:
        return "LOW_CONCENTRATION"


def run_concentration_risk_engine() -> tuple[pd.DataFrame, dict]:
    portfolio = load_json(PORTFOLIO_PATH)

    if not portfolio:
        raise FileNotFoundError(
            "Missing current_portfolio_state.json. Run execution layer first."
        )

    weights = extract_weights(portfolio)

    sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)

    hhi = sum(weight ** 2 for weight in weights.values())
    effective_positions = 1 / hhi if hhi > 0 else 0

    top_1_exposure = sum(weight for _, weight in sorted_weights[:1])
    top_3_exposure = sum(weight for _, weight in sorted_weights[:3])
    top_5_exposure = sum(weight for _, weight in sorted_weights[:5])

    concentration_status = classify_concentration(
        hhi=hhi,
        effective_positions=effective_positions,
        top_3_exposure=top_3_exposure,
    )

    rows = []

    for rank, (asset, weight) in enumerate(sorted_weights, start=1):
        rows.append(
            {
                "rank": rank,
                "asset": asset,
                "weight": weight,
                "weight_percent": weight * 100,
                "squared_weight": weight ** 2,
                "contribution_to_hhi_percent": ((weight ** 2) / hhi * 100) if hhi > 0 else 0,
            }
        )

    report = pd.DataFrame(rows)

    summary = {
        "number_of_positions": len(weights),
        "herfindahl_hirschman_index": hhi,
        "effective_number_of_positions": effective_positions,
        "top_1_exposure": top_1_exposure,
        "top_3_exposure": top_3_exposure,
        "top_5_exposure": top_5_exposure,
        "concentration_status": concentration_status,
        "largest_position": sorted_weights[0][0] if sorted_weights else None,
        "largest_position_weight": sorted_weights[0][1] if sorted_weights else 0,
    }

    report.to_csv(OUTPUT_REPORT_PATH, index=False)
    OUTPUT_SUMMARY_PATH.write_text(json.dumps(summary, indent=4), encoding="utf-8")

    return report, summary


def main() -> None:
    print("=" * 80)
    print("AURUM CONCENTRATION RISK ENGINE")
    print("=" * 80)

    report, summary = run_concentration_risk_engine()

    print("\nCONCENTRATION SUMMARY")
    print("-" * 80)
    print(f"Number of positions: {summary['number_of_positions']}")
    print(f"HHI: {summary['herfindahl_hirschman_index']:.4f}")
    print(f"Effective positions: {summary['effective_number_of_positions']:.2f}")
    print(f"Top 1 exposure: {summary['top_1_exposure']:.2%}")
    print(f"Top 3 exposure: {summary['top_3_exposure']:.2%}")
    print(f"Top 5 exposure: {summary['top_5_exposure']:.2%}")
    print(f"Concentration status: {summary['concentration_status']}")

    print("\nTOP HOLDINGS")
    print("-" * 80)
    print(report.head(10).to_string(index=False))

    print(f"\nOutput report: {OUTPUT_REPORT_PATH}")
    print(f"Output summary: {OUTPUT_SUMMARY_PATH}")


if __name__ == "__main__":
    main()