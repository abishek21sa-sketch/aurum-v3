from __future__ import annotations

from pathlib import Path


FILES = [
    Path("reports/aurum_v1_presentation_package/README_DRAFT.md"),
    Path("reports/aurum_v1_presentation_package/ARCHITECTURE_DIAGRAM.md"),
    Path("reports/aurum_v1_presentation_package/AURUM_WHITEPAPER_DRAFT.md"),
    Path("reports/aurum_v1_presentation_package/RESUME_SUMMARY.md"),
    Path("reports/aurum_v1_presentation_package/PACKAGE_INDEX.md"),
]


def main() -> None:
    print("=" * 80)
    print("AURUM SPRINT 4 PRESENTATION LAYER VALIDATION")
    print("=" * 80)

    passed = True

    for file in FILES:
        if file.exists() and file.stat().st_size > 100:
            print(f"[PASS] {file}")
        else:
            passed = False
            print(f"[FAIL] {file}")

    print("=" * 80)

    if passed:
        print("[PASS] SPRINT 4 PRESENTATION LAYER COMPLETE")
        print("AURUM v1.0 presentation package is generated.")
    else:
        print("[FAIL] SPRINT 4 PRESENTATION LAYER FAILED")
        raise SystemExit(1)

    print("=" * 80)


if __name__ == "__main__":
    main()