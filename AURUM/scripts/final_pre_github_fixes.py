from pathlib import Path

# Fix 1: Update README to say Groq not GPT-4o-mini
readme = Path("README.md").read_text(encoding="utf-8")
readme = readme.replace("GPT-4o-mini", "Groq Llama 3.3 70B (free)")
readme = readme.replace("OpenAI GPT-4o-mini, multi-agent committee architecture",
                        "Groq Llama 3.3 70B (free), multi-agent committee architecture")
Path("README.md").write_text(readme, encoding="utf-8")
print("Fixed README: GPT-4o-mini → Groq Llama 3.3 70B")

# Fix 2: Add results/ to .gitignore but keep backtest
gitignore = Path(".gitignore").read_text(encoding="utf-8")
additions = """
# Results - keep backtest, exclude live state files
results/mission_control/
results/execution/
results/cio/
results/portfolio_os/
results/optimization/
results/simulation/
results/realtime/
results/regimes/
results/risk/
results/research/
results/research_firm/
results/institutional/
results/alpha/
results/monitoring/
results/reporting/
results/reliability/
# Keep these
!results/backtest/
!results/backtest/**
"""
if "results/mission_control/" not in gitignore:
    gitignore += additions
    Path(".gitignore").write_text(gitignore, encoding="utf-8")
    print("Fixed .gitignore: results/ folders excluded")
else:
    print(".gitignore already has results/ rules")

# Fix 3: Create missing __init__.py
init = Path("src/backtest/__init__.py")
if not init.exists():
    init.write_text('"""AURUM Backtest Engine"""\n', encoding="utf-8")
    print("Created src/backtest/__init__.py")
else:
    print("src/backtest/__init__.py already exists")

# Fix 4: Add Finnhub to README tech stack
readme = Path("README.md").read_text(encoding="utf-8")
if "Finnhub" not in readme:
    readme = readme.replace(
        "- Data: yfinance, Alpaca Markets API, Polygon, FRED",
        "- Data: yfinance, Finnhub (real-time), Alpaca Markets API, Redis Streams"
    )
    Path("README.md").write_text(readme, encoding="utf-8")
    print("Fixed README: added Finnhub to tech stack")

print("\nAll pre-GitHub fixes done.")