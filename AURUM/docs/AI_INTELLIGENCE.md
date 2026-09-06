# AURUM Intelligence

AURUM Intelligence is the product-facing AI research layer. It reads the current MARS-CVaR decision payload and produces an executive brief, decision rationale, risk challenge, evidence-change conditions, and a bounded Ask AURUM response.

## Default mode

The default mode is `LOCAL_GROUNDED`. It is deterministic, uses only the current repository-native evidence payload, and does not transmit portfolio data outside the runtime. This mode is the official offline acceptance path.

AI remains read-only and human-gated:

- it cannot change solver outputs;
- it cannot authorize orders or enable execution;
- it cannot promote research;
- it must label the evidence boundary and research-only state.

## Optional live model

An operator may explicitly enable an OpenAI overlay for the brief and Ask AURUM by setting all of the following in the process environment:

```powershell
$env:AURUM_AI_PROVIDER = "openai"
$env:AURUM_AI_LIVE_ENABLED = "true"
$env:AURUM_AI_EXTERNAL_APPROVED = "true"
$env:OPENAI_API_KEY = "<managed-secret>"
$env:AURUM_AI_TIMEOUT_SECONDS = "20"
```

`AURUM_AI_MODEL` can override the configured model. Without all three explicit flags/credentials, AURUM stays in local grounded mode. The live overlay is an interpretation layer only; it does not change the decision payload or governance state. API keys must come from the operator's secret manager or process environment and must never be committed to the repository.

Live evaluation is a separate action. Set `AURUM_AI_RUN_LIVE_EVAL=true` only
for an operator-approved smoke/evaluation run. Readiness, control-plane, and
observability requests never trigger a paid or external model call implicitly.
Live responses are bounded, JSON-shaped, and retain the local execution and
research-promotion safety fields.

## Runtime endpoints

- `GET /api/ai/status` — active provider mode and safety boundary.
- `GET /api/ai/brief` — grounded CIO brief for the current control values.
- `GET /api/ai/ask?question=...` — bounded answer against the current evidence.
- `GET /v1/platform/ai-evaluation` — grounding and safety contract evaluation.

The product UI exposes these capabilities in the `AURUM Intelligence` workspace and on the Overview screen.
