# AURUM Portfolio Operating System

## Purpose

The Portfolio Operating System is the central orchestration engine of AURUM.

Its responsibility is to coordinate all institutional investment workflows and transform research, risk analysis, governance controls, and committee decisions into a unified portfolio directive.

The Portfolio Operating System acts as the orchestration layer of the
platform. It emits governed research directives; it does not by itself send
orders, rebalance a live account, or promote a strategy to production.

---

# Mission

Provide a single operational workflow capable of running the complete investment process from research generation through portfolio recommendations and operating reports.

Primary Command

python -m src.portfolio_os.portfolio_operating_system

---

# Architectural Position

Market Data
↓
Research
↓
AURUM Investment Research Council
↓
Human Review
↓
Memory
↓
Decision Intelligence
↓
Governance
↓
Portfolio Operating System
↓
Learning
↓
Operating Report

The Portfolio Operating System sits above research and governance layers and below institutional reporting.

---

# Core Objectives

The Portfolio Operating System must:

- Coordinate institutional workflows
- Aggregate intelligence
- Enforce governance outcomes
- Generate portfolio directives
- Produce operating reports
- Maintain operational state
- Support auditability
- Support reliability monitoring

---

# Operating Cycle

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

Every operating cycle produces a complete institutional recommendation.

---

# Portfolio Operating System Components

## Portfolio State Machine

File

src/portfolio_os/portfolio_state_machine.py

Purpose

Controls workflow progression.

Responsibilities

- Track workflow state
- Validate transitions
- Coordinate operating stages
- Preserve operational status

Outputs

portfolio_state_machine.json

---

## Portfolio Director

File

src/portfolio_os/portfolio_director.py

Purpose

Generate the final institutional directive.

Responsibilities

- Aggregate research conclusions
- Evaluate governance status
- Interpret committee outcomes
- Generate portfolio instructions

Outputs

portfolio_directive.json

---

## Daily Portfolio Cycle

File

src/portfolio_os/daily_portfolio_cycle.py

Purpose

Coordinate the daily investment workflow.

Responsibilities

- Execute operating stages
- Generate cycle summaries
- Track daily activities

Outputs

daily_portfolio_cycle.json

---

## Portfolio Operating System Engine

File

src/portfolio_os/portfolio_operating_system.py

Purpose

Top-level orchestrator.

Responsibilities

- Execute complete workflow
- Aggregate results
- Produce final operating state
- Generate executive outputs

Outputs

portfolio_operating_system.json

---

# Workflow Stages

## Stage 1 — Research Collection

Inputs

- Research Desk Reports
- Market Intelligence
- Risk Assessments
- Digital Twin Outputs

Activities

- Gather research artifacts
- Evaluate market conditions
- Aggregate intelligence

Outputs

Research package

---

## Stage 2 — Committee Review

Inputs

- Research package
- Risk assessments

Activities

- Review recommendations
- Debate risks
- Generate committee decision

Outputs

- investment_view
- approval_status
- confidence

---

## Stage 3 — Memory Review

Inputs

- Historical decisions
- Institutional memory
- Prior outcomes

Activities

- Compare with previous decisions
- Retrieve relevant history
- Identify recurring patterns

Outputs

Memory context

---

## Stage 4 — Decision Intelligence

Inputs

- Research conclusions
- Committee outcomes
- Memory context

Activities

- Explain reasoning
- Generate confidence measures
- Build decision trace

Outputs

- decision_trace.json
- decision_reasoning.json
- decision_explanation.json

---

## Stage 5 — Governance Validation

Inputs

- Proposed actions
- Portfolio state

Checks

### Exposure Limits

Verify position constraints.

### Concentration Controls

Verify diversification.

### Liquidity Controls

Verify execution feasibility.

### Drawdown Controls

Verify capital preservation requirements.

### Compliance Controls

Verify policy adherence.

Outputs

Governance decision

---

## Stage 6 — Portfolio Directive

Inputs

- Governance status
- Committee status
- Decision intelligence

Activities

- Generate final recommendation
- Determine execution permission
- Produce institutional directive

Outputs

portfolio_directive.json

Example Fields

- action
- confidence
- rationale
- execution_permission

---

## Stage 7 — Learning Evaluation

Inputs

- Current cycle
- Historical outcomes

Activities

- Capture lessons
- Evaluate process quality
- Update institutional knowledge

Outputs

Learning artifacts

---

## Stage 8 — Operating Report

Inputs

- All workflow outputs

Activities

- Summarize institutional state
- Produce executive report
- Archive cycle information

Outputs

Operating reports

---

# State Management

The Portfolio Operating System maintains institutional state.

Examples

### Market State

- regime
- volatility
- stress

### Portfolio State

- allocations
- cash
- risk budget

### Governance State

- approval status
- escalation status

### Operational State

- workflow status
- readiness state

---

# Portfolio Directive Structure

Typical Directive

Status

COMPLETE

Execution Permission

allowed
or
blocked

Confidence

0.00 to 1.00

Recommendation

- Increase Risk
- Reduce Risk
- Hold
- Rebalance
- Escalate

---

# Integration Points

## Research Layer

Provides:

- market intelligence
- research reports

---

## Committee Layer

Provides:

- investment view
- approval status

---

## Memory Layer

Provides:

- institutional history
- decision memory

---

## Governance Layer

Provides:

- approvals
- restrictions
- escalations

---

## Reliability Layer

Provides:

- readiness status
- platform health

---

# Dashboard Integration

Portfolio Operating System results are displayed in:

AURUM Institutional Command Center

Pages

- Portfolio OS
- Overview
- Governance
- Reliability

Users can inspect:

- operating status
- directives
- confidence
- execution permissions

---

# Key Outputs

## portfolio_state_machine.json

Workflow state information.

---

## portfolio_directive.json

Institutional recommendation.

---

## daily_portfolio_cycle.json

Daily cycle summary.

---

## portfolio_operating_system.json

Complete operating system output.

---

# Reliability Requirements

The Portfolio Operating System is considered healthy when:

- Research artifacts exist
- Committee decisions exist
- Governance outputs exist
- Memory outputs exist
- Operating reports are generated

Failure of any critical dependency results in:

Execution Permission = blocked

---

# Operational Readiness

Readiness Conditions

- Database available
- Research available
- Committee available
- Governance available
- Reliability checks passing

Required Status

institutional_ready

---

# Design Goals

The Portfolio Operating System is designed to be:

- Reliable
- Auditable
- Scalable
- Deployable
- Maintainable
- Explainable
- Governed

---

# Current Phase Status

Phase 6A.1 Portfolio Operating System

Status: COMPLETE

Validation Status: PASS

Institutional Readiness: OPERATIONAL

---

# Completion State

The Portfolio Operating System serves as the executive control layer of AURUM.

It transforms market intelligence, committee decisions, governance controls, and institutional memory into a unified portfolio directive while maintaining full auditability and operational oversight.

The Portfolio Operating System is the operational heart of the AURUM Institutional Market Operating System.
