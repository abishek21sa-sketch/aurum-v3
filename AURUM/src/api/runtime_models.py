# src/api/runtime_models.py

from typing import Any

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str
    runtime_dir: str


class GovernanceMetrics(BaseModel):
    pass_rate: float
    failed_modules: int
    stderr_modules: int
    failed_checkpoints: int


class GovernanceResponse(BaseModel):
    decision: str
    severity: str
    approved: bool
    action: str
    conditions: dict[str, bool]
    metrics: GovernanceMetrics


class DriftResponse(BaseModel):
    drift_detected: bool
    severity: str
    previous_state: dict[str, Any]
    current_state: dict[str, Any]
    drift_signals: dict[str, bool]


class HeartbeatResponse(BaseModel):
    heartbeat_timestamp_utc: str
    status: str
    environment: str
    runtime_directory: str
    last_governance_decision: str
    last_governance_severity: str
    approved: bool
    runtime_stable: bool
    pass_rate: float
    failed_modules: int | None
    total_runtime_seconds: float | None
    drift_detected: bool | None
    drift_status: str