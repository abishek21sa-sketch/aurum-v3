from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional


class AURUMLLMClient:
    """
    LLM client for true AI research agents.

    Uses OpenAI Responses API when OPENAI_API_KEY exists.
    Falls back safely when no key is configured.
    """

    def __init__(self, model: Optional[str] = None) -> None:
        self.model = model or os.getenv("AURUM_LLM_MODEL", "gpt-4o-mini")
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.enabled = bool(self.api_key)

    def generate_json(
        self,
        system_prompt: str,
        user_payload: Dict[str, Any],
        fallback: Dict[str, Any],
    ) -> Dict[str, Any]:
        if not self.enabled:
            fallback["llm_mode"] = "fallback_no_api_key"
            return fallback

        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key)

            response = client.responses.create(
                model=self.model,
                instructions=system_prompt,
                input=(
                    "Return ONLY valid JSON. Do not include markdown.\n\n"
                    + json.dumps(user_payload, indent=2, default=str)
                ),
            )

            text = response.output_text.strip()

            parsed = json.loads(text)
            parsed["llm_mode"] = "openai_responses_api"
            parsed["llm_model"] = self.model

            return parsed

        except Exception as exc:
            fallback["llm_mode"] = "fallback_llm_error"
            fallback["llm_error"] = str(exc)
            return fallback