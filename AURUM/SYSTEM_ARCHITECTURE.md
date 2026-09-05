# AURUM System Architecture

## Overview

AURUM is an Institutional Market Operating System designed to run a complete investment workflow from market intelligence through portfolio governance and operating reports.

The platform combines:

- Market Data
- Research Intelligence
- AI Research Desk
- Investment Committee
- Decision Intelligence
- Governance
- Portfolio Management
- Digital Twin Simulation
- Reliability Monitoring
- Institutional Reporting

The objective is to provide a reliable, auditable, scalable, deployable, and maintainable operating system for portfolio management.

---

## Mission

Transform AURUM from a collection of quantitative research modules into a fully integrated Institutional Market Operating System.

The platform must be capable of:

- Daily operation
- Institutional governance
- Continuous monitoring
- Autonomous research support
- Human-supervised portfolio decisions
- Long-term learning and improvement

---

## Architectural Principles

### One Operating System

All major workflows must be executable through a single orchestration layer.

Primary command:

python -m src.portfolio_os.portfolio_operating_system

### One Dashboard

A single institutional dashboard acts as the official user interface.

Official entry point:

dashboard/official_dashboard.py

Delegates to:

src/dashboard/institutional_command_center.py

### Provider Independence

Market data infrastructure must support multiple providers.

Supported architecture:

MarketProvider
├── YFinanceProvider
├── PolygonProvider
└── AlpacaProvider

### Persistence First

Institutional state must be stored in durable databases rather than temporary files whenever possible.

### Governance Before Execution

No portfolio action should bypass governance and committee approval layers.

### Auditability

Every major decision must leave a permanent audit trail.

---

# High-Level Architecture

Market Data
↓
Database Layer
↓
Research Layer
↓
AI Research Desk
↓
Investment Committee
↓
Memory Layer
↓
Decision Intelligence
↓
Governance Layer
↓
Portfolio Operating System
↓
Reliability Layer
↓
Institutional Dashboard

---

# Core System Layers

## 1. Market Data Layer

Purpose:

Acquire and normalize market information.

Responsibilities:

- Live market feeds
- Historical data retrieval
- Provider abstraction
- Data validation
- Data normalization

Primary Modules:

src/market_data/

Outputs:

- market_ticks
- market_features
- live market snapshots

---

## 2. Database Layer

Purpose:

Institutional persistence.

Technologies:

- TimescaleDB
- PostgreSQL
- Redis

Core Tables:

- market_ticks
- market_features
- market_signals
- portfolio_state
- portfolio_decisions
- committee_decisions
- execution_log
- learning_events

Responsibilities:

- Durable storage
- Query support
- Historical analysis
- Event persistence

---

## 3. Research Layer

Purpose:

Generate market intelligence.

Responsibilities:

- Macro analysis
- Market structure analysis
- Regime analysis
- Portfolio analysis
- Risk analysis

Primary Modules:

src/research/

Outputs:

- Research packets
- Market intelligence reports
- Risk assessments

---

## 4. AI Research Desk

Purpose:

Coordinate multiple AI agents.

Agents:

- Macro Agent
- Market Structure Agent
- Regime Agent
- Risk Agent
- Portfolio Agent
- Digital Twin Agent

Responsibilities:

- Independent analysis
- Consensus generation
- Research packet creation

Outputs:

- AI research reports
- Daily research packets
- Committee inputs

---

## 5. Investment Committee Layer

Purpose:

Provide institutional decision oversight.

Responsibilities:

- Debate recommendations
- Evaluate risks
- Approve or reject actions
- Generate committee minutes

Outputs:

- committee_decisions.json
- investment_committee_minutes.json

---

## 6. Memory Layer

Purpose:

Preserve institutional knowledge.

Responsibilities:

- Session memory
- Portfolio memory
- Decision history
- Outcome tracking

Artifacts:

- institutional_memory_index.json
- institutional_memory_report.json

Benefits:

- Learning from prior decisions
- Historical reasoning traceability

---

## 7. Decision Intelligence Layer

Purpose:

Explain decisions.

Responsibilities:

- Decision trace generation
- Reasoning documentation
- Confidence scoring
- Recommendation explanations

Outputs:

- decision_trace.json
- decision_reasoning.json
- decision_explanation.json

---

## 8. Governance Layer

Purpose:

Prevent unsafe portfolio actions.

Responsibilities:

- Exposure controls
- Drawdown controls
- Concentration controls
- Liquidity controls
- Compliance enforcement

Primary Modules:

src/governance/

Outputs:

- compliance reports
- governance alerts
- governance escalations
- approval decisions

---

## 9. Portfolio Operating System

Purpose:

Coordinate the entire institutional workflow.

Primary Command:

python -m src.portfolio_os.portfolio_operating_system

Workflow:

Research
↓
Committee
↓
Memory
↓
Decision Intelligence
↓
Governance
↓
Portfolio Directive
↓
Learning
↓
Operating Report

Core Modules:

- portfolio_state_machine.py
- portfolio_director.py
- daily_portfolio_cycle.py
- portfolio_operating_system.py

Outputs:

- portfolio_directive.json
- daily_portfolio_cycle.json
- portfolio_operating_system.json
- portfolio_state_machine.json

---

## 10. Digital Twin Layer

Purpose:

Simulate future portfolio outcomes.

Capabilities:

- Monte Carlo simulation
- Stress testing
- Contagion analysis
- Historical replay
- Scenario matching

Primary Modules:

src/digital_twin/

Outputs:

- risk projections
- scenario reports
- simulation summaries

---

## 11. Reliability Layer

Purpose:

Continuously monitor platform health.

Responsibilities:

- Platform monitoring
- Service monitoring
- Runtime auditing
- Alert generation
- Readiness scoring

Checks:

- Market Data
- Redis
- TimescaleDB
- API
- Dashboard
- Committee
- Portfolio OS

Outputs:

- institutional_readiness_report.json
- runtime_integrity_audit.json
- governance_alerts.json

---

## 12. Institutional Dashboard

Purpose:

Provide a unified operational interface.

Official Dashboard:

dashboard/official_dashboard.py

Core Application:

src/dashboard/institutional_command_center.py

Pages:

- Overview
- Market
- Risk
- Optimization
- Portfolio Lab
- Strategy Research
- Execution
- Governance
- Institutional Readiness
- Runtime Integrity
- Memory
- AI CIO
- Control Tower
- System Health
- Portfolio OS
- Database
- Reliability

Responsibilities:

- Monitoring
- Investigation
- Reporting
- Institutional oversight

---

## Infrastructure Architecture

### Redis

Purpose:

Real-time event streaming.

Examples:

- market_ticks
- market_features
- market_signals
- risk_events
- optimizer_events
- portfolio_decisions

---

### TimescaleDB

Purpose:

Institutional time-series persistence.

Stores:

- market history
- signals
- portfolio states
- decisions

---

### FastAPI

Purpose:

API services.

Default Port:

8000

---

### Streamlit

Purpose:

Institutional dashboard.

Default Port:

8501

---

### Docker

Purpose:

Deployment and portability.

Services:

- redis
- timescaledb
- api
- dashboard
- portfolio_os
- reliability

Primary Command:

docker compose up --build

---

# Operational Workflow

Daily Workflow

Market Data
↓
Research Desk
↓
Committee
↓
Memory
↓
Decision Intelligence
↓
Governance
↓
Portfolio Directive
↓
Portfolio Operating System
↓
Reliability Validation
↓
Operating Report

---

# Current Phase Status

Phase 6A.1 Portfolio Operating System
Status: COMPLETE

Phase 6A.2 Production Market Data Layer
Status: COMPLETE

Phase 6A.3 Database Layer
Status: COMPLETE

Phase 6A.4 Unified Dashboard
Status: COMPLETE

Phase 6A.5 Reliability Layer
Status: COMPLETE

Phase 6A.6 Deployment Layer
Status: COMPLETE

---

# Institutional Readiness

Current Readiness Score:

100 / 100

Deployment Status:

Docker Compose Ready

Dashboard Status:

Operational

Database Status:

Operational

Reliability Status:

Operational

Portfolio Operating System Status:

Operational

---

# Completion State

At completion of Phase 6A, AURUM operates as an Institutional Market Operating System.

The platform provides:

- Unified operations
- Institutional governance
- Database persistence
- Reliability monitoring
- Containerized deployment
- AI-assisted research
- Portfolio decision support
- Continuous learning

This architecture serves as the foundation for Phase 6B Institutional Intelligence.
