from pathlib import Path
import json

ROOT = Path(".")
OUT = Path("results/phase6a_project_audit")
OUT.mkdir(parents=True, exist_ok=True)

WATCH_DIRS = [
    "src/portfolio_os",
    "src/market_data",
    "src/database",
    "src/reliability",
    "dashboard",
    "dashboards",
    "src/dashboard",
    "src/dashboards",
    "src/monitoring",
    "src/realtime",
    "scripts",
]

KEYWORDS = [
    "command_center",
    "control_tower",
    "dashboard",
    "portfolio_operating_system",
    "portfolio_os",
    "docker",
    "compose",
    "deployment",
    "reliability",
    "health",
    "monitor",
    "timescale",
    "postgres",
    "redis",
]

def rel(p):
    return str(p).replace("\\", "/")

def file_summary(path):
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        text = ""

    return {
        "path": rel(path),
        "size_bytes": path.stat().st_size,
        "lines": text.count("\n") + 1 if text else 0,
        "matched_keywords": [k for k in KEYWORDS if k.lower() in rel(path).lower() or k.lower() in text.lower()],
        "imports_src": "from src." in text or "import src." in text,
        "uses_streamlit": "streamlit" in text.lower(),
        "uses_docker": "docker" in text.lower() or "compose" in text.lower(),
        "uses_postgres": "postgres" in text.lower() or "psycopg2" in text.lower(),
        "uses_redis": "redis" in text.lower(),
        "uses_yfinance": "yfinance" in text.lower(),
    }

def main():
    files = []

    for d in WATCH_DIRS:
        path = ROOT / d
        if path.exists():
            for f in path.rglob("*"):
                if f.is_file() and f.suffix in {".py", ".yml", ".yaml", ".md", ".txt", ".json"}:
                    files.append(file_summary(f))

    root_files = []
    for name in ["Dockerfile", "docker-compose.yml", "docker-compose.yaml", ".dockerignore", "requirements.txt"]:
        p = ROOT / name
        if p.exists():
            root_files.append(file_summary(p))

    command_centers = [
        f for f in files + root_files
        if any(k in f["path"].lower() for k in ["command_center", "control_tower", "dashboard"])
    ]

    deployment_files = [
        f for f in files + root_files
        if any(k in f["path"].lower() for k in ["docker", "compose", "deployment"])
    ]

    phase6a_modules = {
        "portfolio_os": [f for f in files if f["path"].startswith("src/portfolio_os/")],
        "market_data": [f for f in files if f["path"].startswith("src/market_data/")],
        "database": [f for f in files if f["path"].startswith("src/database/")],
        "reliability": [f for f in files if f["path"].startswith("src/reliability/")],
        "dashboards": command_centers,
        "deployment": deployment_files + root_files,
    }

    report = {
        "total_files_scanned": len(files) + len(root_files),
        "command_centers_or_dashboards_found": command_centers,
        "deployment_files_found": deployment_files + root_files,
        "phase6a_modules": phase6a_modules,
        "direct_yfinance_outside_provider": [
            f for f in files
            if f["uses_yfinance"] and f["path"] != "src/market_data/yfinance_provider.py"
        ],
    }

    out_json = OUT / "phase6a_project_audit.json"
    out_txt = OUT / "phase6a_project_audit.txt"

    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = []
    lines.append("=" * 80)
    lines.append("AURUM PHASE 6A PROJECT STATE AUDIT")
    lines.append("=" * 80)
    lines.append(f"Files scanned: {report['total_files_scanned']}")
    lines.append("")
    lines.append("DASHBOARDS / COMMAND CENTERS FOUND")
    lines.append("-" * 80)
    for f in command_centers:
        lines.append(f"- {f['path']} | streamlit={f['uses_streamlit']} | lines={f['lines']}")

    lines.append("")
    lines.append("DEPLOYMENT FILES FOUND")
    lines.append("-" * 80)
    for f in deployment_files + root_files:
        lines.append(f"- {f['path']} | lines={f['lines']}")

    lines.append("")
    lines.append("PHASE 6A MODULE COUNTS")
    lines.append("-" * 80)
    for key, vals in phase6a_modules.items():
        lines.append(f"- {key}: {len(vals)} files")

    lines.append("")
    lines.append("YFINANCE OUTSIDE PROVIDER")
    lines.append("-" * 80)
    bad = report["direct_yfinance_outside_provider"]
    if not bad:
        lines.append("- None")
    else:
        for f in bad:
            lines.append(f"- {f['path']}")

    lines.append("=" * 80)

    out_txt.write_text("\n".join(lines), encoding="utf-8")

    print("\n".join(lines))
    print(f"\nSaved JSON: {out_json}")
    print(f"Saved TXT:  {out_txt}")

if __name__ == "__main__":
    main()