from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List


class BaseResearchAgent(ABC):
    """
    Base class for all AURUM AI Research Desk agents.

    Every research agent must:
    1. observe()
    2. analyze()
    3. recommend()
    4. explain()
    """

    agent_name: str = "base_agent"

    def __init__(self) -> None:
        self.generated_at = datetime.now(timezone.utc).isoformat()
        self.observations: Dict[str, Any] = {}
        self.analysis: Dict[str, Any] = {}
        self.recommendations: List[str] = []
        self.explanation: str = ""

    @abstractmethod
    def observe(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def analyze(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def recommend(self) -> List[str]:
        pass

    @abstractmethod
    def explain(self) -> str:
        pass

    def run(self) -> Dict[str, Any]:
        self.observations = self.observe()
        self.analysis = self.analyze()
        self.recommendations = self.recommend()
        self.explanation = self.explain()

        return {
            "agent_name": self.agent_name,
            "generated_at": self.generated_at,
            "observations": self.observations,
            "analysis": self.analysis,
            "recommendations": self.recommendations,
            "explanation": self.explanation,
        }