# scripts/validate_historical_archive.py

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple

import pandas as pd


ASSETS = ["SPY", "QQQ", "DIA", "TLT", "GLD", "VIX", "BTC-USD", "ETH-USD"]

ARCHIVE_DIR = Path("data/digital_twin/historical_prices")
MATRIX_PATH = Path("data/digital_twin/historical_price_matrix.csv")


class HistoricalArchiveValidator:
    def __init__(self) -> None:
        self.results: List[Tuple[str, bool, str]] = []

    def record(self, name: str, passed: bool, detail: str = "") -> None:
        self.results.append((name, passed, detail))
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {name}")
        if detail:
            print(f"       {detail}")

    def validate_asset_files(self) -> None:
        print("\nASSET HISTORY CHECKS")
        print("-" * 80)

        for asset in ASSETS:
            path = ARCHIVE_DIR / f"{asset}.csv"

            if not path.exists():
                self.record(f"{asset} history", False, f"missing={path}")
                continue

            df = pd.read_csv(path)
            passed = {"date", "close"}.issubset(df.columns) and len(df) > 0

            detail = f"rows={len(df)} path={path}"

            if passed:
                detail += f" start={df['date'].min()} end={df['date'].max()}"

            self.record(f"{asset} history", passed, detail)

    def validate_matrix(self) -> None:
        print("\nPRICE MATRIX CHECKS")
        print("-" * 80)

        if not MATRIX_PATH.exists():
            self.record("Historical price matrix", False, f"missing={MATRIX_PATH}")
            return

        df = pd.read_csv(MATRIX_PATH)
        df["date"] = pd.to_datetime(df["date"])

        earliest = df["date"].min()
        latest = df["date"].max()

        self.record(
            "Historical price matrix exists",
            True,
            f"path={MATRIX_PATH} rows={len(df)}",
        )

        self.record(
            "Earliest date <= 2008-01-01",
            earliest <= pd.Timestamp("2008-01-01"),
            f"earliest={earliest.date()}",
        )

        self.record(
            "Latest date within 7 days",
            latest >= pd.Timestamp(datetime.now().date() - timedelta(days=7)),
            f"latest={latest.date()}",
        )

        expected_cols = set(["date"] + ASSETS)
        actual_cols = set(df.columns)

        self.record(
            "All expected columns present",
            expected_cols.issubset(actual_cols),
            f"missing={sorted(expected_cols - actual_cols)}",
        )

    def summarize(self) -> None:
        print("\n" + "=" * 80)
        print("HISTORICAL ARCHIVE VALIDATION SUMMARY")
        print("=" * 80)

        passed = sum(1 for _, ok, _ in self.results if ok)
        total = len(self.results)
        failed = total - passed

        print(f"Passed: {passed}/{total}")
        print(f"Failed: {failed}/{total}")

        if failed == 0:
            print("\nHISTORICAL ARCHIVE COMPLETE")
        else:
            print("\nHISTORICAL ARCHIVE NOT COMPLETE")

    def run(self) -> None:
        print("=" * 80)
        print("AURUM HISTORICAL ARCHIVE VALIDATION")
        print("=" * 80)

        self.validate_asset_files()
        self.validate_matrix()
        self.summarize()


def main() -> None:
    HistoricalArchiveValidator().run()


if __name__ == "__main__":
    main()