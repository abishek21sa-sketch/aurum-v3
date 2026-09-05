from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, List


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ResearchExperiment:
    experiment_id: str
    hypothesis_id: str
    theme: str
    research_design: str
    status: str
    score: float
    decision: str
    lesson: str


class ResearchLoopState:
    def __init__(self) -> None:
        self.timestamp = utc_now()
        self.stage = "initialized"
        self.experiments: List[ResearchExperiment] = []

    def add_experiment(self, experiment: ResearchExperiment) -> None:
        self.experiments.append(experiment)

    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "stage": self.stage,
            "experiment_count": len(self.experiments),
            "experiments": [asdict(exp) for exp in self.experiments],
        }