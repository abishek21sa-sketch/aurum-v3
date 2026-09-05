from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"

DATA_LAKE_DIRS = [
    DATA_DIR / "raw",
    DATA_DIR / "processed",
    DATA_DIR / "features",
    DATA_DIR / "regimes",
    DATA_DIR / "forecasts",
    DATA_DIR / "allocations",
    DATA_DIR / "backtests",
    DATA_DIR / "live",
]

RESULT_DIRS = [
    RESULTS_DIR / "reports",
    RESULTS_DIR / "figures",
    RESULTS_DIR / "logs",
    RESULTS_DIR / "runtime",
]


def create_storage_directories() -> None:
    for path in DATA_LAKE_DIRS + RESULT_DIRS:
        path.mkdir(parents=True, exist_ok=True)


def get_data_path(layer: str, filename: str) -> Path:
    valid_layers = {
        "raw",
        "processed",
        "features",
        "regimes",
        "forecasts",
        "allocations",
        "backtests",
        "live",
        "signals",
    }

    if layer not in valid_layers:
        raise ValueError(f"Invalid data layer: {layer}")

    return DATA_DIR / layer / filename


def get_result_path(layer: str, filename: str) -> Path:
    valid_layers = {
        "reports",
        "figures",
        "logs",
        "runtime",
    }

    if layer not in valid_layers:
        raise ValueError(f"Invalid results layer: {layer}")

    return RESULTS_DIR / layer / filename


if __name__ == "__main__":
    create_storage_directories()
    print("Storage directories created successfully.")