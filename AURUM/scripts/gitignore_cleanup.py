from pathlib import Path
import shutil

# Fix .gitignore
gitignore = Path(".gitignore").read_text(encoding="utf-8")
additions = []
if "*.zip" not in gitignore:
    additions.append("*.zip")
if "temp_*.py" not in gitignore:
    additions.append("temp_*.py")
if ".pytest_cache" not in gitignore:
    additions.append(".pytest_cache/")
if "*.pyc" not in gitignore:
    additions.append("*.pyc")

if additions:
    gitignore += "\n" + "\n".join(additions) + "\n"
    Path(".gitignore").write_text(gitignore, encoding="utf-8")
    print("Added to .gitignore:", additions)
else:
    print(".gitignore already complete.")

# Delete temp files
for f in Path(".").glob("temp_*.py"):
    f.unlink()
    print(f"Deleted: {f.name}")

# Create .env.example
env_example = """# AURUM Environment Variables
# Copy this file to .env and fill in your keys

# Alpaca Paper Trading (free at alpaca.markets)
ALPACA_API_KEY=your_alpaca_key_here
ALPACA_SECRET_KEY=your_alpaca_secret_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Groq LLM (free at console.groq.com)
GROQ_API_KEY=your_groq_key_here

# OpenAI (optional - Groq is used by default)
OPENAI_API_KEY=your_openai_key_here

# Finnhub (optional)
FINNHUB_API_KEY=your_finnhub_key_here

# Database (optional - system runs without these)
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
POSTGRES_DB=aurum
POSTGRES_USER=aurum
POSTGRES_PASSWORD=aurum

# Redis (optional)
REDIS_HOST=localhost
REDIS_PORT=6379
"""
Path(".env.example").write_text(env_example, encoding="utf-8")
print("Created: .env.example")

# Move old validate scripts to archive
scripts_dir = Path("scripts")
archive_dir = Path("archive/scripts")
archive_dir.mkdir(parents=True, exist_ok=True)

keep = {
    "write_readme.py", "fix_runner.py", "write_copilot.py",
    "fix_copilot_display.py", "fix_dashboard_syntax.py",
    "fix_env_loading.py", "add_equity_chart.py",
    "add_alpaca_positions.py", "remove_old_copilot.py",
    "gitignore_cleanup.py", "__init__.py"
}

moved = 0
for f in scripts_dir.glob("*.py"):
    if f.name not in keep:
        shutil.move(str(f), str(archive_dir / f.name))
        moved += 1

print(f"Moved {moved} old scripts to archive/scripts/")
print("Done.")