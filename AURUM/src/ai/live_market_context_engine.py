from pathlib import Path
import json
import re


REPORT_PATHS = {
    "market_signal": Path("results/reports/market_signal_report.txt"),
    "live_allocation": Path("results/reports/live_allocation_recommendation.txt"),
    "scenario_shock": Path("results/risk/live_scenario_shock_report.txt"),
    "executive_summary": Path("results/reports/aurum_executive_strategy_summary.txt"),
    "confidence_memory": Path("results/ai/aurum_session_memory.json"),
}


def read_file(path: Path):
    if not path.exists():
        return None

    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")


def extract_value(pattern: str, text: str, default=None):
    if not text:
        return default

    match = re.search(pattern, text)

    if not match:
        return default

    return match.group(1).strip()


def load_memory_state():
    path = REPORT_PATHS["confidence_memory"]

    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_live_market_context():
    market_signal = read_file(REPORT_PATHS["market_signal"])
    live_allocation = read_file(REPORT_PATHS["live_allocation"])
    scenario_shock = read_file(REPORT_PATHS["scenario_shock"])
    executive_summary = read_file(REPORT_PATHS["executive_summary"])
    memory = load_memory_state()

    context = {
        "market_regime": extract_value(
            r"Latest Regime:\s*([A-Za-z_]+)",
            market_signal,
        ),
        "risk_signal": extract_value(
            r"Latest Risk Signal:\s*([A-Za-z_]+)",
            market_signal,
        ),
        "market_mean_return": extract_value(
            r"Latest Market Mean Return:\s*([-+]?\d+\.\d+)",
            market_signal,
        ),
        "market_volatility": extract_value(
            r"Latest Market Volatility:\s*([-+]?\d+\.\d+)",
            market_signal,
        ),
        "next_regime": extract_value(
            r"Most Likely Next Regime:\s*([A-Za-z_]+)",
            live_allocation,
        ),
        "next_regime_probability": extract_value(
            r"Most Likely Next Regime:\s*[A-Za-z_]+\s*\(([-+]?\d+\.\d+)% probability\)",
            live_allocation,
        ),
        "growth_risk_weight": extract_value(
            r"Growth / Risk Asset Weight:\s*([-+]?\d+\.\d+)%",
            live_allocation,
        ),
        "defensive_hedge_weight": extract_value(
            r"Defensive / Hedge Asset Weight:\s*([-+]?\d+\.\d+)%",
            live_allocation,
        ),
        "worst_live_scenario": extract_value(
            r"WORST LIVE SCENARIO.*?\n[-]+\n([a-zA-Z0-9_]+)",
            scenario_shock,
        ),
        "active_portfolio_stance": memory.get("active_portfolio_stance"),
        "active_risk_regime": memory.get("active_risk_regime"),
        "active_confidence_level": memory.get("active_confidence_level"),
    }

    return context


def format_live_market_context(context: dict):
    lines = []

    lines.append("=" * 90)
    lines.append("AURUM LIVE MARKET CONTEXT ENGINE")
    lines.append("=" * 90)

    lines.append("")
    lines.append("CURRENT MARKET STATE")
    lines.append("-" * 70)
    lines.append(f"Latest Regime: {context.get('market_regime')}")
    lines.append(f"Latest Risk Signal: {context.get('risk_signal')}")
    lines.append(f"Market Mean Return: {context.get('market_mean_return')}")
    lines.append(f"Market Volatility: {context.get('market_volatility')}")

    lines.append("")
    lines.append("FORWARD REGIME VIEW")
    lines.append("-" * 70)
    lines.append(f"Most Likely Next Regime: {context.get('next_regime')}")
    lines.append(f"Next Regime Probability: {context.get('next_regime_probability')}%")

    lines.append("")
    lines.append("LIVE ALLOCATION POSTURE")
    lines.append("-" * 70)
    lines.append(f"Growth / Risk Asset Weight: {context.get('growth_risk_weight')}%")
    lines.append(f"Defensive / Hedge Asset Weight: {context.get('defensive_hedge_weight')}%")

    lines.append("")
    lines.append("SESSION MEMORY STATE")
    lines.append("-" * 70)
    lines.append(f"Portfolio Stance: {context.get('active_portfolio_stance')}")
    lines.append(f"Risk Regime: {context.get('active_risk_regime')}")
    lines.append(f"Confidence Level: {context.get('active_confidence_level')}")

    return "\n".join(lines)


if __name__ == "__main__":
    context = build_live_market_context()
    print(format_live_market_context(context))