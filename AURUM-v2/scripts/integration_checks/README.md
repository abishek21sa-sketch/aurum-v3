# External integration checks

These files are executable smoke/integration checks retained from the original AURUM V2 research-firm repository. They are intentionally **not** pytest unit tests because several require live external systems or credentials (PostgreSQL, FRED, Anthropic, SEC/market-data services).

Run them explicitly only when the corresponding dependency/service is configured. Normal `pytest` discovery is reserved for deterministic, assertion-bearing tests and must not make live network calls during collection.
