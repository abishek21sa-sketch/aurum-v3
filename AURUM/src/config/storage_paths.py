from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"
REPORTS_DIR = PROJECT_ROOT / "reports"
LOGS_DIR = PROJECT_ROOT / "logs"
ARCHIVE_DIR = PROJECT_ROOT / "archive"

CORE_QUANT_RESULTS_DIR = RESULTS_DIR / "core_quant"
REALTIME_RESULTS_DIR = RESULTS_DIR / "realtime"
PORTFOLIO_OS_RESULTS_DIR = RESULTS_DIR / "portfolio_os"
AI_RESEARCH_RESULTS_DIR = RESULTS_DIR / "research_firm"
SPRINT_RESULTS_DIR = RESULTS_DIR / "sprint_cleanup"


def ensure_storage_dirs() -> None:
    for path in [
        DATA_DIR,
        RESULTS_DIR,
        REPORTS_DIR,
        LOGS_DIR,
        ARCHIVE_DIR,
        CORE_QUANT_RESULTS_DIR,
        REALTIME_RESULTS_DIR,
        PORTFOLIO_OS_RESULTS_DIR,
        AI_RESEARCH_RESULTS_DIR,
        SPRINT_RESULTS_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)


def artifact_path(*parts: str) -> Path:
    ensure_storage_dirs()
    return RESULTS_DIR.joinpath(*parts)


def report_path(*parts: str) -> Path:
    ensure_storage_dirs()
    return REPORTS_DIR.joinpath(*parts)


def data_path(*parts: str) -> Path:
    ensure_storage_dirs()
    return DATA_DIR.joinpath(*parts)