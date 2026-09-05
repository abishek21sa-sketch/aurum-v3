from pathlib import Path

import pandas as pd
from fastapi import APIRouter


router = APIRouter(prefix="/anomalies", tags=["anomalies"])

ANOMALY_PATH = Path("results/anomalies/latest_anomaly_alerts.csv")


@router.get("/latest")
def get_latest_anomaly_alerts():
    if not ANOMALY_PATH.exists():
        return {"status": "missing", "path": str(ANOMALY_PATH), "data": []}

    df = pd.read_csv(ANOMALY_PATH)

    return {
        "status": "ok",
        "path": str(ANOMALY_PATH),
        "rows": len(df),
        "data": df.to_dict(orient="records"),
    }