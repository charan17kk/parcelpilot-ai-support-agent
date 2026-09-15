# Architecture Note

## System shape

The application is a three-container Docker Compose stack:

- React + TypeScript + Vite frontend on port 5173.
- FastAPI backend on port 8000.
- PostgreSQL 16 with pgvector on port 5432.

The backend is the sole security boundary. The browser never connects directly to the database, vector index, OpenRouter, or raw data files.

## Agent design

A single LangGraph state graph alternates between an OpenRouter-hosted model and authorised tools. Obvious ID-based cancellation, service-credit, order-status, and ticket requests are routed directly to the correct safe tool before the model formats the evidence. The primary free model has two automatic fallbacks, and the graph caps LLM calls and tool steps. There is no multi-agent design because one bounded support workflow is easier to audit and demonstrate.

The model is used for intent interpretation, choosing tools, and explaining verified evidence. It is not trusted to calculate fees, decide data scope, or execute actions. Cancellation, service-credit, severity, and SLA logic are deterministic Python functions.

A deterministic final-output guard also prevents advisory cancellation or credit calculations from being described as already executed, even if the model phrases them that way.

## Tool design

| Tool | Type | Responsibility |
|---|---|---|
| `search_documents` | Read-only | Hybrid search over authorised policies, agreements, SOPs, and product guidance |
| `lookup_order` | Read-only | Fetch one authorised order and its account |
| `lookup_ticket` | Read-only | Fetch one authorised ticket, severity, and SLA assessment |
| `calculate_cancellation_outcome` | Deterministic | Apply order state, timing, and Northstar override |
| `calculate_service_credit_outcome` | Deterministic | Apply delay/fault rules and LumenWorks override |
| `prepare_escalation` | State proposal | Persist a pending action only; never execute it |

Confirmation is intentionally outside the LLM loop. `POST /actions/{id}/confirm` locks the pending row, checks owner, status, expiry, and account scope, then creates the escalation once. Repeating confirmation returns the same result.

## Document and structured-data handling

The ingestion command validates all expected filenames, records checksums, reads the workbook snapshot time, normalises timestamps to UTC, and stores source-sheet/row metadata. PyMuPDF extracts the PDFs page by page. Chunks retain title, page, effective dates, status, account scope, authority class, and checksum.

FastEmbed generates 384-dimensional `all-MiniLM-L6-v2` embeddings locally. Retrieval combines pgvector cosine distance and PostgreSQL full-text rank, then uses authority rank as a deterministic tie-breaker. No document content is embedded by OpenRouter during ingestion.

## Reliability and conflicts

Authority is explicit metadata, not a prompt-only convention:

1. Active customer agreement.
2. Current policy.
3. Current SOP.
4. Current product operations guide.
5. Historical ticket resolution as context only.
6. Deprecated policy excluded unless explicitly requested for comparison.

The agent receives this ordering, retrieved results carry authority labels, and deterministic calculators encode the known contract overrides. Missing business-hours calendars produce `human_review_required` rather than a fabricated SLA breach time. Missing fault attribution or cancellation timestamps similarly prevents confident promises.

## Access control

Demo authentication creates an opaque random session token, stores only its SHA-256 hash combined with a server-side pepper, and sends the token in an HttpOnly SameSite cookie. Users have roles and account scopes. Repositories add those scopes to account, order, ticket, document, and citation queries. A cross-account lookup appears as not found, which avoids leaking record existence.

Internal roles may access all records in the supplied snapshot. A production version should connect these roles to ParcelPilot SSO and finer team/region permissions.

## Major trade-offs

- PostgreSQL + pgvector avoids a separate vector service and supports transactional actions and reporting.
- Local FastEmbed keeps document ingestion free and avoids sending the source pack to an embeddings API.
- OpenRouter's free endpoints keep the demo cost-free but introduce rate limits, availability risk, and provider logging. A fast primary model, two fallbacks, deterministic tool routing, and an empty-response fallback reduce that risk, while safe 429/503 states remain explicit.
- Synchronous chat responses keep the assessment implementation compact. Streaming tool progress is a logical follow-up.
- Business-hours SLA dates are not guessed because the pack does not supply a holiday/calendar definition.
