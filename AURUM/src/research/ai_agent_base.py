from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict

from src.research.llm_client import AURUMLLMClient


class BaseAIResearchAgent(ABC):
    """
    Base class for true AI research agents.

    These are different from rule-based analytics agents.

    Rule Agent:
        computes signals

    AI Agent:
        reasons over those signals
    """

    ai_agent_name = "base_ai_research_agent"

    def __init__(self) -> None:
        self.generated_at = datetime.now(timezone.utc).isoformat()
        self.llm = AURUMLLMClient()

    @abstractmethod
    def source_agent_output(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def system_prompt(self) -> str:
        pass

    @abstractmethod
    def fallback_response(self, source_output: Dict[str, Any]) -> Dict[str, Any]:
        pass

    def run(self) -> Dict[str, Any]:
        source_output = self.source_agent_output()

        payload = {
            "ai_agent_name": self.ai_agent_name,
            "generated_at": self.generated_at,
            "source_agent_output": source_output,
            "required_output_schema": {
                "thesis": "string",
                "evidence": ["string"],
                "contradictions": ["string"],
                "risks": ["string"],
                "recommendation": "string",
                "confidence": "float between 0 and 1",
                "decision_rationale": "string",
            },
        }

        ai_output = self.llm.generate_json(
            system_prompt=self.system_prompt(),
            user_payload=payload,
            fallback=self.fallback_response(source_output),
        )

        return {
            "ai_agent_name": self.ai_agent_name,
            "generated_at": self.generated_at,
            "source_agent_output": source_output,
            "ai_analysis": ai_output,
        }