# MARS-CVaR Engine / Research-Orchestrator Boundary

AURUM V2 is the research-orchestration layer. The sibling `AURUM` repository is the quantitative portfolio/regime engine that owns MARS-CVaR optimization and evidence.

V2 may consume the governed MARS-CVaR decision artifact as **read-only research context**. It does not receive execution rights, does not replace the optimizer with LLM output, and must not promote a research result beyond the engine's evidence/promotion gate.

Deterministic bridge tests live in `tests/test_mars_cvar_engine_bridge.py`. Live PostgreSQL/FRED/Anthropic checks are preserved under `scripts/integration_checks/` and are deliberately outside deterministic pytest collection.
