# ParcelPilot Assist

ParcelPilot Assist is a trust-aware customer-support agent for the ParcelPilot interview assessment. It supports a customer mode with strict account isolation and an authorised internal mode for support staff. Answers combine the supplied policies, customer agreements, product documentation, orders, accounts, and tickets. Any proposed escalation remains pending until the user explicitly confirms it.

## What is implemented

- Customer and internal chat contexts with mocked role-based login.
- Backend-enforced account and document access control.
- A LangGraph tool-calling workflow using NVIDIA Nemotron 3 Ultra through OpenRouter.
- Six agent tools: document search, order lookup, ticket lookup, cancellation calculation, service-credit calculation, and escalation preparation.
- Hybrid RAG using local FastEmbed embeddings, PostgreSQL full-text search, and pgvector.
- Explicit source precedence: customer agreement → current policy/SOP → current product guide → historical context.
- Deprecated policy exclusion by default and warnings around historical ticket resolutions.
- A two-phase escalation action: prepare first, then confirm or cancel through a separate API call.
- Source citations, confidence labels, and tool-use summaries in the UI.
- Responsive desktop, tablet, and mobile layouts.

## Cost and privacy

PostgreSQL, pgvector, FastEmbed, React, FastAPI, and all application libraries are free and open source. The selected OpenRouter model ID ends in `:free`, but the free endpoint can be rate-limited, changed, or withdrawn by the provider. Do not send confidential or personal production data to the free endpoint. The supplied assessment pack is synthetic.

No LangSmith project, key, tracing, or paid observability service is used. LangSmith may appear as a transitive package of LangChain, but the application does not configure or call it.

## Prerequisites

- Docker Desktop with Linux containers and Docker Compose.
- The seven assessment files in `data/raw/` with their original filenames.
- An OpenRouter API key authorised to call `nvidia/nemotron-3-ultra-550b-a55b:free`.

No local Node.js, Python, PostgreSQL, or embedding model installation is required when using Docker.

## First-time setup

1. Confirm the data directory contains exactly the six PDFs and `ParcelPilot_Assessment_Data.xlsx`.
2. Copy `backend/.env.example` to `backend/.env`.
3. Set `OPENROUTER_API_KEY=<your-openrouter-key>` in `backend/.env`. Never commit or paste the key into chat.
4. Start the stack:

   ```powershell
   docker compose up --build -d
   ```

5. Import and index the supplied pack:

   ```powershell
   docker compose exec backend python -m scripts.ingest_data_pack --reset
   ```

6. Verify readiness:

   ```powershell
   Invoke-RestMethod http://localhost:8000/api/v1/ready
   ```

7. Open [http://localhost:5173](http://localhost:5173). API documentation is available at [http://localhost:8000/api/docs](http://localhost:8000/api/docs).

The first ingestion downloads the free local embedding model into a Docker volume. Later imports reuse that cache.

## Demo identities

All demo identities use the password `ParcelPilotDemo!` by default.

| Persona | Email | Scope |
|---|---|---|
| Northstar customer | `northstar@demo.parcelpilot.com` | ACCT-001 only |
| LumenWorks customer | `lumenworks@demo.parcelpilot.com` | ACCT-002 only |
| Beacon customer | `beacon@demo.parcelpilot.com` | ACCT-003 only |
| Support agent | `support@demo.parcelpilot.com` | All supplied accounts |
| Operations manager | `ops@demo.parcelpilot.com` | All supplied accounts |

Change `DEMO_USER_PASSWORD` before ingesting if a different local demo password is required.

## Recommended demo requests

- `Can Northstar cancel ORD-1001 without a cancellation fee? Explain why.`
- `A pickup is late because of carrier fault. Should ORD-2002 get a service credit?`
- `Investigate TKT-501 and tell me its severity and applicable SLA.`
- `What guidance should we give for the bulk upload failure in TKT-502?`
- `Create an escalation for ORD-1001 because the customer needs human review.`

For the last prompt, the agent may prepare an escalation, but no escalation exists until **Confirm & create** is pressed.

## Useful commands

```powershell
# Service status
docker compose ps

# Backend logs
docker compose logs -f backend

# Rebuild after frontend package.json/package-lock.json changes
docker compose up --build -d --force-recreate --renew-anon-volumes frontend

# Re-import the candidate pack
docker compose exec backend python -m scripts.ingest_data_pack --reset

# Run deterministic business-rule tests in the backend container
docker compose exec backend python -m unittest discover -s tests -v

# Stop containers while preserving the database and model cache
docker compose down
```

## Project documents

- [Implementation plan](PROJECT_PLAN.md)
- [Architecture note](docs/ARCHITECTURE.md)
- [Product note](docs/PRODUCT_NOTE.md)
- [Demo video script](docs/DEMO_SCRIPT.md)
- [AI tool usage](docs/AI_TOOL_USAGE.md)
- [Free-tier deployment guide](docs/DEPLOYMENT.md)

## Security notes

- `data/raw/`, `.env`, and local model/runtime artifacts are git-ignored.
- Authentication uses an opaque token in an HttpOnly cookie; raw tokens are never stored.
- Customer filtering is applied in repositories and action services, not left to model prompts.
- Document retrieval applies the same account scope before semantic or lexical ranking.
- The state-changing tool creates only a pending action. Execution uses an owner-scoped, locked, idempotent confirmation path.
- For a real production deployment, replace demo identities with company SSO, set secure cookies, rotate the session pepper, restrict CORS, use managed secrets, and review provider data-retention terms.
