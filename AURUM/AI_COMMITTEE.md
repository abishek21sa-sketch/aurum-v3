# AURUM Investment Research Council

The former AI Committee documentation is retained as a research-layer
description, but its authority is deliberately bounded. AURUM's research
agents summarize structured analytical artifacts for human review; they are
not portfolio optimizers, trade issuers, or production approvers.

## Inputs

Council roles may consume:

- observed market-data and provenance records;
- estimated regime states and transition diagnostics;
- MARS-CVaR objective, constraints, scenario, and solver evidence;
- baseline and chronological walk-forward results;
- stress, ablation, and sensitivity artifacts.

## Permitted outputs

The council may explain allocation changes, summarize regime evidence,
compare baselines, challenge assumptions, identify limitations, and draft a
research memo that cites its underlying artifacts.

## Prohibited outputs

Council agents may not invent returns or market events, alter solver outputs,
choose portfolio weights, issue trades, override a blocked decision, or change
`RESEARCH_ONLY` into `PAPER_TRADING`, `PROMOTED`, or `PRODUCTION`.

## Human-gated workflow

```text
Structured evidence
    -> Investment Research Council explanation
    -> human review
    -> independent optimization authorization and policy gates
    -> separate governed integration, if any
```

Optimization authorization means that the analytical input passed the
decision gate. Research promotion is an independent empirical question. The
current AURUM evidence is allowed to remain `RESEARCH_ONLY`, and this status
is shown as a legitimate research result rather than an application error.
