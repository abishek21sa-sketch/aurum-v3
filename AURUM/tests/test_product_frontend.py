from pathlib import Path

from scripts.product_adapter import CONTROLS, PROJECT, SUBTITLE
from scripts.product_frontend import build_html


ROOT = Path(__file__).resolve().parents[1]


def test_product_frontend_contains_command_center_surface_and_safety_copy():
    html = build_html(PROJECT, SUBTITLE, CONTROLS)

    for token in (
        "Executive readout",
        "Signal summary",
        "Governance lane",
        "Market and regime command view",
        "Current vs counterfactual",
        "Evidence room",
        "No orders emitted",
        "AURUM Intelligence",
        "Ask AURUM",
        "Control plane",
        "/api/control-plane",
        "/api/operations/status",
        "/api/ai/brief",
        "/api/ai/ask",
        "/api/preflight",
    ):
        assert token in html


def test_runtime_delegates_to_frontend_template():
    runtime = (ROOT / "scripts/product_runtime.py").read_text(encoding="utf-8")

    assert "from product_frontend import build_html" in runtime
    assert "return build_html(PROJECT, SUBTITLE, CONTROLS)" in runtime
