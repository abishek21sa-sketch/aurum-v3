# AURUM Operations Manual

## Purpose

This document provides operational procedures for running, monitoring, validating, and maintaining the AURUM Institutional Market Operating System.

It serves as the primary reference for day-to-day platform operations. The
current product release is an offline-first research surface: human review is
required and no broker orders are emitted by the product runtime.

---

# Platform Overview

AURUM is an Institutional Market Operating System.

Core Capabilities:

- Market Data Infrastructure
- Research Intelligence
- AI Research Desk
- Investment Research Council
- Memory Layer
- Decision Intelligence
- Governance
- Portfolio Operating System
- Reliability Monitoring
- Institutional Dashboard
- Containerized Deployment

---

# Official Entry Points

## Portfolio Operating System

Command

python -m src.portfolio_os.portfolio_operating_system

Purpose

Runs the complete institutional workflow.

---

## Official Dashboard

Command

streamlit run dashboard/official_dashboard.py --server.port 8501

Purpose

Launches the Institutional Command Center.

---

## Docker Deployment

Command

docker compose up --build

Purpose

Starts the institutional deployment stack.

---

# Dashboard Access

Default URL

http://localhost:8501

Official Dashboard

dashboard/official_dashboard.py

Core Dashboard

src/dashboard/institutional_command_center.py

---

# Core Services

## Redis

Purpose

Real-time event streaming.

Port

6379

Status Check

docker compose ps

---

## TimescaleDB

Purpose

Institutional persistence layer.

Port

5434

Status Check

docker compose ps

---

## API

Purpose

Service and integration layer.

Port

8000

Status Check

docker compose ps

---

## Dashboard

Purpose

Institutional monitoring and oversight.

Port

8501

Status Check

docker compose ps

---

# Daily Startup Procedure

Step 1

Start infrastructure

docker compose up --build

---

Step 2

Verify services

docker compose ps

Expected Services

- redis
- timescaledb
- api
- dashboard

---

Step 3

Verify dashboard

Open

http://localhost:8501

---

Step 4

Verify reliability

python -m scripts.validate_phase6a5_reliability_layer

Expected Result

Institutional Readiness Score: 100

Status: institutional_ready

---

# Portfolio Operating System Workflow

Command

python -m src.portfolio_os.portfolio_operating_system

Workflow

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

---

# Validation Procedures

## Reliability Validation

Command

python -m scripts.validate_phase6a5_reliability_layer

Purpose

Verify platform health.

---

## Deployment Validation

Command

python -m scripts.validate_phase6a6_deployment_layer

Purpose

Verify deployment configuration.

---

## Documentation Validation

Command

python -m scripts.validate_phase6a7_documentation_layer

Purpose

Verify institutional documentation coverage.

---

# Health Monitoring

## Platform Health

Checks

- Database
- Dashboard
- Portfolio OS
- Committee
- Market Data
- Reliability Systems

---

## Service Health

Checks

- Redis
- TimescaleDB
- API
- Dashboard

---

## Runtime Audit

Checks

- Critical artifacts
- System readiness
- Institutional status

---

# Log Inspection

## Dashboard Logs

Command

docker compose logs dashboard --tail=50

---

## API Logs

Command

docker compose logs api --tail=50

---

## Reliability Logs

Command

docker compose logs reliability --tail=50

---

## All Services

Command

docker compose logs

---

# Data Persistence

## Redis

Volume

redis_data

Purpose

Event stream persistence.

---

## TimescaleDB

Volume

aurum_timescale_data

Purpose

Institutional database persistence.

---

# Database Tables

Core Tables

- market_ticks
- market_features
- market_signals
- portfolio_state
- portfolio_decisions
- committee_decisions
- execution_log
- learning_events

---

# Operational Artifacts

## Portfolio OS

Location

results/portfolio_os/

Artifacts

- portfolio_directive.json
- daily_portfolio_cycle.json
- portfolio_operating_system.json
- portfolio_operating_system_report.txt

---

## Research

Location

results/research/

Artifacts

- committee_decision.json
- investment_committee_minutes.json
- research packets

---

## Reliability

Location

results/reliability/

Artifacts

- readiness reports
- health reports
- audit reports

---

# Troubleshooting

## Dashboard Not Starting

Verify

docker compose ps

Check

docker compose logs dashboard --tail=50

---

## Database Connection Failure

Verify

docker compose ps

Check TimescaleDB status

Expected

healthy

---

## Reliability Failure

Run

python -m scripts.validate_phase6a5_reliability_layer

Review failed checks.

---

## Portfolio OS Failure

Run

python -m src.portfolio_os.portfolio_operating_system

Review generated output.

---

# Shutdown Procedure

Command

docker compose down

Purpose

Gracefully stop all services.

---

# Recovery Procedure

Step 1

Start infrastructure

docker compose up --build

---

Step 2

Validate deployment

python -m scripts.validate_phase6a6_deployment_layer

---

Step 3

Validate reliability

python -m scripts.validate_phase6a5_reliability_layer

---

Step 4

Open dashboard

http://localhost:8501

---

# Current Institutional Status

Phase 6A.1 Portfolio Operating System

Status: COMPLETE

---

Phase 6A.2 Market Data Layer

Status: COMPLETE

---

Phase 6A.3 Database Layer

Status: COMPLETE

---

Phase 6A.4 Unified Dashboard

Status: COMPLETE

---

Phase 6A.5 Reliability Layer

Status: COMPLETE

---

Phase 6A.6 Deployment Layer

Status: COMPLETE

---

Phase 6A.7 Documentation Layer

Status: COMPLETE

---

# Completion State

AURUM is operational as an Institutional Market Operating System.

The platform provides:

- Unified workflow orchestration
- Institutional governance
- Durable persistence
- Reliability monitoring
- Containerized deployment
- AI-assisted research
- Committee oversight
- Portfolio directives
- Executive reporting

This manual serves as the operational reference for maintaining and running the AURUM platform.
