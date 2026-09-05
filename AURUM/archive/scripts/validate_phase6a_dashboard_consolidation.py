from pathlib import Path


def check(condition: bool, label: str):
    if condition:
        print(f"[PASS] {label}")
    else:
        print(f"[FAIL] {label}")
        raise SystemExit(1)


def main():
    print("=" * 80)
    print("AURUM PHASE 6A DASHBOARD CONSOLIDATION VALIDATION")
    print("=" * 80)

    canonical = Path("src/dashboard/institutional_command_center.py")
    launcher = Path("dashboard/official_dashboard.py")
    old = Path("dashboard/institutional_control_tower.py")
    archived = Path("dashboard/deprecated/institutional_control_tower_phase6a_backup.py")
    dockerfile = Path("Dockerfile.dashboard")

    check(canonical.exists(), "canonical institutional command center exists")
    check(launcher.exists(), "official dashboard launcher exists")
    check(not old.exists(), "duplicate control tower removed from active dashboard folder")
    check(archived.exists(), "old control tower archived")
    check(dockerfile.exists(), "Dockerfile.dashboard exists")

    docker_text = dockerfile.read_text(encoding="utf-8")
    check("dashboard/official_dashboard.py" in docker_text, "Docker dashboard points to official dashboard")

    canonical_text = canonical.read_text(encoding="utf-8", errors="ignore")
    for page in ["Portfolio OS", "Database", "Reliability"]:
        check(page in canonical_text, f"{page} page integrated into command center")

    print("=" * 80)
    print("[PASS] PHASE 6A DASHBOARD CONSOLIDATION COMPLETE")
    print("AURUM now has one official institutional dashboard.")
    print("=" * 80)


if __name__ == "__main__":
    main()