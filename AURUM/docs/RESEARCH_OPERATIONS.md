# AURUM Research Operations

AURUM now exposes a governed research-firm loop inspired by the original AURUM and AURUM V2 repositories:

`observe → validate → challenge → decide → learn`

The first release is deterministic and evidence-grounded. It uses the current MARS-CVaR decision, public-data manifest, synthetic-ML validation, walk-forward artifact, and risk scenarios as inputs. It does not imply that a research ticket is a live model run, a trading signal, or an investment recommendation.

## Current surfaces

- `/api/research/operations` — complete research-operations payload and lineage.
- `/api/research/feed` — hypothesis queue and validation summary.
- `/api/research/memory` — structured lessons and reusable constraints.
- `/api/research/committee` — Bull/Bear/Risk/Judge challenge record.
- `/api/mission-control/status` — request-driven cycle and component health.
- `/api/digital-twin/status` — reference scenarios with evidence class.
- `/download/research-operations.json` — portable machine-readable artifact.

## Boundary

The research operations fixture is intentionally fail-closed:

- `execution_enabled=false`
- `research_promotion=RESEARCH_ONLY`
- paper trading is disabled
- synthetic and simulated evidence remain explicitly labeled
- equal or inferior baseline performance does not pass incremental-uplift review
- the Judge must record whether it engaged the strongest Bear objection

The next research phase can add an optional persisted ledger, provider-backed model committee, and independently frozen evaluation windows. Those adapters must preserve the same schemas, lineage, evidence classes, and human approval boundary.
