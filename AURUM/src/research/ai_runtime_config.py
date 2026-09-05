from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


CONFIG_PATH = Path("config/ai_settings.json")


DEFAULT_CONFIG: Dict[str, Any] = {
    "ai_enabled": True,
    "fallback_to_cached_artifacts": True,
    "fallback_to_rules": True,
    "max_llm_calls_per_run": 20,
    "default_model": "gpt-4o-mini",
    "low_cost_model": "gpt-4o-mini",
    "phase5b": {
        "enabled": True,
        "use_cached_on_quota_error": True,
        "portfolio_manager_mode": "deterministic",
        "max_agent_count": 5,
        "run_rebuttals": True,
        "run_votes": True,
    },
    "phase5c": {
        "enabled": True,
        "use_llm": False,
    },
}


def load_ai_settings() -> Dict[str, Any]:
    if not CONFIG_PATH.exists():
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with CONFIG_PATH.open("w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
        return DEFAULT_CONFIG

    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        user_config = json.load(f)

    merged = DEFAULT_CONFIG.copy()
    merged.update(user_config)

    for key in ["phase5b", "phase5c"]:
        merged[key] = DEFAULT_CONFIG[key] | user_config.get(key, {})

    return merged


class LLMCallBudget:
    def __init__(self, max_calls: int):
        self.max_calls = max_calls
        self.calls_used = 0

    def consume(self) -> None:
        if self.calls_used >= self.max_calls:
            raise RuntimeError(
                f"LLM call budget exceeded: {self.calls_used}/{self.max_calls}"
            )
        self.calls_used += 1