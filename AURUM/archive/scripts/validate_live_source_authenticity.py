from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


SNAPSHOT_PATH = Path("results/realtime/live_market_snapshot.json")

OUTPUT_DIR = Path("results/institutional")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_JSON = OUTPUT_DIR / "live_source_authenticity_validation.json"
OUTPUT_TXT = OUTPUT_DIR / "live_source_authenticity_validation.txt"


REQUIRED_TICKERS = [
    "SPY",
    "QQQ",
    "DIA",
    "TLT",
    "GLD",
    "BTC-USD",
    "ETH-USD",
    "VIX",
]


PRODUCTION_SOURCES = {
    "polygon",
    "polygon.io",
    "alpaca",
    "databento",
    "ibkr",
    "interactive_brokers",
    "interactive brokers",
    "tradier",
    "iex",
    "iex_cloud",
    "nasdaq",
    "refinitiv",
    "bloomberg",
}


RESEARCH_SOURCES = {
    "yfinance",
    "yahoo",
    "yahoo_finance",
    "stooq",
    "tiingo",
    "alpha_vantage",
    "finnhub",
}


INVALID_SOURCES = {
    "demo",
    "synthetic",
    "simulation",
    "simulated",
    "test",
    "mock",
    "paper_market",
    "synthetic_validation_tick",
    "unknown",
    "",
}


@dataclass
class SourceAuthenticityCheck:
    ticker: str
    status: str
    source: str
    authenticity_class: str
    message: str


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_snapshot() -> Dict[str, Any]:
    if not SNAPSHOT_PATH.exists():
        return {}

    try:
        return json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def normalize_source(source: Any) -> str:
    if source is None:
        return ""

    return str(source).strip().lower()


def classify_source(source: str) -> str:
    normalized = normalize_source(source)

    if normalized in PRODUCTION_SOURCES:
        return "PRODUCTION_EXTERNAL"

    if normalized in RESEARCH_SOURCES:
        return "RESEARCH_EXTERNAL"

    if normalized in INVALID_SOURCES:
        return "INVALID"

    if "demo" in normalized:
        return "INVALID"

    if "synthetic" in normalized:
        return "INVALID"

    if "mock" in normalized:
        return "INVALID"

    if "sim" in normalized:
        return "INVALID"

    return "UNKNOWN"


def status_for_class(auth_class: str) -> str:
    if auth_class in {"PRODUCTION_EXTERNAL", "RESEARCH_EXTERNAL"}:
        return "PASS"

    return "FAIL"


def records_by_ticker(snapshot: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    records = snapshot.get("records", [])

    result: Dict[str, Dict[str, Any]] = {}

    if isinstance(records, list):
        for row in records:
            if not isinstance(row, dict):
                continue

            ticker = row.get("ticker") or row.get("symbol") or row.get("asset")

            if ticker:
                result[str(ticker)] = row

    return result


def check_sources(snapshot: Dict[str, Any]) -> List[SourceAuthenticityCheck]:
    records = records_by_ticker(snapshot)

    checks: List[SourceAuthenticityCheck] = []

    for ticker in REQUIRED_TICKERS:
        row = records.get(ticker, {})

        source = normalize_source(row.get("source", "missing"))
        auth_class = classify_source(source)
        status = status_for_class(auth_class)

        if not row:
            checks.append(
                SourceAuthenticityCheck(
                    ticker=ticker,
                    status="FAIL",
                    source="missing",
                    authenticity_class="MISSING",
                    message=f"{ticker} is missing from live_market_snapshot.",
                )
            )
            continue

        if auth_class == "PRODUCTION_EXTERNAL":
            message = f"{ticker} source is production external market API."
        elif auth_class == "RESEARCH_EXTERNAL":
            message = f"{ticker} source is external research market API."
        elif auth_class == "INVALID":
            message = f"{ticker} source is demo/synthetic/non-external."
        else:
            message = f"{ticker} source is not recognized as approved external market API."

        checks.append(
            SourceAuthenticityCheck(
                ticker=ticker,
                status=status,
                source=source,
                authenticity_class=auth_class,
                message=message,
            )
        )

    return checks


def determine_authenticity_status(checks: List[SourceAuthenticityCheck]) -> str:
    classes = {check.authenticity_class for check in checks}

    if all(check.authenticity_class == "PRODUCTION_EXTERNAL" for check in checks):
        return "PRODUCTION_AUTHENTIC"

    if all(
        check.authenticity_class in {"PRODUCTION_EXTERNAL", "RESEARCH_EXTERNAL"}
        for check in checks
    ):
        return "RESEARCH_AUTHENTIC"

    if "MISSING" in classes:
        return "MISSING_DATA"

    return "NOT_AUTHENTIC"


def run_validation() -> Dict[str, Any]:
    snapshot = load_snapshot()
    checks = check_sources(snapshot)

    failed = [check for check in checks if check.status != "PASS"]
    passed = [check for check in checks if check.status == "PASS"]

    authenticity_status = determine_authenticity_status(checks)

    real_time_claim_allowed = authenticity_status in {
        "PRODUCTION_AUTHENTIC",
        "RESEARCH_AUTHENTIC",
    }

    production_real_time_allowed = authenticity_status == "PRODUCTION_AUTHENTIC"

    report = {
        "platform": "AURUM",
        "phase": "Phase 4M",
        "gate": "Live Source Authenticity Gate",
        "validated_at_utc": now_utc(),
        "snapshot_path": str(SNAPSHOT_PATH),
        "snapshot_exists": SNAPSHOT_PATH.exists(),
        "authenticity_status": authenticity_status,
        "status": "PASS" if real_time_claim_allowed else "FAIL",
        "real_time_claim_allowed": real_time_claim_allowed,
        "production_real_time_allowed": production_real_time_allowed,
        "passed_checks": len(passed),
        "failed_checks": len(failed),
        "checks": [asdict(check) for check in checks],
        "approved_production_sources": sorted(PRODUCTION_SOURCES),
        "approved_research_sources": sorted(RESEARCH_SOURCES),
        "invalid_sources": sorted(INVALID_SOURCES),
        "interpretation": build_interpretation(
            authenticity_status=authenticity_status,
            production_real_time_allowed=production_real_time_allowed,
        ),
    }

    save_report(report)

    return report


def build_interpretation(
    authenticity_status: str,
    production_real_time_allowed: bool,
) -> str:
    if authenticity_status == "PRODUCTION_AUTHENTIC":
        return (
            "AURUM market data source authenticity is production-grade. "
            "AURUM may claim production external real-time market connectivity."
        )

    if authenticity_status == "RESEARCH_AUTHENTIC":
        return (
            "AURUM market data source authenticity is external but research-grade. "
            "AURUM may claim external research-data freshness, but not production trading connectivity."
        )

    if authenticity_status == "MISSING_DATA":
        return (
            "AURUM cannot verify source authenticity because required snapshot data is missing."
        )

    return (
        "AURUM market data originates from demo/synthetic/non-external feeds. "
        "AURUM must not claim external real-time market connectivity."
    )


def save_report(report: Dict[str, Any]) -> None:
    OUTPUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = []
    lines.append("=" * 80)
    lines.append("AURUM LIVE SOURCE AUTHENTICITY GATE")
    lines.append("=" * 80)
    lines.append(f"Validated At UTC: {report['validated_at_utc']}")
    lines.append(f"Snapshot Path: {report['snapshot_path']}")
    lines.append(f"Snapshot Exists: {report['snapshot_exists']}")
    lines.append("")
    lines.append(f"Authenticity Status: {report['authenticity_status']}")
    lines.append(f"Final Status: {report['status']}")
    lines.append(f"Real-Time Claim Allowed: {report['real_time_claim_allowed']}")
    lines.append(f"Production Real-Time Allowed: {report['production_real_time_allowed']}")
    lines.append(f"Passed Checks: {report['passed_checks']}")
    lines.append(f"Failed Checks: {report['failed_checks']}")
    lines.append("")
    lines.append("CHECKS")
    lines.append("-" * 80)

    for check in report["checks"]:
        lines.append(
            f"[{check['status']}] {check['ticker']:<8} | "
            f"source={check['source']:<20} | "
            f"class={check['authenticity_class']:<22} | "
            f"{check['message']}"
        )

    lines.append("")
    lines.append("INTERPRETATION")
    lines.append("-" * 80)
    lines.append(report["interpretation"])

    OUTPUT_TXT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    print("=" * 80)
    print("AURUM LIVE SOURCE AUTHENTICITY GATE")
    print("=" * 80)

    report = run_validation()

    for check in report["checks"]:
        print(
            f"[{check['status']}] {check['ticker']:<8} | "
            f"source={check['source']} | class={check['authenticity_class']}"
        )

    print("-" * 80)
    print(f"Authenticity Status: {report['authenticity_status']}")
    print(f"Final Status: {report['status']}")
    print(f"Real-Time Claim Allowed: {report['real_time_claim_allowed']}")
    print(f"Production Real-Time Allowed: {report['production_real_time_allowed']}")
    print(f"Saved: {OUTPUT_JSON}")
    print(f"Saved: {OUTPUT_TXT}")

    if not report["real_time_claim_allowed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()