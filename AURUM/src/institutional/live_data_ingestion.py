"""Provider-neutral normalization and receipt generation for live snapshots.

This module deliberately does not fetch from a vendor. A deployment-specific
adapter can normalize vendor payloads here, produce a receipt, and then pass
the normalized rows to ``live_data_contract.validate_snapshot_rows``. Keeping
the receipt separate from the provider SDK makes provenance and replay tests
possible without credentials or network access.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Iterable, Mapping


RECEIPT_SCHEMA_VERSION = "1.0"
NORMALIZED_FIELDS = ("ticker", "timestamp", "open", "high", "low", "close")


def _utc_text(value: datetime | None = None) -> str:
    value = value or datetime.now(timezone.utc)
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _first(row: Mapping[str, Any], *names: str) -> Any:
    for name in names:
        if name in row and row[name] not in (None, ""):
            return row[name]
    return None


def normalize_provider_rows(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Map common vendor field names into AURUM's stable snapshot shape."""
    normalized: list[dict[str, Any]] = []
    for row in rows:
        normalized.append({
            "ticker": _first(row, "ticker", "symbol", "asset", "instrument"),
            "timestamp": _first(row, "timestamp", "as_of", "time", "datetime", "t"),
            "open": _first(row, "open", "o"),
            "high": _first(row, "high", "h"),
            "low": _first(row, "low", "l"),
            "close": _first(row, "close", "c", "price", "last"),
        })
    return normalized


def build_ingestion_receipt(
    rows: Iterable[Mapping[str, Any]],
    *,
    provider: str,
    request_id: str,
    received_at: datetime | None = None,
) -> dict[str, Any]:
    """Return a deterministic, secret-free receipt for normalized rows."""
    normalized = normalize_provider_rows(rows)
    canonical = json.dumps(normalized, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    tickers = sorted({str(row.get("ticker", "")).strip() for row in normalized if row.get("ticker")})
    return {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "provider": str(provider).strip() or "unconfigured",
        "request_id": str(request_id).strip() or "missing-request-id",
        "received_at_utc": _utc_text(received_at),
        "row_count": len(normalized),
        "tickers": tickers,
        "normalized_fields": list(NORMALIZED_FIELDS),
        "payload_sha256": hashlib.sha256(canonical).hexdigest(),
        "credentials_in_receipt": False,
        "network_fetch_performed": False,
    }
