from pathlib import Path
from src.ai.memory import load_memory

def read_text_report(report_path: str) -> str:
    path = Path(report_path)

    if not path.exists():
        raise FileNotFoundError(f"Report not found: {report_path}")

    return path.read_text(encoding="utf-8")


def format_portfolio_context(report_text: str) -> str:
    return f"""
AURUM Portfolio Report:

{report_text}
"""

def format_memory_context() -> str:
    memory = load_memory()

    if not memory:
        return "No prior AI memory available."

    return f"""
AURUM AI Memory:

Latest Market Regime:
{memory.get("latest_market_regime", "unknown")}

Latest Risk Signal:
{memory.get("latest_risk_signal", "unknown")}

Last Market Analysis Time:
{memory.get("last_market_signal_analysis_time", "unknown")}

Latest Market Analysis:
{memory.get("latest_market_analysis", "unknown")}
"""
