# AURUM Data Pipeline

## Purpose

The AURUM Data Pipeline is responsible for collecting, processing, storing, distributing, and preserving institutional market intelligence across the platform.

The pipeline ensures that every portfolio decision can be traced back to underlying market information and research inputs.

---

# Pipeline Overview

Market Providers
↓
Market Data Layer
↓
Feature Engineering
↓
Database Layer
↓
Research Layer
↓
AI Research Desk
↓
Committee
↓
Decision Intelligence
↓
Governance
↓
Portfolio Operating System
↓
Dashboard & Reporting

---

# Stage 1 — Market Data Acquisition

## Objective

Collect raw market information from external providers.

## Supported Providers

- YFinanceProvider
- PolygonProvider
- AlpacaProvider

## Data Types

### Equities

Examples:

- SPY
- QQQ
- DIA

### Fixed Income

Examples:

- TLT
- Treasury instruments

### Commodities

Examples:

- GLD
- Oil
- Copper

### Volatility

Examples:

- VIX

### Crypto

Examples:

- BTC-USD
- ETH-USD

---

# Stage 2 — Market Data Normalization

## Objective

Convert provider-specific data into a common institutional format.

Example Fields

- timestamp
- ticker
- price
- volume
- source

## Benefits

- Provider independence
- Consistent downstream processing
- Easier migration between vendors

---

# Stage 3 — Feature Engineering

## Objective

Transform raw prices into analytical signals.

Examples

### Returns

Daily returns

### Volatility

Rolling volatility estimates

### Momentum

Price trend calculations

### Drawdown

Portfolio stress measurements

### Correlation

Cross-asset relationships

### Risk Signals

Institutional risk indicators

---

# Stage 4 — Real-Time Event Distribution

## Objective

Distribute market intelligence throughout the platform.

Technology:

Redis Streams

## Core Streams

### market_ticks

Raw market updates

### market_features

Calculated analytics

### market_signals

Research and regime signals

### risk_events

Risk alerts

### optimizer_events

Optimization triggers

### portfolio_decisions

Portfolio actions

---

# Stage 5 — Database Persistence

## Objective

Preserve institutional state.

Technology Stack

- TimescaleDB
- PostgreSQL
- Redis

---

# Core Institutional Tables

## market_ticks

Stores normalized market updates.

Example Fields

- timestamp
- ticker
- price
- volume
- source

---

## market_features

Stores derived analytics.

Example Fields

- volatility
- momentum
- correlation
- trend signals

---

## market_signals

Stores higher-level intelligence.

Examples

- regime decisions
- market alerts
- research conclusions

---

## portfolio_state

Stores current portfolio conditions.

Examples

- allocations
- cash levels
- risk budget

---

## portfolio_decisions

Stores approved actions.

Examples

- rebalance actions
- allocation changes
- recommendations

---

## committee_decisions

Stores committee outputs.

Examples

- approvals
- restrictions
- investment views

---

## execution_log

Stores execution activity.

Examples

- orders
- fills
- execution reports

---

## learning_events

Stores institutional learning outcomes.

Examples

- lessons
- decision reviews
- performance feedback

---

# Stage 6 — Research Intelligence

## Objective

Transform data into actionable insight.

Inputs

- Market ticks
- Features
- Signals
- Portfolio state

Outputs

- Research reports
- Risk assessments
- Market outlooks

---

# Stage 7 — AI Research Desk

## Objective

Generate institutional analysis.

Agents

### Macro Agent

Economic analysis

### Market Structure Agent

Internal market behavior

### Regime Agent

Market regime classification

### Risk Agent

Risk evaluation

### Portfolio Agent

Portfolio assessment

### Digital Twin Agent

Scenario evaluation

---

# Stage 8 — Committee Review

## Objective

Apply institutional oversight.

Committee evaluates:

- Research conclusions
- Risk conditions
- Portfolio recommendations

Outputs

- Investment view
- Approval status
- Committee minutes

---

# Stage 9 — Decision Intelligence

## Objective

Explain why decisions were made.

Outputs

- Decision trace
- Reasoning report
- Explanation report

Benefits

- Auditability
- Transparency
- Governance support

---

# Stage 10 — Governance Controls

## Objective

Prevent unsafe portfolio actions.

Checks

### Exposure Limits

Position constraints

### Drawdown Limits

Capital preservation

### Concentration Limits

Diversification requirements

### Liquidity Controls

Execution feasibility

### Compliance Controls

Institutional policy enforcement

---

# Stage 11 — Portfolio Operating System

## Objective

Coordinate the complete workflow.

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

Outputs

- portfolio_directive.json
- daily_portfolio_cycle.json
- operating reports

---

# Stage 12 — Dashboard Distribution

## Objective

Present institutional information.

Official Dashboard

dashboard/official_dashboard.py

Primary Interface

src/dashboard/institutional_command_center.py

Dashboard Sections

- Markets
- Risk
- Portfolio
- Governance
- Execution
- Digital Twin
- Committee
- Learning
- Portfolio OS
- Database
- Reliability

---

# Reliability Monitoring

The data pipeline is continuously monitored.

Checks include:

- Provider health
- Redis health
- Timescale health
- Dashboard health
- Committee health
- Portfolio OS health

Outputs

- readiness reports
- alerts
- audit reports

---

# Daily Operating Cycle

Start of Day

Market Data Collection
↓
Feature Generation
↓
Research Generation
↓
Committee Review
↓
Governance Validation
↓
Portfolio Directive
↓
Operating Report

End of Day

Learning Evaluation
↓
Memory Update
↓
Institutional Archive

---

# Design Goals

The AURUM Data Pipeline is designed to be:

- Reliable
- Auditable
- Scalable
- Deployable
- Maintainable
- Provider Independent
- Institutionally Governed

---

# Completion State

The data pipeline provides a complete path from market information to portfolio decisions while maintaining institutional auditability and operational reliability.

It serves as the central nervous system of the AURUM Institutional Market Operating System.
