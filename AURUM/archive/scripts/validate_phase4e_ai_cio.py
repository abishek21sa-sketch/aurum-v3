from pathlib import Path
import json

from src.ai.ai_cio_copilot import (
    run_ai_cio_copilot,
)

print("=" * 80)
print(
    "AURUM AI CIO VALIDATION"
)
print("=" * 80)

brief = run_ai_cio_copilot()

assert "market_view" in brief
assert "recommended_action" in brief

json_path = Path(
    "results/ai/cio_daily_brief.json"
)

txt_path = Path(
    "results/ai/cio_daily_brief.txt"
)

assert json_path.exists()
assert txt_path.exists()

saved = json.loads(
    json_path.read_text(
        encoding="utf-8"
    )
)

print(
    f"[PASS] cycles = "
    f"{saved['historical_cycles']}"
)

print(
    f"[PASS] action = "
    f"{saved['recommended_action']}"
)

print("=" * 80)
print(
    "[PASS] PHASE 4E.6 AI CIO COPILOT"
)
print("=" * 80)