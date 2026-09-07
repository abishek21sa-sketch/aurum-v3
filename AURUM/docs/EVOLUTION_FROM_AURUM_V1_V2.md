# Evolution from AURUM and AURUM V2

This comparison is based on local snapshots of the two earlier repositories
and describes capability boundaries rather than claiming that every optional
integration was production-ready.

## AURUM original strengths

The original AURUM repository provided a broad application and operations
surface: mission-control views, provider and agent health, digital-twin and
paper-trading scaffolding, a copilot surface, and a wider execution-oriented
application shape. Its main lesson was that a serious product needs observable
operations, not only a research notebook.

The consolidated system keeps those ideas as explicit concepts but tightens the
boundary around them: execution is disabled in the reference path, every
external source is labeled, and operational status is exposed through
machine-readable contracts.

## AURUM V2 strengths

AURUM V2 contributed the research-firm perspective: hypotheses, Bull, Bear,
Risk, and Judge debate, statistical validation, research memory, an alpha
registry, knowledge-graph ideas, persistence, and continuous-learning
workflows. Its main lesson was that one backtest number is not enough; research
must record why a result survived challenge and what was learned when it
failed.

The consolidated system brings that structure into the quantitative product as
a governed research-operations loop with stable artifacts and UI/API surfaces.
It also keeps the conservative research-only boundary instead of allowing a
research narrative to become an execution command.

## What this release adds

| Area | Earlier pattern | Consolidated AURUM v3 approach |
| --- | --- | --- |
| Quantitative core | Separate portfolio and research identities | MARS-CVaR decision engine with explicit bridge and lineage |
| Research workflow | Strong ideas spread across scripts and services | Observe, validate, challenge, decide, learn contract |
| AI | Copilot or provider-specific research calls | Local grounded AI by default; optional bounded overlay |
| Validation | Backtest/statistical utilities with external dependencies | Deterministic chronological acceptance plus promotion gate |
| Data | Live-provider assumptions and mixed paths | Reference, public, synthetic, and customer evidence classes |
| Operations | Mission-control and health concepts | Read-only readiness, observability, role-policy, and audit contracts |
| Governance | Execution-oriented scaffolding | Fail-closed execution and research-promotion separation |
| Reproducibility | Environment/service-dependent checks | Offline deterministic fixture, manifests, hashes, and release verifier |
| ML engineering | Research models and experiments | 10,000-row labeled synthetic lab with edge cases and leakage checks |
| Product | Multiple surfaces across two projects | One decision workspace with Intelligence and Research Operations views |

## What is not being claimed

The consolidation does not turn simulated evidence into market truth, or an AI
brief into independent model validation. The previous repositories remain
useful references, but provider credentials, database deployments, customer
controls, live-data entitlements, security testing, and independent validation
still require authentic external evidence.

## Migration map

- Quantitative logic: AURUM/src/optimization/ and AURUM/src/institutional/.
- AI interpretation: AURUM/src/institutional/ai_intelligence.py and the product
  runtime routes.
- Research workflow: AURUM/src/institutional/research_operations.py.
- Public evidence: AURUM/scripts/ingest_public_data.py and
  AURUM/artifacts/public_data/.
- ML laboratory: AURUM/scripts/generate_synthetic_ml_dataset.py and the
  synthetic validation artifacts.
- Historical V2 reference: AURUM-v2/ is retained for comparison and
  compatibility review; it is not the source of truth for the consolidated
  product contracts.
