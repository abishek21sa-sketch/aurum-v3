"""Capture public SEC, FDIC, Treasury, and research-market snapshots."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.institutional.public_data import DEFAULT_SEC_CIKS, fetch_public_data


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--cik", action="append", dest="ciks", help="SEC CIK; repeatable")
    parser.add_argument("--fdic-limit", type=int, default=100)
    parser.add_argument("--treasury-limit", type=int, default=100)
    parser.add_argument("--market-period", default="1y")
    parser.add_argument("--no-market", action="store_true")
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()
    manifest = fetch_public_data(args.root, ciks=args.ciks or DEFAULT_SEC_CIKS, fdic_limit=args.fdic_limit, treasury_limit=args.treasury_limit, market_period=args.market_period, include_market=not args.no_market)
    print(f"AURUM_PUBLIC_DATA_STATUS={manifest['status']}")
    print(f"AURUM_PUBLIC_DATA_SOURCES={len(manifest['sources'])}")
    print(f"AURUM_PUBLIC_DATA_ERRORS={len(manifest['errors'])}")
    print(f"AURUM_PUBLIC_DATA_CLASS={manifest['data_class']}")
    print(f"AURUM_PUBLIC_DATA_OPTIMIZER_FEED={manifest['optimizer_feed_enabled']}")
    if manifest["status"] != "PASS" and not args.allow_partial:
        raise SystemExit("PUBLIC_DATA_INGESTION=FAIL; rerun with --allow-partial only for research diagnostics")


if __name__ == "__main__":
    main()
