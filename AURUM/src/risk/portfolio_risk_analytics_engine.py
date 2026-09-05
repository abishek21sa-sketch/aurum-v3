from pathlib import Path
import pandas as pd
import numpy as np


INPUT_PATH = Path("data/institutional/portfolio_backtest_results.csv")
OUTPUT_DIR = Path("results/risk")
OUTPUT_PATH = OUTPUT_DIR / "portfolio_risk_report.csv"
ROLLING_DRAWDOWN_PATH = OUTPUT_DIR / "rolling_drawdown_report.csv"
SPY_PATH = Path("data/market_matrix/market_return_matrix.csv")

TRADING_DAYS = 252

ASSET_BETA_MAP = {
    "SPY": 1.00,
    "QQQ": 1.20,
    "DIA": 0.90,
    "TLT": -0.20,
    "GLD": 0.00,
    "BTC-USD": 1.50,
    "ETH-USD": 1.70,
    "VIX": -3.00,
    "CASH": 0.00,
}

WEIGHTS_PATH = Path("data/institutional/portfolio_weights.csv")

def calculate_exposure_implied_beta() -> float:
    if not WEIGHTS_PATH.exists():
        raise FileNotFoundError(f"Missing weights file: {WEIGHTS_PATH}")

    weights = pd.read_csv(WEIGHTS_PATH)
    weights["Date"] = pd.to_datetime(weights["Date"])

    latest_date = weights["Date"].max()
    latest = weights[weights["Date"] == latest_date].copy()

    latest["asset_beta"] = latest["asset"].map(ASSET_BETA_MAP).fillna(0.0)

    implied_beta = (
        latest["final_weight"] * latest["asset_beta"]
    ).sum()

    return implied_beta

def annualized_volatility(returns: pd.Series) -> float:
    return returns.std() * np.sqrt(TRADING_DAYS)


def downside_deviation(returns: pd.Series) -> float:
    downside = returns[returns < 0]
    if downside.empty:
        return 0.0
    return downside.std() * np.sqrt(TRADING_DAYS)


def max_drawdown(equity_curve: pd.Series) -> float:
    running_peak = equity_curve.cummax()
    drawdown = equity_curve / running_peak - 1
    return drawdown.min()


def calculate_beta(portfolio_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    aligned = pd.concat([portfolio_returns, benchmark_returns], axis=1).dropna()
    aligned.columns = ["portfolio", "benchmark"]

    if len(aligned) < 2:
        return np.nan

    benchmark_variance = aligned["benchmark"].var()
    if benchmark_variance == 0:
        return np.nan

    covariance = aligned["portfolio"].cov(aligned["benchmark"])
    return covariance / benchmark_variance

def load_spy_returns() -> pd.DataFrame:
    if not SPY_PATH.exists():
        raise FileNotFoundError(f"Missing SPY benchmark file: {SPY_PATH}")

    market = pd.read_csv(SPY_PATH)
    market["Date"] = pd.to_datetime(market["Date"])

    if "SPY" not in market.columns:
        raise ValueError(
            f"SPY column not found in {SPY_PATH}. "
            f"Available columns: {list(market.columns)}"
        )

    return market[["Date", "SPY"]].rename(columns={"SPY": "spy_return"})

def build_risk_report() -> pd.DataFrame:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Missing input file: {INPUT_PATH}")

    df = pd.read_csv(INPUT_PATH)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date")

    required_columns = [
        "gross_portfolio_return",
        "net_portfolio_return",
        "gross_equity_curve",
        "net_equity_curve",
        "gross_drawdown",
        "net_drawdown",
    ]

    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    gross_returns = df["gross_portfolio_return"].fillna(0.0)
    net_returns = df["net_portfolio_return"].fillna(0.0)

    # Temporary benchmark fallback:
    # Until we wire SPY benchmark returns directly, use gross portfolio return
    # as internal benchmark proxy for beta sanity checking.
    spy_returns = load_spy_returns()

    merged_beta = df[["Date", "net_portfolio_return"]].merge(
        spy_returns,
        on="Date",
        how="inner",
    )

    print(f"Merged observations: {len(merged_beta)}")
    print(
        f"Portfolio observations: {len(df)}, "
        f"SPY observations: {len(spy_returns)}"
    )

    portfolio_beta_vs_spy = calculate_beta(
        merged_beta["net_portfolio_return"],
        merged_beta["spy_return"],
    )

    exposure_implied_beta = calculate_exposure_implied_beta()

    metrics = [
        {
            "metric": "annualized_volatility_gross",
            "value": annualized_volatility(gross_returns),
            "description": "Annualized volatility before transaction costs.",
        },
        {
            "metric": "annualized_volatility_net",
            "value": annualized_volatility(net_returns),
            "description": "Annualized volatility after transaction costs.",
        },
        {
            "metric": "downside_deviation_gross",
            "value": downside_deviation(gross_returns),
            "description": "Annualized downside deviation before transaction costs.",
        },
        {
            "metric": "downside_deviation_net",
            "value": downside_deviation(net_returns),
            "description": "Annualized downside deviation after transaction costs.",
        },
        {
            "metric": "max_drawdown_gross",
            "value": max_drawdown(df["gross_equity_curve"]),
            "description": "Maximum peak-to-trough loss before transaction costs.",
        },
        {
            "metric": "max_drawdown_net",
            "value": max_drawdown(df["net_equity_curve"]),
            "description": "Maximum peak-to-trough loss after transaction costs.",
        },
        {
            "metric": "portfolio_beta_vs_spy",
            "value": portfolio_beta_vs_spy,
            "description": "Historical beta from sparse institutional backtest returns; may be distorted by zero-return carry days.",
        },
        {
            "metric": "exposure_implied_beta_vs_spy",
            "value": exposure_implied_beta,
            "description": "Estimated beta from latest portfolio weights and asset beta assumptions.",
        },
        {
            "metric": "average_gross_exposure",
            "value": df["gross_exposure"].mean() if "gross_exposure" in df.columns else np.nan,
            "description": "Average gross portfolio exposure.",
        },
        {
            "metric": "average_cash_weight",
            "value": df["cash_weight"].mean() if "cash_weight" in df.columns else np.nan,
            "description": "Average portfolio cash allocation.",
        },
        {
            "metric": "average_turnover",
            "value": df["portfolio_turnover"].mean() if "portfolio_turnover" in df.columns else np.nan,
            "description": "Average portfolio turnover.",
        },
    ]

    report = pd.DataFrame(metrics)

    rolling = df[["Date", "gross_drawdown", "net_drawdown"]].copy()
    rolling.columns = ["date", "gross_rolling_drawdown", "net_rolling_drawdown"]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report.to_csv(OUTPUT_PATH, index=False)
    rolling.to_csv(ROLLING_DRAWDOWN_PATH, index=False)

    return report


def main():
    print("=" * 80)
    print("AURUM PORTFOLIO RISK ANALYTICS ENGINE")
    print("=" * 80)

    report = build_risk_report()

    print("\nPORTFOLIO RISK REPORT")
    print("-" * 80)
    print(report.to_string(index=False))

    print(f"\nSaved risk report to: {OUTPUT_PATH}")
    print(f"Saved rolling drawdown report to: {ROLLING_DRAWDOWN_PATH}")
    print("\nPORTFOLIO RISK ANALYTICS COMPLETE")


if __name__ == "__main__":
    main()