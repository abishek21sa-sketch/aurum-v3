from pathlib import Path

import pandas as pd
from fastapi import APIRouter


router = APIRouter(prefix="/market", tags=["market"])

LIVE_SNAPSHOT_PATH = Path("data/live/latest_live_market_snapshot.csv")
MARKET_STORE_PATH = Path("data/storage/market_price_store.csv")


def _read_csv(path: Path):
    if not path.exists():
        return {"status": "missing", "path": str(path), "data": []}

    df = pd.read_csv(path)
    return {
        "status": "ok",
        "path": str(path),
        "rows": len(df),
        "data": df.to_dict(orient="records"),
    }


@router.get("/latest")
def get_latest_market_snapshot():
    return _read_csv(LIVE_SNAPSHOT_PATH)


@router.get("/store")
def get_market_store():
    return _read_csv(MARKET_STORE_PATH)