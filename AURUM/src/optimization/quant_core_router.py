from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict

import pandas as pd

from src.optimization.cvar_lp_optimizer import CVaRLPOptimizer


from src.config.storage_paths import artifact_path, ensure_storage_dirs

ensure_storage_dirs()


@dataclass
class QuantCoreRoutingResult:
    optimizer_engine: str
    cvar_method: str
    beta: float
    weights: Dict[str, float]
    status: str
    integration_status: str


class QuantCoreRouter:
    """
    Central router proving AURUM now points to the hardened CVaR LP optimizer.
    """

    def run_cvar_lp(self, returns: pd.DataFrame) -> QuantCoreRoutingResult:
        optimizer = CVaRLPOptimizer(
            returns=returns,
            beta=0.95,
            long_only=True,
            max_weight=0.35,
        )

        result = optimizer.optimize()

        routed = QuantCoreRoutingResult(
            optimizer_engine="CVaRLPOptimizer",
            cvar_method=result.method,
            beta=result.beta,
            weights=result.weights,
            status=result.status,
            integration_status="connected",
        )

        path = artifact_path("sprint1b", "quant_core_router_result.json")
        path.write_text(json.dumps(asdict(routed), indent=4), encoding="utf-8")

        return routed