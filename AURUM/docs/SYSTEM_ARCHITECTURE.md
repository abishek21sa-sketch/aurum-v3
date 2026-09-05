# AURUM System Architecture

## Official Runtime Architecture

The official runtime architecture is organized under:

src/

All production research and infrastructure development should happen inside this directory.

---

## Core System Layers

### Data Ingestion

Responsible for:
- downloading market data
- loading historical datasets
- preparing raw market inputs

Directory:

src/data_ingestion/

---

### Features Layer

Responsible for:
- return calculations
- rolling statistics
- volatility features
- market indicators
- engineered alpha features

Directory:

src/features/

---

### Regime Layer

Responsible for:
- market regime detection
- transition modeling
- regime forecasting
- stability estimation

Directory:

src/regimes/

Outputs stored in:

data/regimes/

---

### Signals Layer

Responsible for:
- generating market allocation signals
- directional positioning
- signal aggregation

Directory:

src/signals/

---

### Optimization Layer

Responsible for:
- portfolio construction
- regime-aware allocation
- probabilistic allocation
- confidence-adjusted optimization
- efficient frontier analysis

Directory:

src/optimization/

---

### Risk Layer

Responsible for:
- factor exposure analysis
- stress testing
- rolling beta monitoring
- dynamic risk budgeting
- portfolio diagnostics

Directory:

src/risk/

---

### Backtesting Layer

Responsible for:
- historical strategy simulation
- allocation replay
- regime-aware backtesting
- performance evaluation

Directory:

src/backtesting/

---

### Analytics Layer

Responsible for:
- attribution analysis
- portfolio health monitoring
- rolling analytics
- diagnostics

Directory:

src/analytics/

---

### AI Layer

Responsible for:
- LLM orchestration
- executive summaries
- structured reasoning
- AI portfolio copilot functionality

Directory:

src/ai/

---

### Reporting Layer

Responsible for:
- executive reports
- portfolio summaries
- exported research outputs

Directory:

src/reporting/

---

### Execution Layer

Responsible for:
- future live allocation systems
- execution simulation
- live deployment interfaces

Directory:

src/execution/

---

## Pipeline Goal

The full Phase 1 system should eventually execute through:

python -m src.pipelines.run_phase1_market_pulse

---

## Infrastructure Principles

- use src/ as the official architecture
- avoid duplicate storage paths
- centralize regime outputs into data/regimes/
- maintain modular separation between layers
- keep research reproducible
- maintain deterministic pipelines where possible

---

## Legacy Layer

The app/ directory represents an earlier prototype architecture.

It should not be used for future core development.
