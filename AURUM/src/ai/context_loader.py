from pathlib import Path
from datetime import datetime
import json


REPORT_DIRS = [
    Path("results/reports"),
    Path("results/risk"),
    Path("results/analytics"),
    Path("results/optimization"),
    Path("results/forecasting"),
]


TEXT_EXTENSIONS = {".txt", ".md", ".log"}
DATA_EXTENSIONS = {".json", ".csv"}


def read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")


def load_json_file(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def collect_report_files():
    files = []

    for report_dir in REPORT_DIRS:
        if not report_dir.exists():
            continue

        for path in report_dir.rglob("*"):
            if path.is_file() and path.suffix.lower() in TEXT_EXTENSIONS | DATA_EXTENSIONS:
                files.append(path)

    return sorted(files)


def load_aurum_context():
    context = {
        "generated_at": datetime.now().isoformat(),
        "source_files": [],
        "text_reports": {},
        "json_reports": {},
        "csv_reports": {},
    }

    files = collect_report_files()

    for path in files:
        relative_path = str(path)

        context["source_files"].append(relative_path)

        if path.suffix.lower() in TEXT_EXTENSIONS:
            context["text_reports"][relative_path] = read_text_file(path)

        elif path.suffix.lower() == ".json":
            context["json_reports"][relative_path] = load_json_file(path)

        elif path.suffix.lower() == ".csv":
            context["csv_reports"][relative_path] = read_text_file(path)

    return context


def summarize_context_inventory(context: dict) -> str:
    lines = []
    lines.append("AURUM AI CONTEXT INVENTORY")
    lines.append("=" * 70)
    lines.append(f"Generated At: {context['generated_at']}")
    lines.append("")
    lines.append(f"Total Source Files: {len(context['source_files'])}")
    lines.append(f"Text Reports: {len(context['text_reports'])}")
    lines.append(f"JSON Reports: {len(context['json_reports'])}")
    lines.append(f"CSV Reports: {len(context['csv_reports'])}")
    lines.append("")
    lines.append("Loaded Files:")
    lines.append("-" * 70)

    for file in context["source_files"]:
        lines.append(f"- {file}")

    return "\n".join(lines)


def save_context_snapshot(context: dict):
    output_dir = Path("results/ai")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "aurum_context_snapshot.json"

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(context, f, indent=2, default=str)

    return output_path


if __name__ == "__main__":
    context = load_aurum_context()
    inventory = summarize_context_inventory(context)
    output_path = save_context_snapshot(context)

    print(inventory)
    print("")
    print(f"Saved AI context snapshot to: {output_path}")