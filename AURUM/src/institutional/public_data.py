"""Authoritative public-data intake for research-only evidence.

The public lane uses source-owned data where a stable public endpoint exists:
SEC EDGAR company facts, FDIC BankFind institution records, U.S. Treasury
Fiscal Data, and an optional public market-price snapshot through the existing
research-only yfinance adapter. Every artifact is hashed and recorded in a
manifest. This lane never enables the optimizer feed or changes promotion.
"""

from __future__ import annotations

from datetime import datetime, timezone
import csv
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Iterable
import urllib.request


PUBLIC_DATA_SCHEMA_VERSION = "1.0"
PUBLIC_DATA_DIR = "artifacts/public_data"
PUBLIC_DATA_CLASS = "PUBLIC_AUTHORITATIVE_DATA"
DEFAULT_SEC_CIKS = ("0000789019", "0000019617", "0000070858")
DEFAULT_MARKET_TICKERS = ("SPY", "QQQ", "TLT", "GLD", "DIA")
DEFAULT_FDIC_LIMIT = 100
DEFAULT_TREASURY_LIMIT = 100


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _json_bytes(payload: Any) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _fetch_json(url: str, *, user_agent: str, timeout_seconds: int) -> tuple[Any, bytes]:
    request = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": user_agent}, method="GET")
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        raw = response.read()
    return json.loads(raw.decode("utf-8")), raw


def _artifact_record(*, source_id: str, authority: str, source_type: str, source_url: str, artifact: str, payload: bytes, record_count: int, retrieved_at_utc: str, status: str = "PASS", note: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "source_id": source_id,
        "authority": authority,
        "source_type": source_type,
        "source_url": source_url,
        "artifact": artifact,
        "retrieved_at_utc": retrieved_at_utc,
        "bytes": len(payload),
        "sha256": _sha256_bytes(payload),
        "record_count": record_count,
        "status": status,
    }
    if note:
        result["note"] = note
    return result


def _count_payload(source_id: str, payload: Any) -> int:
    if source_id.startswith("sec_companyfacts"):
        facts = payload.get("facts", {}) if isinstance(payload, dict) else {}
        return sum(len(tags) for tags in facts.values() if isinstance(tags, dict))
    if isinstance(payload, dict) and isinstance(payload.get("data"), list):
        return len(payload["data"])
    return 1


def _write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def _market_rows(tickers: Iterable[str], period: str) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Fetch public market prices through the existing optional research adapter."""
    try:
        import yfinance as yf
    except ModuleNotFoundError as exc:  # pragma: no cover - optional runtime
        raise RuntimeError("yfinance is required for --include-market") from exc

    rows: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for ticker in tickers:
        ticker = str(ticker).strip()
        if not ticker:
            continue
        try:
            history = yf.Ticker(ticker).history(period=period, auto_adjust=False)
            if history is None or history.empty:
                raise RuntimeError("empty_history")
            for timestamp, values in history.iterrows():
                close = float(values["Close"])
                if not math.isfinite(close) or close <= 0:
                    continue
                stamp = timestamp.to_pydatetime() if hasattr(timestamp, "to_pydatetime") else timestamp
                if stamp.tzinfo is None:
                    stamp = stamp.replace(tzinfo=timezone.utc)
                rows.append({
                    "ticker": ticker,
                    "timestamp": stamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "open": float(values["Open"]),
                    "high": float(values["High"]),
                    "low": float(values["Low"]),
                    "close": close,
                    "volume": int(values["Volume"]),
                    "source": "yfinance_public_market_data",
                })
        except Exception as exc:  # pragma: no cover - provider/network dependent
            errors.append({"ticker": ticker, "error": type(exc).__name__ + ": " + str(exc)[:240]})
    return rows, errors


def _write_market_csv(path: Path, rows: list[dict[str, Any]]) -> bytes:
    fieldnames = ["ticker", "timestamp", "open", "high", "low", "close", "volume", "source"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return path.read_bytes()


def build_public_market_validation(root: Path) -> dict[str, Any]:
    """Run transparent descriptive math on the captured public price panel."""
    path = root / PUBLIC_DATA_DIR / "market_prices.csv"
    if not path.is_file():
        return {"schema_version": PUBLIC_DATA_SCHEMA_VERSION, "service": "AURUM public market math validation", "status": "REQUIRED", "data_class": "PUBLIC_MARKET_DATA_RESEARCH_ONLY", "promotion_state": "RESEARCH_ONLY", "execution_enabled": False}
    rows: list[dict[str, Any]] = []
    invalid_rows = 0
    duplicate_keys: set[tuple[str, str]] = set()
    duplicates = 0
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            ticker = str(row.get("ticker", "")).strip()
            timestamp = str(row.get("timestamp", "")).strip()
            try:
                close = float(row.get("close", "nan"))
                if not ticker or not timestamp or not math.isfinite(close) or close <= 0:
                    raise ValueError("invalid_row")
                datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except (TypeError, ValueError):
                invalid_rows += 1
                continue
            key = (ticker, timestamp)
            if key in duplicate_keys:
                duplicates += 1
            duplicate_keys.add(key)
            rows.append({"ticker": ticker, "timestamp": timestamp, "close": close})
    per_ticker: list[dict[str, Any]] = []
    for ticker in sorted({row["ticker"] for row in rows}):
        series = sorted((row for row in rows if row["ticker"] == ticker), key=lambda row: row["timestamp"])
        closes = [row["close"] for row in series]
        returns = [closes[index] / closes[index - 1] - 1.0 for index in range(1, len(closes)) if closes[index - 1] > 0]
        mean_return = sum(returns) / len(returns) if returns else 0.0
        variance = sum((value - mean_return) ** 2 for value in returns) / max(1, len(returns) - 1) if returns else 0.0
        running_max = closes[0] if closes else 0.0
        max_drawdown = 0.0
        for close in closes:
            running_max = max(running_max, close)
            max_drawdown = min(max_drawdown, close / running_max - 1.0)
        per_ticker.append({"ticker": ticker, "rows": len(series), "start_timestamp": series[0]["timestamp"] if series else None, "end_timestamp": series[-1]["timestamp"] if series else None, "mean_daily_return": mean_return, "daily_volatility": math.sqrt(variance), "annualized_volatility": math.sqrt(variance) * math.sqrt(252.0), "max_drawdown": max_drawdown})
    dates = sorted({row["timestamp"][:10] for row in rows})
    split_index = max(1, min(len(dates) - 1, int(len(dates) * 0.8))) if len(dates) > 1 else 0
    train_dates = dates[:split_index]
    test_dates = dates[split_index:]
    train_rows = sum(row["timestamp"][:10] in set(train_dates) for row in rows)
    test_rows = sum(row["timestamp"][:10] in set(test_dates) for row in rows)
    no_lookahead = bool(train_dates and test_dates and max(train_dates) < min(test_dates))
    return {"schema_version": PUBLIC_DATA_SCHEMA_VERSION, "service": "AURUM public market math validation", "status": "PASS" if rows and invalid_rows == 0 and duplicates == 0 and no_lookahead else "FAIL", "data_class": "PUBLIC_MARKET_DATA_RESEARCH_ONLY", "source_artifact": f"{PUBLIC_DATA_DIR}/market_prices.csv", "row_count": len(rows), "ticker_count": len(per_ticker), "tickers": [item["ticker"] for item in per_ticker], "invalid_rows": invalid_rows, "duplicate_rows": duplicates, "per_ticker": per_ticker, "chronological_split": {"method": "unique_calendar_dates_80_20", "train_rows": train_rows, "test_rows": test_rows, "train_end_date": max(train_dates) if train_dates else None, "test_start_date": min(test_dates) if test_dates else None, "no_lookahead": no_lookahead}, "promotion_state": "RESEARCH_ONLY", "execution_enabled": False, "claim_boundary": "Descriptive public-price statistics and chronological partition checks do not establish causal forecasts, alpha, or realized investment performance."}


def write_public_market_validation(root: Path) -> dict[str, Any]:
    result = build_public_market_validation(root)
    path = root / PUBLIC_DATA_DIR / "public_market_validation.json"
    path.write_bytes(_json_bytes(result))
    return result


def _base_manifest(*, external_fetch_performed: bool, sources: list[dict[str, Any]], errors: list[dict[str, str]]) -> dict[str, Any]:
    statuses = [str(source.get("status", "FAIL")) for source in sources]
    if sources and not errors and all(status == "PASS" for status in statuses):
        status = "PASS"
    elif sources:
        status = "PARTIAL"
    else:
        status = "FAIL"
    return {
        "schema_version": PUBLIC_DATA_SCHEMA_VERSION,
        "service": "AURUM public data evidence intake",
        "generated_at_utc": _utc_now(),
        "status": status,
        "data_class": PUBLIC_DATA_CLASS,
        "external_fetch_performed": external_fetch_performed,
        "optimizer_feed_enabled": False,
        "promotion_state": "RESEARCH_ONLY",
        "sources": sources,
        "errors": errors,
        "claim_boundary": "Public snapshots support research and feature validation; they do not establish causal forecasts, customer approval, or realized investment performance.",
    }


def fetch_public_data(root: Path, *, ciks: Iterable[str] = DEFAULT_SEC_CIKS, fdic_limit: int = DEFAULT_FDIC_LIMIT, treasury_limit: int = DEFAULT_TREASURY_LIMIT, market_tickers: Iterable[str] = DEFAULT_MARKET_TICKERS, market_period: str = "1y", include_market: bool = True, timeout_seconds: int = 45, user_agent: str | None = None) -> dict[str, Any]:
    """Fetch and snapshot public data; failures are recorded, never replaced."""
    output_dir = root / PUBLIC_DATA_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    user_agent = user_agent or os.getenv("AURUM_SEC_USER_AGENT", "AURUM-Research/1.0 student-research")
    retrieved_at = _utc_now()
    sources: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    for cik in ciks:
        normalized_cik = str(cik).strip().replace("CIK", "").zfill(10)
        source_id = f"sec_companyfacts_CIK{normalized_cik}"
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{normalized_cik}.json"
        artifact = f"{PUBLIC_DATA_DIR}/sec_companyfacts_CIK{normalized_cik}.json"
        try:
            payload, raw = _fetch_json(url, user_agent=user_agent, timeout_seconds=timeout_seconds)
            _write_bytes(root / artifact, raw)
            sources.append(_artifact_record(source_id=source_id, authority="U.S. Securities and Exchange Commission", source_type="PUBLIC_REGULATORY_XBRL", source_url=url, artifact=artifact, payload=raw, record_count=_count_payload(source_id, payload), retrieved_at_utc=retrieved_at, note="SEC public JSON; request used a declared User-Agent."))
        except Exception as exc:  # pragma: no cover - network dependent
            errors.append({"source_id": source_id, "error": type(exc).__name__ + ": " + str(exc)[:240]})

    fdic_url = "https://banks.data.fdic.gov/api/institutions?fields=NAME,CERT,ACTIVE,ASSET,DEP,STALP,STNAME&limit=" + str(int(fdic_limit)) + "&format=json"
    try:
        payload, raw = _fetch_json(fdic_url, user_agent=user_agent, timeout_seconds=timeout_seconds)
        artifact = f"{PUBLIC_DATA_DIR}/fdic_institutions.json"
        _write_bytes(root / artifact, raw)
        sources.append(_artifact_record(source_id="fdic_institutions", authority="Federal Deposit Insurance Corporation", source_type="PUBLIC_BANK_REGULATORY_DATA", source_url=fdic_url, artifact=artifact, payload=raw, record_count=_count_payload("fdic_institutions", payload), retrieved_at_utc=retrieved_at))
    except Exception as exc:  # pragma: no cover - network dependent
        errors.append({"source_id": "fdic_institutions", "error": type(exc).__name__ + ": " + str(exc)[:240]})

    treasury_url = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny?fields=record_date,debt_held_public_amt,intragov_hold_amt,tot_pub_debt_out_amt&sort=-record_date&page[size]=" + str(int(treasury_limit)) + "&format=json"
    try:
        payload, raw = _fetch_json(treasury_url, user_agent=user_agent, timeout_seconds=timeout_seconds)
        artifact = f"{PUBLIC_DATA_DIR}/treasury_debt_to_penny.json"
        _write_bytes(root / artifact, raw)
        sources.append(_artifact_record(source_id="treasury_debt_to_penny", authority="U.S. Department of the Treasury, Fiscal Data", source_type="PUBLIC_GOVERNMENT_FINANCE_DATA", source_url=treasury_url, artifact=artifact, payload=raw, record_count=_count_payload("treasury_debt_to_penny", payload), retrieved_at_utc=retrieved_at))
    except Exception as exc:  # pragma: no cover - network dependent
        errors.append({"source_id": "treasury_debt_to_penny", "error": type(exc).__name__ + ": " + str(exc)[:240]})

    if include_market:
        market_artifact = f"{PUBLIC_DATA_DIR}/market_prices.csv"
        try:
            rows, market_errors = _market_rows(market_tickers, market_period)
            if not rows:
                raise RuntimeError("no_market_rows")
            payload = _write_market_csv(root / market_artifact, rows)
            sources.append(_artifact_record(source_id="market_prices_yfinance", authority="Yahoo Finance public market feed via yfinance", source_type="PUBLIC_MARKET_DATA_RESEARCH_ONLY", source_url="https://finance.yahoo.com/", artifact=market_artifact, payload=payload, record_count=len(rows), retrieved_at_utc=retrieved_at, status="PASS" if not market_errors else "PARTIAL", note="Third-party public market feed; not an authoritative regulatory source."))
            errors.extend({"source_id": "market_prices_yfinance", **error} for error in market_errors)
        except Exception as exc:  # pragma: no cover - network/provider dependent
            errors.append({"source_id": "market_prices_yfinance", "error": type(exc).__name__ + ": " + str(exc)[:240]})

    manifest = _base_manifest(external_fetch_performed=True, sources=sources, errors=errors)
    if (output_dir / "market_prices.csv").is_file():
        validation = write_public_market_validation(root)
        validation_path = output_dir / "public_market_validation.json"
        manifest["derived_validations"] = [{"validation_id": "public_market_math", "artifact": f"{PUBLIC_DATA_DIR}/public_market_validation.json", "status": validation["status"], "sha256": _sha256_bytes(validation_path.read_bytes()), "bytes": validation_path.stat().st_size}]
        if validation["status"] != "PASS" and manifest["status"] == "PASS":
            manifest["status"] = "PARTIAL"
    (output_dir / "public_data_manifest.json").write_bytes(_json_bytes(manifest))
    return manifest


def build_public_data_status(root: Path) -> dict[str, Any]:
    """Validate captured public snapshots without network access."""
    manifest_path = root / PUBLIC_DATA_DIR / "public_data_manifest.json"
    if not manifest_path.is_file():
        return {"schema_version": PUBLIC_DATA_SCHEMA_VERSION, "service": "AURUM public data evidence intake", "status": "REQUIRED", "data_class": "PUBLIC_DATA_NOT_CAPTURED", "external_fetch_performed": False, "optimizer_feed_enabled": False, "promotion_state": "RESEARCH_ONLY", "source_count": 0, "passed_sources": 0, "artifact_integrity": [], "claim_boundary": "Public snapshots support research and feature validation; they do not establish causal forecasts, customer approval, or realized investment performance."}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"schema_version": PUBLIC_DATA_SCHEMA_VERSION, "service": "AURUM public data evidence intake", "status": "FAIL", "error": str(exc), "optimizer_feed_enabled": False}

    integrity: list[dict[str, Any]] = []
    passed = 0
    for source in manifest.get("sources", []):
        artifact = root / str(source.get("artifact", ""))
        actual_sha = _sha256_bytes(artifact.read_bytes()) if artifact.is_file() else None
        ok = artifact.is_file() and actual_sha == source.get("sha256") and source.get("status") == "PASS"
        passed += int(ok)
        integrity.append({"source_id": source.get("source_id"), "artifact": source.get("artifact"), "present": artifact.is_file(), "sha256_matches": actual_sha == source.get("sha256"), "status": "PASS" if ok else "FAIL"})
    source_count = len(manifest.get("sources", []))
    derived_integrity: list[dict[str, Any]] = []
    derived_passed = 0
    for validation in manifest.get("derived_validations", []):
        artifact = root / str(validation.get("artifact", ""))
        actual_sha = _sha256_bytes(artifact.read_bytes()) if artifact.is_file() else None
        ok = artifact.is_file() and actual_sha == validation.get("sha256") and validation.get("status") == "PASS"
        derived_passed += int(ok)
        derived_integrity.append({"validation_id": validation.get("validation_id"), "artifact": validation.get("artifact"), "present": artifact.is_file(), "sha256_matches": actual_sha == validation.get("sha256"), "status": "PASS" if ok else "FAIL"})
    derived_count = len(manifest.get("derived_validations", []))
    status = "PASS" if source_count and passed == source_count and derived_passed == derived_count and not manifest.get("errors") else "PARTIAL" if source_count else "FAIL"
    return {"schema_version": PUBLIC_DATA_SCHEMA_VERSION, "service": manifest.get("service", "AURUM public data evidence intake"), "status": status, "data_class": manifest.get("data_class", PUBLIC_DATA_CLASS), "external_fetch_performed": bool(manifest.get("external_fetch_performed")), "optimizer_feed_enabled": False, "promotion_state": "RESEARCH_ONLY", "source_count": source_count, "passed_sources": passed, "artifact_integrity": integrity, "derived_validation_count": derived_count, "derived_validations": derived_integrity, "errors": manifest.get("errors", []), "claim_boundary": manifest.get("claim_boundary"), "manifest_path": str(manifest_path.relative_to(root)).replace("\\", "/")}
