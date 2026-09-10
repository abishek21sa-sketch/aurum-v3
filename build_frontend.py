import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT / "AURUM"
sys.path.insert(0, str(PROJECT / "scripts"))
from product_runtime import _html  # noqa: E402

(ROOT / "site").mkdir(parents=True, exist_ok=True)
(ROOT / "site" / "index.html").write_text(_html(), encoding="utf-8")
print("AURUM_FRONTEND_BUILD=PASS")
