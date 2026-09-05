from pathlib import Path
import json

from src.memory.portfolio_memory_engine import (
    run_portfolio_memory_engine,
)

print("=" * 80)
print(
    "AURUM MEMORY LAYER VALIDATION"
)
print("=" * 80)

result = (
    run_portfolio_memory_engine()
)

memory_path = Path(
    "results/memory/portfolio_memory.jsonl"
)

summary_path = Path(
    "results/memory/memory_summary.json"
)

assert memory_path.exists()
assert summary_path.exists()

summary = json.loads(
    summary_path.read_text(
        encoding="utf-8"
    )
)

assert (
    summary["total_cycles"] >= 1
)

print(
    f"[PASS] total_cycles = "
    f"{summary['total_cycles']}"
)

print(
    f"[PASS] approved = "
    f"{summary['approved']}"
)

print(
    f"[PASS] escalated = "
    f"{summary['escalated']}"
)

print(
    f"[PASS] rejected = "
    f"{summary['rejected']}"
)

print("=" * 80)
print(
    "[PASS] PHASE 4E.5 MEMORY LAYER"
)
print("=" * 80)