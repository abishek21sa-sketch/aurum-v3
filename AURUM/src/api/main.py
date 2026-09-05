from pathlib import Path

from fastapi import FastAPI, Query

from src.institutional.mars_cvar_product import build_reference_product_evidence
from src.institutional.mars_cvar_reference import build_reference_mars_decision
from src.institutional.enterprise_readiness import (
    build_audit_lineage,
    build_evidence_bundle,
    build_enterprise_readiness,
    build_observability_snapshot,
    build_role_policy,
)
from src.institutional.deployment_preflight import build_deployment_preflight

from src.api.routes_market import router as market_router
from src.api.routes_anomalies import router as anomalies_router


app = FastAPI(
    title="AURUM Market Intelligence API",
    version="0.3.0",
    description="Live market intelligence, anomaly alerts, and portfolio regime outputs.",
)

app.include_router(market_router)
app.include_router(anomalies_router)


@app.get("/")
def root():
    return {
        "service": "AURUM Market Intelligence API",
        "status": "running",
        "version": "0.3.0",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "market-intelligence-api",
    }

@app.get("/v1/mars-cvar/reference", tags=["MARS-CVaR"])
def mars_cvar_reference():
    return build_reference_mars_decision()

@app.post("/v1/mars-cvar/decision", tags=["MARS-CVaR"])
def mars_cvar_decision(
    stress_probability: float = Query(default=.50, ge=0.0, le=1.0),
    turnover_penalty: float = Query(default=.05, ge=0.0, le=1.0),
):
    return build_reference_mars_decision(stress_probability=stress_probability, turnover_penalty=turnover_penalty)


@app.get("/v1/mars-cvar/evidence", tags=["MARS-CVaR"])
def mars_cvar_evidence(
    stress_probability: float = Query(default=.50, ge=0.0, le=1.0),
    turnover_penalty: float = Query(default=.05, ge=0.0, le=1.0),
    risk_aversion: float = Query(default=.35, ge=0.0, le=3.0),
    alpha: float = Query(default=.95, gt=0.0, lt=1.0),
):
    """Return the institutional workstation evidence payload."""
    return build_reference_product_evidence(
        Path(__file__).resolve().parents[2],
        stress_probability=stress_probability,
        turnover_penalty=turnover_penalty,
        risk_aversion=risk_aversion,
        alpha=alpha,
    )


@app.get("/v1/platform/readiness", tags=["Platform controls"])
def platform_readiness():
    """Return the machine-readable enterprise control-plane contract."""
    root = Path(__file__).resolve().parents[2]
    evidence = build_reference_product_evidence(root)
    return build_enterprise_readiness(root, evidence)


@app.get("/v1/platform/observability", tags=["Platform controls"])
def platform_observability():
    """Return low-cardinality operational health signals without secrets."""
    root = Path(__file__).resolve().parents[2]
    evidence = build_reference_product_evidence(root)
    readiness = build_enterprise_readiness(root, evidence)
    return build_observability_snapshot(root, readiness)


@app.get("/v1/platform/deployment-preflight", tags=["Platform controls"])
def platform_deployment_preflight():
    """Return deployment controls while preserving the research-only boundary."""
    root = Path(__file__).resolve().parents[2]
    return build_deployment_preflight(root)


@app.get("/v1/platform/role-policy", tags=["Platform controls"])
def platform_role_policy():
    """Return the declarative role/capability contract for deployment IAM."""
    return build_role_policy()


@app.get("/v1/platform/audit/lineage", tags=["Platform controls"])
def platform_audit_lineage():
    """Return the tamper-evident hash-linked lineage for the current evidence."""
    root = Path(__file__).resolve().parents[2]
    evidence = build_reference_product_evidence(root)
    readiness = build_enterprise_readiness(root, evidence)
    return readiness["audit_lineage"]


@app.get("/v1/platform/evidence-bundle", tags=["Platform controls"])
def platform_evidence_bundle():
    """Return a portable evidence bundle without persisting or executing anything."""
    root = Path(__file__).resolve().parents[2]
    evidence = build_reference_product_evidence(root)
    readiness = build_enterprise_readiness(root, evidence)
    return build_evidence_bundle(root, evidence, readiness)
