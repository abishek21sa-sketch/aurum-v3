from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
import threading
from urllib.parse import parse_qs, urlparse
import urllib.request
import webbrowser


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from product_adapter import (  # noqa: E402
    PROJECT,
    ALGORITHM,
    SUBTITLE,
    PORT,
    CONTROLS,
    DEFAULTS,
    DEMO_STRESS,
    compute,
)
from product_frontend import build_html  # noqa: E402
from src.institutional.deployment_preflight import build_deployment_preflight  # noqa: E402
from src.institutional.ai_intelligence import (  # noqa: E402
    answer_ai_question,
    build_ai_brief,
    build_ai_status,
)
from src.institutional.live_data_contract import build_live_data_status  # noqa: E402
from src.institutional.control_plane import build_control_plane  # noqa: E402
from src.institutional.operations_contract import build_operations_status  # noqa: E402
from src.institutional.external_evidence import build_customer_evidence_status, build_production_image_provenance  # noqa: E402
from src.institutional.synthetic_ml import build_synthetic_dataset_status  # noqa: E402
from src.institutional.public_data import build_public_data_status  # noqa: E402


ARTIFACT = ROOT / "artifacts" / "product_runtime" / "latest_product_evidence.json"
PREFLIGHT_ARTIFACT = ROOT / "artifacts" / "compliance" / "deployment_preflight.json"
AI_ARTIFACT = ROOT / "artifacts" / "product_runtime" / "latest_ai_intelligence_brief.json"


def prepare_demo() -> dict:
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    decision = compute(DEFAULTS)
    counterfactual = compute(DEMO_STRESS)
    payload = {
        "project": PROJECT,
        "algorithm": ALGORITHM,
        "mode": "DETERMINISTIC_PORTFOLIO_DEMO",
        "parameters": DEFAULTS,
        "decision": decision,
        "counterfactual": counterfactual,
        "evidence_boundary": decision["claim"],
        "runtime_contract": "institutional evidence surface over the repository-native MARS-CVaR LP; human review remains mandatory",
    }
    ARTIFACT.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
    ai_payload = {
        "status": build_ai_status(ROOT),
        "brief": build_ai_brief(ROOT, decision),
    }
    AI_ARTIFACT.write_text(json.dumps(ai_payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(f"{ALGORITHM}_PRODUCT_DEMO_PREPARED=PASS")
    print(f"DECISION_ID={decision['decision_id']}")
    return payload


def load_preflight() -> dict:
    """Load the verified preflight artifact without rescanning the repository per request."""
    if PREFLIGHT_ARTIFACT.exists():
        try:
            return json.loads(PREFLIGHT_ARTIFACT.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    return build_deployment_preflight(ROOT)


def _html() -> str:
    return build_html(PROJECT, SUBTITLE, CONTROLS)


def _params_from_query(query: dict[str, list[str]]) -> dict:
    return {
        control["key"]: float(query.get(control["key"], [control["default"]])[0])
        for control in CONTROLS
    }


def _decision_from_query(query: dict[str, list[str]]) -> dict:
    return compute(_params_from_query(query) if query else DEFAULTS)


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, ctype: str = "application/json") -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/health":
                return self._send(200, json.dumps({"status": "ok", "project": PROJECT, "algorithm": ALGORITHM, "surface": "institutional-research-workstation"}).encode())
            if parsed.path == "/":
                return self._send(200, _html().encode("utf-8"), "text/html; charset=utf-8")
            if parsed.path == "/api/evidence":
                payload = json.loads(ARTIFACT.read_text(encoding="utf-8")) if ARTIFACT.exists() else prepare_demo()
                return self._send(200, json.dumps(payload, default=str).encode())
            if parsed.path == "/api/preflight":
                return self._send(200, json.dumps(load_preflight(), default=str).encode())
            if parsed.path == "/api/ai/status":
                return self._send(200, json.dumps(build_ai_status(ROOT), default=str).encode())
            if parsed.path == "/api/ai/brief":
                return self._send(200, json.dumps(build_ai_brief(ROOT, _decision_from_query(parse_qs(parsed.query))), default=str).encode())
            if parsed.path == "/api/ai/ask":
                query = parse_qs(parsed.query)
                question = query.get("question", [""])[0]
                return self._send(200, json.dumps(answer_ai_question(ROOT, _decision_from_query(query), question), default=str).encode())
            if parsed.path == "/api/data/status":
                return self._send(200, json.dumps(build_live_data_status(ROOT), default=str).encode())
            if parsed.path == "/api/control-plane":
                return self._send(200, json.dumps(build_control_plane(ROOT), default=str).encode())
            if parsed.path == "/api/operations/status":
                return self._send(200, json.dumps(build_operations_status(ROOT), default=str).encode())
            if parsed.path == "/api/customer-evidence":
                return self._send(200, json.dumps(build_customer_evidence_status(ROOT), default=str).encode())
            if parsed.path == "/api/image-provenance":
                return self._send(200, json.dumps(build_production_image_provenance(ROOT), default=str).encode())
            if parsed.path == "/api/synthetic-ml/status":
                return self._send(200, json.dumps(build_synthetic_dataset_status(ROOT), default=str).encode())
            if parsed.path == "/api/public-data/status":
                return self._send(200, json.dumps(build_public_data_status(ROOT), default=str).encode())
            if parsed.path == "/api/decision":
                query = parse_qs(parsed.query)
                params = _params_from_query(query)
                decision = compute(params)
                payload = {"project": PROJECT, "algorithm": ALGORITHM, "mode": "INTERACTIVE", "parameters": params, "decision": decision}
                ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
                ARTIFACT.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
                return self._send(200, json.dumps(decision, default=str).encode())
            if parsed.path == "/download/evidence.json":
                payload = ARTIFACT.read_bytes() if ARTIFACT.exists() else json.dumps(prepare_demo(), indent=2).encode()
                return self._send(200, payload, "application/json")
            return self._send(404, b'{"detail":"not found"}')
        except Exception as exc:
            return self._send(500, json.dumps({"error": type(exc).__name__, "detail": str(exc)}).encode())

    def log_message(self, fmt: str, *args) -> None:
        print("[product]", fmt % args)


def serve(*, open_browser: bool = True) -> None:
    if not ARTIFACT.exists():
        prepare_demo()
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://127.0.0.1:{PORT}/"
    print(f"PRODUCT_RUNTIME_READY={url}", flush=True)
    if open_browser:
        webbrowser.open(url, new=2)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping product runtime...")
    finally:
        server.server_close()


def acceptance() -> None:
    payload = prepare_demo()
    decision = payload["decision"]
    required = {"market_regime", "portfolio_workspace", "risk_lab", "constraints", "frontier", "walk_forward_research", "data_provenance", "governance"}
    missing = required.difference(decision)
    if missing:
        raise SystemExit(f"PRODUCT_RUNTIME_ACCEPTANCE=FAIL missing_sections={sorted(missing)}")
    if decision["optimization_authorization"] not in ("AUTHORIZED", "BLOCKED"):
        raise SystemExit("PRODUCT_RUNTIME_ACCEPTANCE=FAIL invalid optimization authorization")
    if decision["research_promotion"] != "RESEARCH_ONLY":
        raise SystemExit("PRODUCT_RUNTIME_ACCEPTANCE=FAIL research promotion was silently changed")
    ai_status = build_ai_status(ROOT)
    ai_brief = build_ai_brief(ROOT, decision)
    if ai_status["service"] != "AURUM Intelligence" or ai_brief["decision_id"] != decision["decision_id"]:
        raise SystemExit("PRODUCT_RUNTIME_ACCEPTANCE=FAIL AI intelligence contract is not grounded")
    if ai_brief["execution_enabled"] is not False or ai_brief["research_promotion"] != "RESEARCH_ONLY":
        raise SystemExit("PRODUCT_RUNTIME_ACCEPTANCE=FAIL AI governance boundary changed")
    changed = payload["counterfactual"]
    if changed["decision_id"] == decision["decision_id"] and changed["raw"] == decision["raw"]:
        raise SystemExit("PRODUCT_RUNTIME_ACCEPTANCE=FAIL counterfactual did not change")
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        for path in (
            "/health",
            "/",
            "/api/evidence",
            "/api/preflight",
            "/api/ai/status",
            "/api/ai/brief",
            "/api/ai/ask?question=What%20is%20the%20main%20risk%3F",
            "/api/data/status",
            "/api/control-plane",
            "/api/operations/status",
            "/api/customer-evidence",
            "/api/image-provenance",
            "/api/synthetic-ml/status",
            "/api/public-data/status",
            "/download/evidence.json",
        ):
            with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=20) as response:
                if response.status != 200:
                    raise SystemExit(f"PRODUCT_RUNTIME_ACCEPTANCE=FAIL http={path}:{response.status}")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
    if not ARTIFACT.exists():
        raise SystemExit("PRODUCT_RUNTIME_ACCEPTANCE=FAIL evidence artifact missing")
    if not AI_ARTIFACT.exists():
        raise SystemExit("PRODUCT_RUNTIME_ACCEPTANCE=FAIL AI artifact missing")
    print(f"{ALGORITHM}_PRODUCT_RUNTIME_ACCEPTANCE=PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare-demo", action="store_true")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--accept", action="store_true")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    if args.prepare_demo:
        prepare_demo()
    if args.accept:
        acceptance()
    if args.serve:
        serve(open_browser=not args.no_browser)
    if not (args.prepare_demo or args.accept or args.serve):
        parser.print_help()


if __name__ == "__main__":
    main()
