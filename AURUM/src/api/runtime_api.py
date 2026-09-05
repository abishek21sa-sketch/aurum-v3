# src/api/runtime_api.py

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from src.api.rate_limiter import limiter
from src.api.runtime_models import (
    DriftResponse,
    GovernanceResponse,
    HealthResponse,
    HeartbeatResponse,
)
from src.config.config_loader import load_config
from src.logging.runtime_logger import get_logger
from src.cache.cache_manager import CacheManager


config = load_config()
logger = get_logger("api.runtime")


RUNTIME_DIR = Path(config["runtime"]["output_dir"])
STATE_DIR = RUNTIME_DIR / "state"

MANIFEST_PATH = RUNTIME_DIR / "runtime_manifest.json"
GOVERNANCE_PATH = RUNTIME_DIR / "runtime_governance_decision.json"
DRIFT_PATH = RUNTIME_DIR / "runtime_drift_report.json"
HEARTBEAT_PATH = RUNTIME_DIR / "runtime_heartbeat.json"
LATEST_STATE_PATH = STATE_DIR / "latest_runtime_state.json"
HEARTBEAT_CACHE_KEY = "aurum:runtime:heartbeat"

app = FastAPI(title="AURUM Runtime API", version="1.0.0")

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    logger.warning("Rate limit exceeded | client=%s | path=%s", request.client.host, request.url.path)

    raise HTTPException(
        status_code=429,
        detail="Rate limit exceeded. Please retry later.",
    )


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        logger.error("Requested runtime artifact missing: %s", path)
        raise HTTPException(
            status_code=404,
            detail=f"Runtime artifact not found: {path}",
        )

    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/health", response_model=HealthResponse)
@limiter.limit("60/minute")
async def health(request: Request) -> HealthResponse:
    logger.info("Health endpoint requested.")

    return HealthResponse(
        status="ok",
        service="AURUM Runtime API",
        environment=config["environment"],
        runtime_dir=str(RUNTIME_DIR),
    )


@app.get("/runtime/manifest")
@limiter.limit("20/minute")
async def get_manifest(request: Request) -> dict[str, Any]:
    logger.info("Runtime manifest endpoint requested.")
    return read_json(MANIFEST_PATH)


@app.get("/runtime/governance", response_model=GovernanceResponse)
@limiter.limit("30/minute")
async def get_governance(request: Request) -> GovernanceResponse:
    logger.info("Runtime governance endpoint requested.")
    return GovernanceResponse(**read_json(GOVERNANCE_PATH))


@app.get("/runtime/drift", response_model=DriftResponse)
@limiter.limit("30/minute")
async def get_drift(request: Request) -> DriftResponse:
    logger.info("Runtime drift endpoint requested.")
    return DriftResponse(**read_json(DRIFT_PATH))


@app.get("/runtime/heartbeat", response_model=HeartbeatResponse)
@limiter.limit("60/minute")
async def get_heartbeat(request: Request) -> HeartbeatResponse:
    logger.info("Runtime heartbeat endpoint requested.")

    cache = CacheManager()
    cached_heartbeat = cache.get(HEARTBEAT_CACHE_KEY)

    if cached_heartbeat is not None:
        logger.info(
            "Returning heartbeat from cache | backend=%s",
            cache.backend_name,
        )
        return HeartbeatResponse(**cached_heartbeat)

    logger.info("Heartbeat cache miss. Falling back to file.")
    return HeartbeatResponse(**read_json(HEARTBEAT_PATH))


@app.get("/runtime/latest-state")
@limiter.limit("20/minute")
async def get_latest_state(request: Request) -> dict[str, Any]:
    logger.info("Latest runtime state endpoint requested.")
    return read_json(LATEST_STATE_PATH)