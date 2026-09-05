# src/monitoring/benchmark_comparison_engine.py

import json
from pathlib import Path

import pandas as pd


MONITORING_DIR = Path("results/monitoring")
MONITORING_DIR.mkdir(parents=True, exist_ok=True)

ATTRIBUTION_SUMMARY_PATH = MONITORING_DIR / "performance_attribution_summary.json"

OUTPUT_PATH = MONITORING_DIR / "benchmark_report.csv"
SUMMARY_PATH = MONITORING_DIR / "benchmark_summary.json"


BENCHMARKS = {
    "SPY": {
        "return": 0.0020,
        "volatility": 0.0100,
    },
    "60_40": {
        "return": 0.0018,
        "volatility": 0.0070,
    },
    "risk_parity_benchmark": {
        "return": 0.0019,
        "volatility": 0.0065,
    },
}


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def run_benchmark_comparison() -> pd.DataFrame:
    attribution_summary = load_json(ATTRIBUTION_SUMMARY_PATH)

    portfolio_return = float(attribution_summary["portfolio_return"])
    portfolio_volatility = 0.0060

    rows = []

    for benchmark, metrics in BENCHMARKS.items():
        benchmark_return = metrics["return"]
        benchmark_volatility = metrics["volatility"]

        active_return = portfolio_return - benchmark_return
        tracking_error = abs(portfolio_volatility - benchmark_volatility)

        information_ratio = (
            active_return / tracking_error
            if tracking_error != 0
            else 0.0
        )

        beta_proxy = (
            portfolio_volatility / benchmark_volatility
            if benchmark_volatility != 0
            else 0.0
        )

        alpha_proxy = portfolio_return - beta_proxy * benchmark_return

        rows.append(
            {
                "benchmark": benchmark,
                "portfolio_return": portfolio_return,
                "benchmark_return": benchmark_return,
                "active_return": active_return,
                "portfolio_volatility": portfolio_volatility,
                "benchmark_volatility": benchmark_volatility,
                "tracking_error": tracking_error,
                "information_ratio": information_ratio,
                "beta_proxy": beta_proxy,
                "alpha_proxy": alpha_proxy,
                "status": "OUTPERFORM" if active_return > 0 else "UNDERPERFORM",
            }
        )

    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_PATH, index=False)

    best_relative = df.sort_values("active_return", ascending=False).iloc[0]

    summary = {
        "portfolio_return": portfolio_return,
        "benchmark_count": int(len(df)),
        "best_relative_benchmark": best_relative["benchmark"],
        "best_active_return": float(best_relative["active_return"]),
        "outperform_count": int((df["status"] == "OUTPERFORM").sum()),
        "underperform_count": int((df["status"] == "UNDERPERFORM").sum()),
    }

    SUMMARY_PATH.write_text(json.dumps(summary, indent=4), encoding="utf-8")

    return df


if __name__ == "__main__":
    print("=" * 80)
    print("AURUM BENCHMARK COMPARISON ENGINE")
    print("=" * 80)

    result = run_benchmark_comparison()

    print(result.to_string(index=False))
    print("\nSaved:")
    print(f"- {OUTPUT_PATH}")
    print(f"- {SUMMARY_PATH}")