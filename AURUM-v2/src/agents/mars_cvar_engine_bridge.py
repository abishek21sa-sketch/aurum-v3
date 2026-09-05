from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def default_mars_decision_path() -> Path:
    configured = os.getenv("AURUM_MARS_DECISION_PATH")
    if configured:
        return Path(configured)
    # AURUM V2 and the quantitative engine are sibling repositories in the
    # portfolio distribution. V2 consumes the engine artifact read-only.
    return Path(__file__).resolve().parents[3] / "AURUM" / "results" / "institutional" / "mars_cvar_decision.json"


def load_mars_cvar_context(path: str | Path | None = None) -> dict[str, Any]:
    decision_path = Path(path) if path is not None else default_mars_decision_path()
    if not decision_path.exists():
        return {
            "available": False,
            "source": str(decision_path),
            "reason": "MARS-CVaR engine decision artifact not found",
            "execution_authorized": False,
        }

    payload = json.loads(decision_path.read_text(encoding="utf-8"))
    required = {"algorithm", "status", "decision_id", "target_weights", "risk_gate", "claim_boundary"}
    missing = sorted(required - set(payload))
    if missing:
        return {
            "available": False,
            "source": str(decision_path),
            "reason": f"MARS-CVaR artifact missing fields: {missing}",
            "execution_authorized": False,
        }

    governed = (
        payload.get("algorithm") == "MARS-CVaR"
        and payload.get("status") == "OPTIMAL"
        and payload.get("risk_gate") == "AUTHORIZED"
    )
    return {
        "available": True,
        "source": str(decision_path),
        "decision_id": payload["decision_id"],
        "governed": governed,
        "risk_gate": payload.get("risk_gate"),
        "expected_return": payload.get("expected_return"),
        "cvar_loss": payload.get("cvar_loss"),
        "turnover": payload.get("turnover"),
        "target_weights": payload.get("target_weights", {}),
        "regime_probabilities": payload.get("regime_probabilities", {}),
        "claim_boundary": payload.get("claim_boundary"),
        # Deliberately false: V2 may reason over this context, never execute it.
        "execution_authorized": False,
        "usage_boundary": (
            "Read-only research context from the AURUM quantitative engine. "
            "AURUM V2 cannot execute or promote portfolio trades from this bridge."
        ),
    }
