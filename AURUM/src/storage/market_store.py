from pathlib import Path

import pandas as pd


STORE_DIR = Path("data/storage")
STORE_DIR.mkdir(parents=True, exist_ok=True)

MARKET_STORE_PATH = STORE_DIR / "market_price_store.csv"


def persist_market_snapshot(snapshot: pd.DataFrame) -> Path:
    if snapshot.empty:
        raise ValueError("Cannot persist empty market snapshot.")

    if MARKET_STORE_PATH.exists():
        existing = pd.read_csv(MARKET_STORE_PATH)
        combined = pd.concat([existing, snapshot], ignore_index=True)
    else:
        combined = snapshot.copy()

    combined = combined.drop_duplicates(
        subset=["timestamp_utc", "ticker"],
        keep="last",
    )

    combined.to_csv(MARKET_STORE_PATH, index=False)
    return MARKET_STORE_PATH


def load_market_store() -> pd.DataFrame:
    if not MARKET_STORE_PATH.exists():
        return pd.DataFrame()

    return pd.read_csv(MARKET_STORE_PATH)


if __name__ == "__main__":
    df = load_market_store()
    print("\nMARKET STORE")
    print("=" * 80)
    print(df.tail(20))