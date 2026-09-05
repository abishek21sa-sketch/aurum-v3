from __future__ import annotations


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 4 REPORTING SUITE")
    print("=" * 80)

    from src.reporting.phase4_master_status_report import (
        generate_phase4_master_status_report,
    )
    from src.reporting.phase4_architecture_summary import (
        generate_phase4_architecture_summary,
    )

    status_json, status_txt = generate_phase4_master_status_report()
    architecture_md = generate_phase4_architecture_summary()

    print("\nGENERATED REPORTS")
    print("-" * 80)
    print(f"[PASS] {status_json}")
    print(f"[PASS] {status_txt}")
    print(f"[PASS] {architecture_md}")

    print("\nFINAL STATUS")
    print("-" * 80)
    print("[PASS] PHASE 4 REPORTING SUITE COMPLETE")


if __name__ == "__main__":
    main()