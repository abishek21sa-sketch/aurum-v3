from __future__ import annotations

import importlib
import json
from pathlib import Path

from src.config.storage_paths import artifact_path, ensure_storage_dirs


MODULES = [
    "src.market.providers.base_provider",
    "src.market.providers.yfinance_provider",
    "src.market.providers.polygon_provider",
    "src.market.providers.alpaca_provider",
    "src.market.providers.provider_factory",
]


def main() -> None:
    print("=" * 80)
    print("AURUM SPRINT 3A MARKET PROVIDER ABSTRACTION VALIDATION")
    print("=" * 80)

    passed = True
    validation_payload = {
        "provider_abstraction": "created",
        "providers": [],
        "live_download": {},
        "status": "unknown",
    }

    print("MODULE CHECKS")
    print("-" * 80)

    for module in MODULES:
        try:
            importlib.import_module(module)
            print(f"[PASS] import {module}")
        except Exception as exc:
            passed = False
            print(f"[FAIL] import {module}")
            print(f"       {exc}")

    print()
    print("PROVIDER FACTORY CHECK")
    print("-" * 80)

    try:
        from src.market.providers.provider_factory import available_providers, get_provider

        providers = available_providers()
        validation_payload["providers"] = providers

        assert providers == ["yfinance", "polygon", "alpaca"]

        yfinance_provider = get_provider("yfinance")
        polygon_provider = get_provider("polygon")
        alpaca_provider = get_provider("alpaca")

        assert yfinance_provider.provider_name == "yfinance"
        assert polygon_provider.provider_name == "polygon"
        assert alpaca_provider.provider_name == "alpaca"

        print("[PASS] provider factory")
        print(f"[INFO] available providers: {providers}")

    except Exception as exc:
        passed = False
        print("[FAIL] provider factory")
        print(f"       {exc}")

    print()
    print("STUB PROVIDER CHECKS")
    print("-" * 80)

    try:
        from src.market.providers.provider_factory import get_provider

        for name in ["polygon", "alpaca"]:
            provider = get_provider(name)

            try:
                provider.get_prices("SPY", period="5d", interval="1d")
                passed = False
                print(f"[FAIL] {name} should be reserved until API credentials are configured")
            except NotImplementedError:
                print(f"[PASS] {name} provider reserved cleanly")

    except Exception as exc:
        passed = False
        print("[FAIL] stub providers")
        print(f"       {exc}")

    print()
    print("LIVE MARKET DOWNLOAD CHECK")
    print("-" * 80)

    try:
        from src.market.providers.provider_factory import get_provider

        provider = get_provider("yfinance")
        data = provider.get_prices("SPY", period="5d", interval="1d")

        assert provider.provider_name == "yfinance"
        assert provider.validate_prices(data)
        assert len(data) > 0

        validation_payload["live_download"] = {
            "provider": provider.provider_name,
            "ticker": "SPY",
            "rows": int(len(data)),
            "columns": list(map(str, data.columns)),
            "status": "success",
        }

        print("[PASS] live market download")
        print(f"[INFO] rows: {len(data)}")
        print(f"[INFO] columns: {list(data.columns)}")

    except Exception as exc:
        passed = False
        validation_payload["live_download"] = {
            "provider": "yfinance",
            "ticker": "SPY",
            "status": "failed",
            "error": str(exc),
        }
        print("[FAIL] live market download")
        print(f"       {exc}")

    print()
    print("ARTIFACT CHECK")
    print("-" * 80)

    try:
        ensure_storage_dirs()
        validation_payload["status"] = "passed" if passed else "failed"

        output = artifact_path("sprint3", "provider_abstraction_validation.json")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(validation_payload, indent=4), encoding="utf-8")

        assert output.exists()

        print(f"[PASS] artifact written: {output}")

    except Exception as exc:
        passed = False
        print("[FAIL] artifact write")
        print(f"       {exc}")

    print()
    print("=" * 80)

    if passed:
        print("[PASS] SPRINT 3A MARKET PROVIDER ABSTRACTION COMPLETE")
        print("AURUM now uses a provider abstraction with yfinance, Polygon, and Alpaca interfaces.")
    else:
        print("[FAIL] SPRINT 3A MARKET PROVIDER ABSTRACTION FAILED")

    print("=" * 80)

    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()