# AURUM AI and ML System

AURUM separates deterministic quantitative computation from interpretation,
learning experiments, and optional external model calls. This prevents a
language model from silently changing a portfolio result or turning an
unverified narrative into an execution instruction.

## 1. System layers

~~~text
Governed inputs
    -> MARS-CVaR decision engine
    -> evidence assembler and provenance
    -> deterministic AURUM Intelligence
    -> research-operations committee
    -> human review and promotion gate
~~~

The quantitative engine owns weights, CVaR, constraints, scenarios, and solver
status. The AI layer reads those outputs and explains or challenges them. The
research-operations layer creates structured hypotheses and committee records;
it does not grant execution authority.

## 2. Grounded AI mode

The default provider is LOCAL_GROUNDED. It uses the current repository-native
decision evidence, data class, scenario class, and governance state to produce:

- an executive brief;
- a decision rationale;
- a risk challenge;
- conditions that would change the conclusion;
- a bounded answer to an operator question.

The generated text must carry the evidence boundary. It cannot change solver
outputs, alter target weights, enable orders, or change RESEARCH_ONLY into a
production state. The API surfaces are /api/ai/status, /api/ai/brief,
/api/ai/ask, and /v1/platform/ai-evaluation.

## 3. Optional live model overlay

An OpenAI overlay can be explicitly enabled with provider, approval, live-mode,
model, timeout, and secret settings. The overlay is an interpretation adapter;
the local payload remains the source of truth. The implementation must:

1. build a minimized evidence context;
2. exclude secrets and unnecessary portfolio data;
3. request bounded JSON-shaped output;
4. validate the response schema and length;
5. retain provider, model, time, and error metadata;
6. fall back to the local grounded brief if the external call fails;
7. never make external calls during readiness or acceptance checks implicitly.

## 4. Research-operations loop

The governed loop is:

~~~text
observe -> validate -> challenge -> decide -> learn
~~~

The current deterministic fixture reads the MARS-CVaR decision, public-data
manifest, synthetic ML validation, walk-forward evidence, and risk scenarios.
It then records:

- hypothesis ID and current status;
- validation checks and their evidence references;
- Bull, Bear, Risk, and Judge committee positions;
- whether the Judge engaged the strongest Bear objection;
- reusable research memories;
- learning and decay metadata;
- next actions and blockers;
- Mission Control and digital-twin status.

The current contract is intentionally conservative: an equal or inferior
baseline result remains REVIEW, and an unresolved validation item blocks
promotion.

## 5. Synthetic ML laboratory

The 10,000-row dataset is generated for deterministic engineering coverage and
is labeled SIMULATED_SYNTHETIC_DATA. It is not historical, customer, causal,
or realized-performance data. Cases include normal observations, trends,
volatility clusters, stress, recovery, liquidity shocks, regime boundaries,
missing features, stale timestamps, duplicates, outliers, nonpositive prices,
label noise, and schema drift.

Each row contains a timestamp, regime/scenario metadata, price/return-like
features, liquidity/volatility proxies, and a bounded target used by the
baseline tasks. The manifest records row counts, case counts, schema, seed,
generator version, and SHA-256 hashes.

## 6. Implemented baseline models

### Chronological ridge regression

For feature matrix X, target vector y, and regularization gamma, the ridge
coefficient is:

~~~text
beta = (X^T X + gamma I)^(-1) X^T y
~~~

The implementation fits only on earlier observations and evaluates on later
observations. Scaling statistics are fit on the training window, not the full
dataset. The artifact records the split, seed, feature list, coefficients,
metrics, and leakage checks.

### Nearest-centroid classifier

For each class c, the training centroid is:

~~~text
mu_c = (1 / |Ic|) * sum(i in Ic) xi
~~~

An evaluation point is assigned to the class with the smallest declared
distance to its training centroid. The classifier is a transparent baseline
for regime-like labels, not a claim of market predictability.

### Evaluation contract

The baseline report includes sample counts, chronological split boundaries,
MAE/RMSE or classification metrics where applicable, class coverage, missing
value behavior, and schema validation. Acceptance is about reproducibility and
leakage control; it is not a performance guarantee.

## 7. ML risk controls

The system is designed to reject or flag:

- random shuffling when time order matters;
- training features derived from future rows;
- duplicate or stale timestamps;
- schema drift and missing-feature cases;
- nonfinite values and invalid prices;
- evaluation on an empty or undersized window;
- silent synthetic-to-public data substitution;
- claims that a synthetic result is external evidence.

For a stronger model program, add nested time-series validation, a frozen final
holdout, feature lineage, calibration, drift monitoring, uncertainty estimates,
model cards, and independent review.

## 8. AI/ML governance boundary

AI and ML can prioritize research, summarize evidence, challenge assumptions,
and propose the next experiment. They cannot place orders, modify customer
accounts, bypass human review, or promote a strategy merely because a model
metric improved. Every promoted research result needs a reproducible artifact,
independent validation, and an explicit approval record.
