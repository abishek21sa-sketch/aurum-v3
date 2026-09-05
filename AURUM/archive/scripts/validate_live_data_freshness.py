from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


RESULTS_DIR = Path("results/institutional")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_JSON = RESULTS_DIR / "live_data_freshness_validation.json"
OUTPUT_TXT = RESULTS_DIR / "live_data_freshness_validation.txt"

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

EQUITY_TICKERS = ["SPY", "QQQ"]
CRYPTO_TICKERS = ["BTC-USD"]
REQUIRED_TICKERS = EQUITY_TICKERS + CRYPTO_TICKERS

MAX_SNAPSHOT_AGE_SECONDS = 10 * 60
MAX_REDIS_LOOKBACK = 500


@dataclass
class FreshnessCheck:
    ticker: str
    asset_type: str
    status: str
    message: str
    observed_timestamp: Optional[str]
    observed_date: Optional[str]
    expected_date: Optional[str]
    source: str


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def parse_timestamp(value: Any) -> Optional[datetime]:
    if value is None:
        return None

    try:
        text = str(value).strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(text)

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt.astimezone(timezone.utc)

    except Exception:
        return None


def load_json(path: Path) -> Any:
    try:
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def observed_date(dt: Optional[datetime]) -> Optional[date]:
    return dt.date() if dt else None


def nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    d = date(year, month, 1)

    while d.weekday() != weekday:
        d += timedelta(days=1)

    return d + timedelta(days=7 * (n - 1))


def last_weekday(year: int, month: int, weekday: int) -> date:
    if month == 12:
        d = date(year, 12, 31)
    else:
        d = date(year, month + 1, 1) - timedelta(days=1)

    while d.weekday() != weekday:
        d -= timedelta(days=1)

    return d


def observed_holiday(d: date) -> date:
    if d.weekday() == 5:
        return d - timedelta(days=1)
    if d.weekday() == 6:
        return d + timedelta(days=1)
    return d


def good_friday(year: int) -> date:
    # Anonymous Gregorian algorithm for Easter, then minus 2 days.
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    easter = date(year, month, day)
    return easter - timedelta(days=2)


def nyse_holidays(year: int) -> set[date]:
    holidays = {
        observed_holiday(date(year, 1, 1)),          # New Year
        nth_weekday(year, 1, 0, 3),                 # MLK
        nth_weekday(year, 2, 0, 3),                 # Presidents Day
        good_friday(year),                          # Good Friday
        last_weekday(year, 5, 0),                   # Memorial Day
        observed_holiday(date(year, 6, 19)),        # Juneteenth
        observed_holiday(date(year, 7, 4)),         # Independence Day
        nth_weekday(year, 9, 0, 1),                 # Labor Day
        nth_weekday(year, 11, 3, 4),                # Thanksgiving
        observed_holiday(date(year, 12, 25)),       # Christmas
    }

    return holidays


def is_nyse_trading_day(d: date) -> bool:
    if d.weekday() >= 5:
        return False

    return d not in nyse_holidays(d.year)


def latest_nyse_trading_session(as_of: datetime) -> date:
    d = as_of.date()

    while not is_nyse_trading_day(d):
        d -= timedelta(days=1)

    return d


def snapshot_candidates() -> List[Path]:
    explicit = [
        Path("results/live_market_snapshot.json"),
        Path("results/market/live_market_snapshot.json"),
        Path("results/realtime/live_market_snapshot.json"),
        Path("results/market_data/live_market_snapshot.json"),
        Path("results/digital_twin/live_state/live_market_snapshot.json"),
        Path("results/digital_twin/live_state/latest_market_snapshot.json"),
    ]

    discovered = list(Path("results").glob("**/*market*snapshot*.json"))

    seen = set()
    candidates = []

    for path in explicit + discovered:
        if path.exists() and path not in seen:
            seen.add(path)
            candidates.append(path)

    return candidates


def extract_records_from_json(payload: Any) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []

    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict):
                records.append(item)
        return records

    if not isinstance(payload, dict):
        return records

    for key in ["records", "data", "ticks", "prices", "snapshots", "market_data"]:
        value = payload.get(key)

        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    records.append(item)

        if isinstance(value, dict):
            for ticker, item in value.items():
                if isinstance(item, dict):
                    row = item.copy()
                    row.setdefault("ticker", ticker)
                    records.append(row)

    for ticker, item in payload.items():
        if isinstance(item, dict) and (
            "timestamp" in item
            or "timestamp_utc" in item
            or "date" in item
            or "price" in item
        ):
            row = item.copy()
            row.setdefault("ticker", ticker)
            records.append(row)

    if any(k in payload for k in ["ticker", "symbol", "asset"]):
        records.append(payload)

    return records


def find_latest_snapshot_records() -> Tuple[Dict[str, Dict[str, Any]], Optional[Path], Optional[datetime]]:
    latest_by_ticker: Dict[str, Dict[str, Any]] = {}
    best_path = None
    best_generated_at = None

    for path in snapshot_candidates():
        payload = load_json(path)
        if payload is None:
            continue

        generated_at = None

        if isinstance(payload, dict):
            for key in ["generated_at", "timestamp", "timestamp_utc", "created_at", "as_of"]:
                generated_at = parse_timestamp(payload.get(key))
                if generated_at:
                    break

        records = extract_records_from_json(payload)

        for record in records:
            ticker = (
                record.get("ticker")
                or record.get("symbol")
                or record.get("asset")
                or record.get("Ticker")
            )

            if not ticker:
                continue

            ticker = str(ticker)

            timestamp = None

            for key in [
                "timestamp_utc",
                "timestamp",
                "datetime",
                "last_trade_time",
                "last_price_time",
                "date",
                "as_of",
            ]:
                timestamp = parse_timestamp(record.get(key))
                if timestamp:
                    break

            if ticker not in latest_by_ticker:
                latest_by_ticker[ticker] = {
                    **record,
                    "_parsed_timestamp": timestamp.isoformat() if timestamp else None,
                    "_source": str(path),
                }
            else:
                old_ts = parse_timestamp(latest_by_ticker[ticker].get("_parsed_timestamp"))
                if timestamp and (not old_ts or timestamp > old_ts):
                    latest_by_ticker[ticker] = {
                        **record,
                        "_parsed_timestamp": timestamp.isoformat(),
                        "_source": str(path),
                    }

        if generated_at and (best_generated_at is None or generated_at > best_generated_at):
            best_generated_at = generated_at
            best_path = path
        elif best_path is None and records:
            best_path = path

    return latest_by_ticker, best_path, best_generated_at


def find_redis_latest_ticks() -> Dict[str, Dict[str, Any]]:
    try:
        import redis

        client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        client.ping()

        rows = client.xrevrange("market_ticks", count=MAX_REDIS_LOOKBACK)

    except Exception:
        return {}

    latest: Dict[str, Dict[str, Any]] = {}

    for redis_id, raw in rows:
        event = {}

        for key, value in raw.items():
            try:
                event[key] = json.loads(value)
            except Exception:
                event[key] = value

        ticker = event.get("ticker") or event.get("symbol") or event.get("asset")

        if not ticker:
            continue

        ticker = str(ticker)

        if ticker not in latest:
            event["_redis_id"] = redis_id
            event["_source"] = "redis:market_ticks"
            latest[ticker] = event

        if all(t in latest for t in REQUIRED_TICKERS):
            break

    return latest


def merge_sources(
    snapshot_records: Dict[str, Dict[str, Any]],
    redis_records: Dict[str, Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    merged = dict(snapshot_records)

    for ticker, event in redis_records.items():
        if ticker not in merged:
            merged[ticker] = event
            continue

        snapshot_ts = parse_timestamp(merged[ticker].get("_parsed_timestamp")) or find_event_timestamp(merged[ticker])
        redis_ts = find_event_timestamp(event)

        if redis_ts and (not snapshot_ts or redis_ts > snapshot_ts):
            merged[ticker] = event

    return merged


def find_event_timestamp(event: Dict[str, Any]) -> Optional[datetime]:
    for key in [
        "_parsed_timestamp",
        "timestamp_utc",
        "timestamp",
        "datetime",
        "last_trade_time",
        "last_price_time",
        "date",
        "as_of",
        "ingested_at",
    ]:
        dt = parse_timestamp(event.get(key))
        if dt:
            return dt

    return None


def check_ticker(
    ticker: str,
    event: Optional[Dict[str, Any]],
    expected_equity_session: date,
    today_utc: date,
) -> FreshnessCheck:
    asset_type = "crypto" if ticker in CRYPTO_TICKERS else "equity"

    if not event:
        return FreshnessCheck(
            ticker=ticker,
            asset_type=asset_type,
            status="FAIL",
            message=f"{ticker} has no available market data record.",
            observed_timestamp=None,
            observed_date=None,
            expected_date=str(today_utc if asset_type == "crypto" else expected_equity_session),
            source="missing",
        )

    ts = find_event_timestamp(event)
    source = str(event.get("_source", event.get("source", "unknown")))

    if not ts:
        return FreshnessCheck(
            ticker=ticker,
            asset_type=asset_type,
            status="FAIL",
            message=f"{ticker} has no parseable market data timestamp.",
            observed_timestamp=None,
            observed_date=None,
            expected_date=str(today_utc if asset_type == "crypto" else expected_equity_session),
            source=source,
        )

    obs_date = ts.date()

    if asset_type == "crypto":
        if obs_date == today_utc:
            status = "PASS"
            message = f"{ticker} latest data is from today."
        else:
            status = "FAIL"
            message = f"{ticker} stale market data: observed {obs_date}, expected {today_utc}."

        return FreshnessCheck(
            ticker=ticker,
            asset_type=asset_type,
            status=status,
            message=message,
            observed_timestamp=ts.isoformat(),
            observed_date=str(obs_date),
            expected_date=str(today_utc),
            source=source,
        )

    if obs_date == expected_equity_session:
        status = "PASS"
        message = f"{ticker} latest data is from current trading session."
    else:
        status = "FAIL"
        message = (
            f"{ticker} stale market data: observed {obs_date}, "
            f"expected current trading session {expected_equity_session}."
        )

    return FreshnessCheck(
        ticker=ticker,
        asset_type=asset_type,
        status=status,
        message=message,
        observed_timestamp=ts.isoformat(),
        observed_date=str(obs_date),
        expected_date=str(expected_equity_session),
        source=source,
    )


def check_snapshot_generated_now(snapshot_path: Optional[Path], generated_at: Optional[datetime]) -> FreshnessCheck:
    now = now_utc()

    if generated_at is None:
        return FreshnessCheck(
            ticker="live_market_snapshot",
            asset_type="system",
            status="FAIL",
            message="live_market_snapshot has no parseable generated_at/timestamp.",
            observed_timestamp=None,
            observed_date=None,
            expected_date=str(now.date()),
            source=str(snapshot_path) if snapshot_path else "missing",
        )

    age = (now - generated_at).total_seconds()

    if 0 <= age <= MAX_SNAPSHOT_AGE_SECONDS:
        return FreshnessCheck(
            ticker="live_market_snapshot",
            asset_type="system",
            status="PASS",
            message="live_market_snapshot generated now.",
            observed_timestamp=generated_at.isoformat(),
            observed_date=str(generated_at.date()),
            expected_date=str(now.date()),
            source=str(snapshot_path),
        )

    return FreshnessCheck(
        ticker="live_market_snapshot",
        asset_type="system",
        status="FAIL",
        message=(
            f"live_market_snapshot is stale: age={age:.1f}s, "
            f"max_allowed={MAX_SNAPSHOT_AGE_SECONDS}s."
        ),
        observed_timestamp=generated_at.isoformat(),
        observed_date=str(generated_at.date()),
        expected_date=str(now.date()),
        source=str(snapshot_path),
    )


def run_validation() -> Dict[str, Any]:
    now = now_utc()
    expected_session = latest_nyse_trading_session(now)
    today = now.date()

    snapshot_records, snapshot_path, snapshot_generated_at = find_latest_snapshot_records()
    redis_records = find_redis_latest_ticks()
    records = merge_sources(snapshot_records, redis_records)

    checks: List[FreshnessCheck] = []

    for ticker in REQUIRED_TICKERS:
        checks.append(
            check_ticker(
                ticker=ticker,
                event=records.get(ticker),
                expected_equity_session=expected_session,
                today_utc=today,
            )
        )

    checks.append(
        check_snapshot_generated_now(
            snapshot_path=snapshot_path,
            generated_at=snapshot_generated_at,
        )
    )

    failed = [c for c in checks if c.status != "PASS"]
    passed = [c for c in checks if c.status == "PASS"]

    live_claim_allowed = len(failed) == 0

    report = {
        "platform": "AURUM",
        "phase": "Phase 4L",
        "gate": "Live-Date Integrity Gate",
        "validated_at_utc": now.isoformat(),
        "today_utc": str(today),
        "expected_us_equity_session": str(expected_session),
        "snapshot_path": str(snapshot_path) if snapshot_path else None,
        "snapshot_generated_at": snapshot_generated_at.isoformat() if snapshot_generated_at else None,
        "live_claim_allowed": live_claim_allowed,
        "status": "PASS" if live_claim_allowed else "FAIL",
        "passed_checks": len(passed),
        "failed_checks": len(failed),
        "checks": [asdict(c) for c in checks],
        "interpretation": (
            "AURUM may call this run live."
            if live_claim_allowed
            else "AURUM must not call this run live because one or more live-date freshness checks failed."
        ),
    }

    save_report(report)
    return report


def save_report(report: Dict[str, Any]) -> None:
    OUTPUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = []
    lines.append("=" * 80)
    lines.append("AURUM LIVE-DATE INTEGRITY GATE")
    lines.append("=" * 80)
    lines.append(f"Validated At UTC: {report['validated_at_utc']}")
    lines.append(f"Today UTC: {report['today_utc']}")
    lines.append(f"Expected U.S. Equity Session: {report['expected_us_equity_session']}")
    lines.append(f"Snapshot Path: {report['snapshot_path']}")
    lines.append(f"Snapshot Generated At: {report['snapshot_generated_at']}")
    lines.append("")
    lines.append(f"Final Status: {report['status']}")
    lines.append(f"Live Claim Allowed: {report['live_claim_allowed']}")
    lines.append(f"Passed Checks: {report['passed_checks']}")
    lines.append(f"Failed Checks: {report['failed_checks']}")
    lines.append("")
    lines.append("CHECKS")
    lines.append("-" * 80)

    for check in report["checks"]:
        lines.append(
            f"[{check['status']}] {check['ticker']} | "
            f"{check['message']} | "
            f"observed={check['observed_date']} | "
            f"expected={check['expected_date']} | "
            f"source={check['source']}"
        )

    lines.append("")
    lines.append("INTERPRETATION")
    lines.append("-" * 80)
    lines.append(report["interpretation"])

    OUTPUT_TXT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    print("=" * 80)
    print("AURUM LIVE-DATE INTEGRITY GATE")
    print("=" * 80)

    report = run_validation()

    for check in report["checks"]:
        print(
            f"[{check['status']}] {check['ticker']} | {check['message']}"
        )

    print("-" * 80)
    print(f"Final Status: {report['status']}")
    print(f"Live Claim Allowed: {report['live_claim_allowed']}")
    print(f"Saved: {OUTPUT_JSON}")
    print(f"Saved: {OUTPUT_TXT}")

    if not report["live_claim_allowed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()