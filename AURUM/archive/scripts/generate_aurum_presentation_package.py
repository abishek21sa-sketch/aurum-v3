from __future__ import annotations

import textwrap
from datetime import datetime, timezone
from pathlib import Path

from src.config.storage_paths import REPORTS_DIR, ensure_storage_dirs


def clean(text: str) -> str:
    return textwrap.dedent(text).strip() + "\n"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(clean(content), encoding="utf-8")


def main() -> None:
    ensure_storage_dirs()

    package_dir = REPORTS_DIR / "aurum_v1_presentation_package"
    package_dir.mkdir(parents=True, exist_ok=True)

    write(package_dir / "README_DRAFT.md", """
    # AURUM — Institutional Portfolio Intelligence Platform

    AURUM is an institutional-style portfolio intelligence system combining quantitative optimization, regime detection, live market monitoring, AI research agents, governance controls, and portfolio operating workflows.

    ## Core Capabilities

    - CVaR optimization using Rockafellar-Uryasev linear programming via cvxpy
    - HMM regime detection using live-safe filtered probabilities
    - Anomaly detection using rolling z-score and Isolation Forest
    - Market provider abstraction for YFinance, Polygon, and Alpaca
    - Scheduled live refresh pipeline from market data to portfolio action
    - Digital twin stress scoring
    - AI research firm, investment committee, and CIO briefing layers
    - Portfolio Operating System
    - Official dashboard: `src/dashboard/institutional_command_center.py`

    ## Validation

    Run:

    ```bash
    python -m scripts.validate_platform_complete
    ```
    """)

    write(package_dir / "ARCHITECTURE_DIAGRAM.md", """
    # AURUM Architecture Diagram

    ```text
    Live Market Providers
            ↓
    Market Data + Feature Engine
            ↓
    Regime Detection + Anomaly Detection
            ↓
    Digital Twin + Risk Projection
            ↓
    AI Research Desk + Committee
            ↓
    Chief Investment Officer Agent
            ↓
    Portfolio Operating System
            ↓
    Institutional Command Center
    ```
    """)

    write(package_dir / "AURUM_WHITEPAPER_DRAFT.md", """
    # AURUM Whitepaper Draft

    ## 1. Executive Summary

    AURUM is an institutional-style portfolio intelligence platform built to integrate quantitative finance, live market monitoring, risk management, AI research workflows, and portfolio governance.

    ## 2. Quantitative Core

    AURUM includes a hardened CVaR optimization engine based on the Rockafellar-Uryasev linear programming formulation using cvxpy.

    The regime engine uses Hidden Markov Models and clearly separates filtered probabilities from smoothed probabilities. Live decisions use filtered probabilities only.

    Anomaly detection combines rolling z-scores with Isolation Forest.

    ## 3. Live Market Infrastructure

    AURUM uses a provider abstraction layer:

    - YFinanceProvider
    - PolygonProvider
    - AlpacaProvider

    The live refresh pipeline runs:

    ```text
    Market Data
    ↓
    Features
    ↓
    Regime
    ↓
    Anomaly Detection
    ↓
    Digital Twin Stress
    ↓
    Portfolio OS Action
    ```

    ## 4. Dashboard

    The official dashboard is:

    ```text
    src/dashboard/institutional_command_center.py
    ```

    ## 5. Conclusion

    AURUM v1.0 is a defensible institutional-style portfolio intelligence platform focused on quant credibility, live-market credibility, governance, and presentation readiness.
    """)

    write(package_dir / "RESUME_SUMMARY.md", """
    # Resume Summary — AURUM

    Built AURUM, an institutional-style portfolio intelligence platform integrating CVaR optimization, HMM regime detection, anomaly monitoring, live market refresh orchestration, AI research agents, governance controls, and a Streamlit command center.

    ## Resume Bullet

    Built AURUM, an institutional-style portfolio intelligence platform integrating CVaR optimization, HMM regime detection, anomaly monitoring, live market refresh orchestration, AI research agents, governance controls, and a Streamlit command center; consolidated validation and architecture for a defensible v1.0 system.
    """)

    write(package_dir / "PACKAGE_INDEX.md", f"""
    # AURUM v1.0 Presentation Package

    Generated at: {datetime.now(timezone.utc).isoformat()}

    Files:

    - README_DRAFT.md
    - ARCHITECTURE_DIAGRAM.md
    - AURUM_WHITEPAPER_DRAFT.md
    - RESUME_SUMMARY.md
    - PACKAGE_INDEX.md

    Status: generated
    """)

    print("=" * 80)
    print("AURUM V1 PRESENTATION PACKAGE GENERATED")
    print("=" * 80)
    print(f"Output directory: {package_dir}")
    print("=" * 80)


if __name__ == "__main__":
    main()