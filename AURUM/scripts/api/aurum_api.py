from pathlib import Path

import pandas as pd
from fastapi import FastAPI
from fastapi.responses import JSONResponse


app = FastAPI(
    title="AURUM Institutional Quant API",
    version="1.0",
)


BASE_PATHS = {
    "meta_strategy":
        Path("data/backtesting/meta_strategy_backtest_summary.csv"),

    "factor_exposures":
        Path("data/analytics/factor_attribution_v2.csv"),

    "walk_forward":
        Path("data/validation/walk_forward_meta_validation_summary.csv"),

    "risk_monitor":
        Path("results/live/daily_risk_monitor.csv"),

    "meta_weights":
        Path("data/optimization/meta_strategy_weights.csv"),

    "institutional_report":
        Path("results/reports/institutional_strategy_report.txt"),
}


@app.get("/")
def root():
    return {
        "system": "AURUM",
        "status": "online",
        "platform": "institutional_quant_research",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "api": "operational",
    }


@app.get("/meta-strategy")
def meta_strategy():
    path = BASE_PATHS["meta_strategy"]

    if not path.exists():
        return JSONResponse(
            status_code=404,
            content={"error": "meta strategy summary not found"},
        )

    df = pd.read_csv(path)

    return df.to_dict(orient="records")


@app.get("/factor-exposures")
def factor_exposures():
    path = BASE_PATHS["factor_exposures"]

    if not path.exists():
        return JSONResponse(
            status_code=404,
            content={"error": "factor attribution not found"},
        )

    df = pd.read_csv(path)

    return df.to_dict(orient="records")


@app.get("/walk-forward-validation")
def walk_forward_validation():
    path = BASE_PATHS["walk_forward"]

    if not path.exists():
        return JSONResponse(
            status_code=404,
            content={"error": "walk forward validation not found"},
        )

    df = pd.read_csv(path)

    return df.to_dict(orient="records")


@app.get("/risk-monitor")
def risk_monitor():
    path = BASE_PATHS["risk_monitor"]

    if not path.exists():
        return JSONResponse(
            status_code=404,
            content={"error": "risk monitor not found"},
        )

    df = pd.read_csv(path)

    return df.to_dict(orient="records")


@app.get("/latest-allocations")
def latest_allocations():
    path = BASE_PATHS["meta_weights"]

    if not path.exists():
        return JSONResponse(
            status_code=404,
            content={"error": "meta allocations not found"},
        )

    df = pd.read_csv(path)

    return df.to_dict(orient="records")


@app.get("/institutional-report")
def institutional_report():
    path = BASE_PATHS["institutional_report"]

    if not path.exists():
        return JSONResponse(
            status_code=404,
            content={"error": "institutional report not found"},
        )

    with open(path, "r", encoding="utf-8") as f:
        report = f.read()

    return {
        "report": report
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "scripts.api.aurum_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )