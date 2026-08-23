# Five-Minute Demo Script

## 0:00–0:45 — Problem and product

ParcelPilot support staff currently search agreements, policies, product documentation, tickets, and operational records by hand. This demo provides customer and internal support modes while treating contracts, freshness, privacy, and uncertainty deliberately.

Show the login screen and point out the two demo identities.

## 0:45–1:35 — Architecture

Show the repository or a simple architecture slide:

- React/Vite frontend.
- FastAPI + LangGraph backend.
- PostgreSQL/pgvector for relational records, chat/action state, full-text search, and vectors.
- Local FastEmbed ingestion.
- NVIDIA Nemotron 3 Ultra through OpenRouter.

Explain that account filtering and action confirmation are backend controls, not model instructions.

## 1:35–2:35 — Customer example

Log in as Northstar and ask:

`Can Northstar cancel ORD-1001 without a cancellation fee? Explain why.`

Open the tool timeline and citations. Explain that the order is BOOKED and not picked up, while Northstar's active agreement waives the normal after-30-minute fee. Point out the confidence badge and account-scoped source drawer.

## 2:35–3:35 — Internal multi-step example

Log in as support and ask:

`A pickup is late because of carrier fault. Should ORD-2002 get a service credit?`

Explain that the agent looks up the order, finds LumenWorks, reads its agreement and the SOP, uses the workbook snapshot time, and applies the contract's four-hour threshold and fixed INR 300 amount rather than the default formula.

Then briefly ask about `TKT-502` to show that the current product guide overrides the incorrect historical resolution.

## 3:35–4:20 — Confirmation and privacy

Ask the Northstar customer mode to create an escalation for `ORD-1001`. Show the pending confirmation card and emphasise that nothing has happened yet. Confirm it and show the generated escalation reference.

Mention the verified privacy test: a Northstar session receives a generic 404 for LumenWorks account data.

## 4:20–5:00 — Decisions and next steps

Summarise the authority order, deprecated/historical handling, deterministic calculations, and human-review fallback. State that the next priorities are an evaluation gate, proactive issue dashboard, SSO, and a real ticketing connector.

Use grounded first-contact resolution rate as the primary product metric, with zero cross-account leaks and zero unconfirmed actions as guardrails.
