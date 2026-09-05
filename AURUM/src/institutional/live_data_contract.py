"""Fail-closed market-data contract for a future live AURUM deployment.

The reference product intentionally does not silently replace missing live data
with a fixture.  This module gives the deployment boundary a concrete shape:
provider selection, ticker completeness, numeric validity, timestamp
freshness, and an explicit optimizer-feed approval flag.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import csv
import math
import os
from pathlib import Path
from typing import Any, Iterable


LIVE_DATA_SCHEMA_VERSION = "1.0"
DEFAULT_SNAPSHOT = "data/live/latest_live_market_snapshot.csv"
DEFAULT_TICKERS = ("SPY", "QQQ", "TLT", "GLD", "BTC-USD")
PRICE_FIELDS = ("open", "high", "low", "close")


def _truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _parse_timestamp(value: Any) -> datetime | None:
    if value is None or str(value).strip() == "":
        return None
    text = str(value).strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)


def _required_tickers(root: Path) -> list[str]:
    config = root / "configs" / "prod.yaml"
    if not config.is_file():
        return list(DEFAULT_TICKERS)
    values: list[str] = []
    in_tickers = False
    for line in config.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped == "tickers:":
            in_tickers = True
            continue
        if in_tickers and stripped.startswith("-"):
            values.append(stripped[1:].strip().strip("'\""))
            continue
        if in_tickers and stripped and not line.startswith(" "):
            break
    return values or list(DEFAULT_TICKERS)


def validate_snapshot_rows(
    rows: Iterable[dict[str, Any]],
    required_tickers: Iterable[str],
    *,
    now: datetime | None = None,
    freshness_minutes: int = 30,
) -> dict[str, Any]:
    """Validate a normalized snapshot without fetching or mutating anything."""
    rows = list(rows)
    required = list(dict.fromkeys(str(ticker) for ticker in required_tickers))
    now = now or datetime.now(timezone.utc)
    normalized_now = now.astimezone(timezone.utc)
    seen: set[str] = set()
    invalid_rows: list[str] = []
    timestamps: list[datetime] = []
    for index, row in enumerate(rows):
        ticker = str(row.get("ticker", "")).strip()
        if not ticker or ticker in seen:
            invalid_rows.append(f"row_{index}:missing_or_duplicate_ticker")
        seen.add(ticker)
        timestamp = _parse_timestamp(row.get("timestamp") or row.get("as_of"))
        if timestamp is None:
            invalid_rows.append(f"{ticker or index}:invalid_timestamp")
        else:
            timestamps.append(timestamp)
        for field in PRICE_FIELDS:
            try:
                value = float(row.get(field))
            except (TypeError, ValueError):
                value = math.nan
            if not math.isfinite(value) or value <= 0:
                invalid_rows.append(f"{ticker or index}:invalid_{field}")
    missing = sorted(set(required).difference(seen))
    latest = max(timestamps) if timestamps else None
    age_minutes = (normalized_now - latest).total_seconds() / 60 if latest else None
    freshness_ok = latest is not None and age_minutes is not None and age_minutes <= freshness_minutes and age_minutes >= -5
    checks = {
        "required_tickers_present": not missing,
        "unique_tickers": len(seen) == len(rows),
        "numeric_prices_valid": not any("invalid_" in item for item in invalid_rows),
        "timestamps_valid": bool(timestamps) and len(timestamps) == len(rows),
        "freshness_within_sla": freshness_ok,
    }
    return {
        "schema_version": LIVE_DATA_SCHEMA_VERSION,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "row_count": len(rows),
        "required_tickers": required,
        "observed_tickers": sorted(seen),
        "missing_tickers": missing,
        "latest_timestamp_utc": latest.isoformat().replace("+00:00", "Z") if latest else None,
        "freshness_sla_minutes": freshness_minutes,
        "latest_age_minutes": round(age_minutes, 2) if age_minutes is not None else None,
        "invalid_rows": invalid_rows,
        "checks": checks,
    }


def _read_snapshot(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def build_live_data_status(root: Path) -> dict[str, Any]:
    """Return the current provider/data contract status; never silently fall back."""
    mode = os.getenv("AURUM_MARKET_DATA_MODE", "REFERENCE_ONLY").strip().upper()
    provider = os.getenv("AURUM_MARKET_DATA_PROVIDER", "repository_fixture").strip()
    freshness_minutes = int(os.getenv("AURUM_MARKET_DATA_FRESHNESS_MINUTES", "30"))
    snapshot_path = root / os.getenv("AURUM_MARKET_DATA_SNAPSHOT", DEFAULT_SNAPSHOT)
    required = _required_tickers(root)
    quality = validate_snapshot_rows(
        _read_snapshot(snapshot_path),
        required,
        freshness_minutes=freshness_minutes,
    )
    live_requested = mode in {"LIVE", "PAPER"}
    provider_configured = provider not in {"", "repository_fixture", "unconfigured"} if live_requested else True
    approved = _truthy("AURUM_LIVE_DATA_APPROVED")
    feed_enabled = live_requested and provider_configured and quality["status"] == "PASS" and approved
    if not live_requested:
        status = "REFERENCE_ONLY"
        note = "Reference data is active; live acquisition is not requested."
    elif not provider_configured:
        status = "BLOCKED"
        note = "Live mode requested without an approved provider configuration."
    elif quality["status"] != "PASS":
        status = "BLOCKED"
        note = "Live mode is fail-closed because the snapshot is missing, stale, incomplete, or invalid."
    elif not approved:
        status = "READY_FOR_REVIEW"
        note = "The live snapshot passed quality checks but optimizer feed approval is still required."
    else:
        status = "PASS"
        note = "Live snapshot passed quality checks and the optimizer feed is explicitly approved."
    return {
        "schema_version": LIVE_DATA_SCHEMA_VERSION,
        "service": "AURUM governed market data",
        "status": status,
        "mode": mode,
        "provider": provider,
        "snapshot_path": str(snapshot_path.relative_to(root)).replace("\\", "/") if snapshot_path.is_relative_to(root) else str(snapshot_path),
        "live_requested": live_requested,
        "optimizer_feed_enabled": feed_enabled,
        "external_fetch_enabled": live_requested and provider_configured,
        "approval_required": True,
        "note": note,
        "quality": quality,
        "fail_closed_policy": "No live snapshot may be replaced by bundled reference data without an explicit operator mode change.",
    }
