from pathlib import Path
import json
import pandas as pd


REQUIRED_FILES = [
    "data/features/macro_features.parquet",
    "data/regimes/hidden_markov_regimes.csv",
    "data/regimes/hidden_markov_filtered_probabilities.csv",
    "data/regimes/hidden_markov_smoothed_probabilities.csv",
    "data/regimes/hidden_markov_transition_matrix.csv",
    "data/regimes/bayesian_regime_probabilities.csv",
    "data/regimes/calibrated_regime_probabilities.csv",
    "data/risk/tail_risk_report.csv",
    "data/risk/asset_tail_risk_report.csv",
    "data/risk/tail_dependence_report.csv",
    "data/risk/dynamic_hedging_policy.csv",
    "data/risk/correlation_breakdown_report.csv",
    "data/signals/cross_sectional_alpha_signals.csv",
    "data/forecasting/ensemble_forecast_signals.csv",
    "data/forecasting/signal_decay_summary.csv",
    "data/validation/alpha_validation_report.csv",
    "data/validation/walk_forward_report.csv",
    "data/validation/transaction_cost_summary.csv",
    "data/institutional/portfolio_weights.csv",
    "data/institutional/portfolio_backtest_summary.csv",
    "data/research/experiment_registry.csv",
    "results/research/institutional_quant_research_report.txt",
    "data/infrastructure/research_pipeline_run_log.json",
]


def pass_check(message, detail=None):
    print(f"[PASS] {message}")
    if detail is not None:
        print(f"       {detail}")


def fail_check(message, detail=None):
    print(f"[FAIL] {message}")
    if detail is not None:
        print(f"       {detail}")


def validate_file_exists(path):
    file_path = Path(path)

    if file_path.exists():
        pass_check(f"{path} exists")
        return True

    fail_check(f"{path} missing")
    return False


def validate_nonempty_table(path):
    file_path = Path(path)

    if not file_path.exists():
        fail_check(f"{path} missing")
        return False

    try:
        if file_path.suffix == ".parquet":
            df = pd.read_parquet(file_path)
        else:
            df = pd.read_csv(file_path)

        if len(df) == 0:
            fail_check(f"{path} has zero rows")
            return False

        pass_check(f"{path} non-empty", f"rows={len(df)}, cols={len(df.columns)}")
        return True

    except Exception as exc:
        fail_check(f"{path} could not be read", str(exc))
        return False


def validate_pipeline_log():
    path = Path("data/infrastructure/research_pipeline_run_log.json")

    if not path.exists():
        fail_check("pipeline run log missing")
        return False

    try:
        with open(path, "r", encoding="utf-8") as file:
            log = json.load(file)

        status = log.get("overall_status")
        steps = log.get("steps", [])

        if status != "PASS":
            fail_check("pipeline status is not PASS", status)
            return False

        failed_steps = [
            step for step in steps
            if step.get("status") != "PASS"
        ]

        if failed_steps:
            fail_check("pipeline has failed steps", failed_steps)
            return False

        pass_check(
            "pipeline completed successfully",
            f"steps={len(steps)}, runtime={log.get('total_runtime_seconds')}s",
        )
        return True

    except Exception as exc:
        fail_check("pipeline log could not be validated", str(exc))
        return False


def validate_portfolio_weight_safety():
    path = Path("data/institutional/portfolio_weights.csv")

    if not path.exists():
        fail_check("portfolio weights missing")
        return False

    df = pd.read_csv(path)

    required_cols = {"Date", "asset", "final_weight"}

    if not required_cols.issubset(df.columns):
        fail_check("portfolio weights missing required columns")
        return False

    grouped = df.groupby("Date")["final_weight"].sum()
    max_deviation = (grouped - 1.0).abs().max()

    if max_deviation > 1e-6:
        fail_check(
            "daily portfolio weights do not sum to 1",
            f"max_deviation={max_deviation}",
        )
        return False

    single_asset_violations = df[
        (~df["asset"].isin(["CASH", "BTC-USD", "ETH-USD", "VIX"]))
        & (df["final_weight"] > 0.350001)
    ]

    crypto_violations = df[
        (df["asset"].isin(["BTC-USD", "ETH-USD"]))
        & (df["final_weight"] > 0.040001)
    ]

    vix_violations = df[
        (df["asset"] == "VIX")
        & (df["final_weight"] > 0.050001)
    ]

    cash_violations = df[
        (df["asset"] == "CASH")
        & (df["final_weight"] > 1.000001)
    ]

    if not single_asset_violations.empty:
        fail_check("single asset cap violation detected")
        return False

    if not crypto_violations.empty:
        fail_check("crypto cap violation detected")
        return False

    if not vix_violations.empty:
        fail_check("VIX cap violation detected")
        return False

    if not cash_violations.empty:
        fail_check("cash cap violation detected")
        return False

    pass_check(
        "portfolio weights are institutionally safe",
        f"dates={grouped.shape[0]}, max_sum_deviation={max_deviation}",
    )
    return True


def validate_report_text():
    path = Path("results/research/institutional_quant_research_report.txt")

    if not path.exists():
        fail_check("institutional research report missing")
        return False

    text = path.read_text(encoding="utf-8")

    required_sections = [
        "EXECUTIVE SUMMARY",
        "WALK-FORWARD VALIDATION",
        "TAIL RISK ANALYTICS",
        "DYNAMIC HEDGING SYSTEM",
        "ALPHA RESEARCH",
        "TRANSACTION COST ANALYSIS",
        "INSTITUTIONAL PORTFOLIO BACKTEST",
        "DEPLOYABILITY ASSESSMENT",
    ]

    missing_sections = [
        section for section in required_sections
        if section not in text
    ]

    if missing_sections:
        fail_check("research report missing sections", missing_sections)
        return False

    pass_check("institutional research report contains required sections")
    return True


def main():
    print("\nAURUM QUANT RESEARCH PHASE 2 VALIDATION")
    print("=" * 80)

    results = []

    for path in REQUIRED_FILES:
        results.append(validate_file_exists(path))

    print("\nTABLE CONTENT VALIDATION")
    print("=" * 80)

    table_files = [
        path for path in REQUIRED_FILES
        if path.endswith(".csv") or path.endswith(".parquet")
    ]

    for path in table_files:
        results.append(validate_nonempty_table(path))

    print("\nPIPELINE VALIDATION")
    print("=" * 80)
    results.append(validate_pipeline_log())

    print("\nPORTFOLIO SAFETY VALIDATION")
    print("=" * 80)
    results.append(validate_portfolio_weight_safety())

    print("\nREPORT VALIDATION")
    print("=" * 80)
    results.append(validate_report_text())

    print("\nFINAL RESULT")
    print("=" * 80)

    passed = sum(results)
    total = len(results)

    if all(results):
        print(f"[PASS] Quant Research Phase 2 validation complete: {passed}/{total}")
        print("       Status: READY TO FREEZE QUANT RESEARCH CHAT 2")
    else:
        print(f"[FAIL] Quant Research Phase 2 validation incomplete: {passed}/{total}")
        print("       Fix failing checks before freezing this phase.")


if __name__ == "__main__":
    main()