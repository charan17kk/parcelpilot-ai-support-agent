# ParcelPilot AI Customer Support — Implementation Plan

**Status:** Ready for implementation  
**Plan updated:** 22 August 2026  
**Workspace:** `C:\projects\CalQuity`  
**Scope of this document:** Technical and product specification only. It does not contain application implementation.

---

## 1. Executive Summary

ParcelPilot is a B2B logistics platform whose support team currently searches customer agreements, policies, operating procedures, product documentation, account data, order data, and historical tickets manually. The project will create an AI support application that performs those searches through controlled tools and produces evidence-backed answers.

The application will support two contexts:

1. A customer-facing chatbot restricted to the authenticated customer's account.
2. An internal support chatbot for authorized ParcelPilot staff, with broader but role-scoped investigation access.

The primary additional client problem addressed in the P0 submission is **Trust and Reliability**. Answers must deliberately account for customer-specific contract overrides, current versus deprecated policies, incomplete information, conflicting sources, and potentially incorrect historical ticket resolutions.

The chatbot will not behave as an unrestricted autonomous AI. It will use a constrained, auditable workflow with allowlisted tools:

- Document retrieval.
- Account, order, and ticket lookup.
- Deterministic calculations.
- Confirmation-gated escalation creation.

The selected primary LLM is **Liquid LFM2.5 through OpenRouter's hosted API**, with inclusionAI Ling and OpenRouter's free model router as fallbacks. The model chain remains configurable through backend environment variables so it can be changed without source changes.

The guaranteed development environment is local Docker Desktop using PostgreSQL with PGVector. A hosted deployment is P1 because the assessment prefers a hosted link, but the implementation must remain fully usable locally without paid infrastructure.

---

## 2. Current Readiness and Locked Decisions

### 2.1 Verified local environment

The following setup was verified before implementation:

- WSL default version: 2.
- WSL version: 2.5.9.0.
- Docker Desktop: 4.87.0.
- Docker Engine: 29.7.2, Linux/AMD64.
- Docker Compose: 5.4.0.
- `docker run --rm hello-world` completed successfully.
- Git is installed.
- The workspace is not yet initialized as a Git repository.
- A complete OpenRouter API key has been created and stored privately by the user.
- The API key has not yet been tested and must never be displayed or logged.

No local NVIDIA GPU, CUDA, NVIDIA Container Toolkit, Ollama, or n8n installation is required.

### 2.2 Verified data pack

The following seven non-empty files exist under `data/raw/` with the expected names:

1. `01_Support_Policy_v3_CURRENT.pdf`
2. `02_Support_Policy_v2_DEPRECATED.pdf`
3. `03_Cancellation_and_Service_Credit_SOP_v4.pdf`
4. `04_Product_Operations_Guide_and_Known_Issues.pdf`
5. `05_Northstar_Logistics_Enterprise_Agreement.pdf`
6. `06_LumenWorks_Service_Agreement.pdf`
7. `ParcelPilot_Assessment_Data.xlsx`

All six PDFs have valid `%PDF-` file headers. The Excel workbook opens as a valid XLSX ZIP archive. Document contents and workbook sheet mappings have not yet been analyzed; that analysis is the first data implementation task.

### 2.3 Locked technology decisions

| Area | Decision |
|---|---|
| Frontend | React, TypeScript, Vite, Tailwind CSS, shadcn/ui |
| Routing | React Router |
| Server state | TanStack Query |
| Small client UI state | Zustand |
| Forms/validation | React Hook Form and Zod where useful |
| Charts | Recharts for P1 operational insights |
| Backend | Python 3.12, FastAPI, Pydantic |
| ORM/migrations | SQLAlchemy 2.x async and Alembic |
| Database | PostgreSQL with PGVector |
| Local infrastructure | Docker Compose |
| LLM gateway | OpenRouter |
| LLM | `liquid/lfm-2.5-2.6b:free` with free fallbacks |
| Embeddings | Local `sentence-transformers/all-MiniLM-L6-v2` |
| Agent framework | LangChain integrations plus LangGraph orchestration |
| PDF parsing | PyMuPDF, subject to license review; `pypdf` fallback |
| XLSX parsing | OpenPyXL |
| Authentication | Seeded demo users with opaque server-side sessions |
| Additional problem | Trust and Reliability as P0 |
| Proactive issue detection | P1 |
| Automatic LLM fallback | Not included |
| LangSmith | Explicitly excluded |
| n8n | Not required |
| Paid services | None required |

### 2.4 Important OpenRouter constraints

- The free endpoint is appropriate for an interview prototype, not guaranteed production service.
- Free-model requests are rate-limited. The application must minimize LLM calls and handle HTTP 429 cleanly.
- Target no more than three LLM calls for one user request.
- Free OpenRouter models support tool calling but do not guarantee strict JSON through `response_format`; all model/tool output must be validated server-side.
- Free endpoints may log usage and are not appropriate for confidential production data.
- Use only the supplied assessment dataset and do not enter real customer data.
- Retrieve locally and send only the small number of relevant excerpts and structured facts needed for an answer; never send the complete data pack to the model.

---

## 3. Requirements Analysis

### 3.1 What must be built

The P0 implementation must provide:

1. Seeded demo authentication for customer and internal users.
2. Backend-enforced account and role authorization.
3. Customer and internal natural-language chat modes.
4. Ingestion of all supplied PDFs and workbook sheets.
5. Page-aware document retrieval with citations.
6. Structured account, order, and ticket lookups.
7. Deterministic cancellation, service-credit, lateness, and SLA calculations where supported by the data.
8. A bounded multi-step tool-calling agent.
9. Explicit source reliability and conflict rules.
10. An escalation action requiring explicit confirmation.
11. Conversation, citation, safe tool-event, pending-action, and audit persistence.
12. Loading, empty, error, success, conflict, and confirmation UI states.
13. Responsive desktop, tablet, and mobile behavior.
14. Repository, setup, architecture, product, AI-usage, deployment, and demo documentation.

### 3.2 Selected product scope

#### P0

- Customer chat.
- Internal support chat.
- Trust and reliability behavior.
- Document and structured data tools.
- Multi-step workflows.
- Confirmation-gated escalation.
- Citations and source-quality indicators.
- Docker-based local deployment.

#### P1

- Proactive internal insights dashboard.
- SLA risk and overdue detection.
- Recurring complaint and cross-account issue detection.
- Internal ticket queue and details.
- Confirmation-gated ticket updates.
- Hosted deployment on a genuinely available free tier.

#### P2

- OCR for scanned documents.
- Saved internal filters.
- Insight acknowledgement and resolution.
- Feedback analytics.
- Exportable investigation summaries.
- Production identity provider and real operational integrations.

### 3.3 Explicit exclusions

- Real carrier cancellation APIs.
- Real refund or service-credit issuance.
- Real helpdesk/CRM integration.
- Public registration and password reset.
- Multi-agent architecture.
- Web search or external ParcelPilot knowledge.
- Fine-tuning.
- LangSmith or paid observability.
- Paid vector database.
- Autonomous actions without confirmation.

---

## 4. Functional Requirements

| ID | Requirement | Persona | Trigger | Expected result | Priority |
|---|---|---|---|---|---|
| FR-001 | Ingest the candidate pack | Developer | Run ingestion | PDFs and workbook records are validated, normalized, and indexed with provenance | P0 |
| FR-002 | Extract dataset snapshot time | System | Workbook ingestion | README snapshot time becomes the reference for all relative-time calculations | P0 |
| FR-003 | Demo login/logout | All users | Submit credentials/logout | Secure server session created/revoked | P0 |
| FR-004 | Enforce account and role access | All users | Any protected request/tool | Only permitted records and agreement chunks are returned | P0 |
| FR-005 | Create/list/resume chats | All users | Chat navigation | Owner-scoped conversation state is persisted | P0 |
| FR-006 | Natural-language support | All users | Submit message | Supported answer, safe limitation, or pending action is returned | P0 |
| FR-007 | Search supplied documents | Agent | Policy/contract/SOP/known-issue question | Ranked authorized excerpts with page citations | P0 |
| FR-008 | Look up operational data | Agent | Account/order/ticket question | Authorized canonical records with workbook provenance | P0 |
| FR-009 | Calculate outcomes deterministically | Agent | Entitlement/lateness/SLA query | Calculation result, inputs, missing facts, and applied rule references | P0 |
| FR-010 | Handle multi-step requests | Agent | Question needs multiple sources | Bounded tool sequence and consolidated answer | P0 |
| FR-011 | Apply source hierarchy | Agent | Multiple sources available | Applicable agreements/current sources outrank deprecated/history sources | P0 |
| FR-012 | Detect conflicts/uncertainty | Agent | Evidence disagrees or is incomplete | Qualified answer or escalation, never unsupported confidence | P0 |
| FR-013 | Show citations | All users | Answer rendered | Document/page and structured-record evidence is visible | P0 |
| FR-014 | Treat historical ticket resolutions as context only | Agent | Similar tickets retrieved | Historical guidance is labeled and never independently determines entitlement | P0 |
| FR-015 | Show safe tool activity | All users | Agent executes | UI displays tool names and safe summaries, not chain-of-thought | P0 |
| FR-016 | Prepare escalation | All users | User asks or evidence is unresolved | Immutable pending action preview is created | P0 |
| FR-017 | Confirm/cancel escalation | Action owner | Press Confirm/Cancel | Exactly one authorized escalation is created or proposal is cancelled | P0 |
| FR-018 | Audit sensitive activity | System | Login/tool denial/action execution | Safe structured audit record is persisted | P0 |
| FR-019 | Supplied-data-only behavior | Agent | Any question | No web/general knowledge is presented as ParcelPilot policy | P0 |
| FR-020 | Proactive issue detection | Internal user | Open dashboard | Ranked recurring, urgent, unusual, or cross-account issues | P1 |
| FR-021 | Internal ticket queue | Internal user | Search/filter tickets | Paginated role-authorized ticket list/detail | P1 |
| FR-022 | Confirmed ticket update | Internal user | Confirm proposal | Supported ticket fields update transactionally and are audited | P1 |
| FR-023 | Submission documentation | Reviewer | Open repository | Complete setup, architecture, product, AI usage, and demo guidance | P0 |

---

## 5. Non-Functional Requirements

| ID | Requirement | Acceptance target | Priority |
|---|---|---|---|
| NFR-001 | Privacy isolation | No customer can retrieve another account's data through APIs, tools, citations, chat history, or actions | P0 |
| NFR-002 | Evidence-backed trust | Every material policy/contract conclusion cites supporting evidence or explicitly escalates | P0 |
| NFR-003 | Reproducible time logic | Every relative-time result uses the workbook snapshot time | P0 |
| NFR-004 | Action safety | Operational actions are explicit, immutable, expiring, authorized, transactional, and idempotent | P0 |
| NFR-005 | Bounded AI use | Maximum tool/LLM steps, retrieval size, timeouts, and retries are configured | P0 |
| NFR-006 | Maintainability | API, domain rules, tools, retrieval, persistence, and UI are separated | P0 |
| NFR-007 | Portability | Complete local run through Docker Compose with no paid dependency | P0 |
| NFR-008 | Observability | Request IDs, structured logs, tool runs, ingestion reports, and audit events | P0 |
| NFR-009 | Accessibility | Keyboard operation, semantic labels, visible focus, sufficient contrast | P1 |
| NFR-010 | Responsive design | Core chat usable from 320 px width through desktop | P0 |
| NFR-011 | Failure safety | LLM/retrieval failures never become fabricated confident answers | P0 |
| NFR-012 | Provenance | Every imported record/chunk records source file and sheet row/page | P0 |
| NFR-013 | Performance | Structured lookup target <1 s; retrieval target <2 s; LLM response target reasonable for free endpoint | P1 |

---

## 6. User Roles and Authorization

### Customer

- Assigned to exactly one demo account initially.
- Can see only that account's orders, tickets, agreement, chats, citations, and escalations.
- Can create and confirm an escalation for the assigned account.
- Cannot access internal routes or arbitrary account IDs.

### Support agent

- Can use internal chat for authorized accounts.
- Can search relevant accounts, orders, tickets, agreements, policies, SOPs, and known issues.
- Can create escalations.
- Can view P1 operational insights.

### Operations manager

- Includes support-agent read permissions.
- Can view cross-account P1 insights.
- Can propose and confirm allowlisted P1 ticket changes.
- Cannot change agreements, policies, authentication, refunds, credits, or carrier systems.

### Developer/ingestion operator

- Local command-line responsibility only.
- Loads and validates the supplied pack.
- No public ingestion UI or API.

### Authorization enforcement rules

Authorization must be enforced in all of the following layers:

1. FastAPI route dependency.
2. Application service.
3. Repository/database query.
4. Agent tool wrapper.
5. Citation lookup.
6. Action confirmation/execution.

Customer account scope is injected from authenticated server context. A model-supplied or user-supplied account ID is never trusted as authorization input.

---

## 7. User Flows

### UF-001 — Login

1. User opens `/login`.
2. User enters seeded credentials.
3. Frontend validates required fields and calls `POST /api/v1/auth/login`.
4. Backend verifies Argon2 hash and active status.
5. Backend creates an opaque session and sets an HTTP-only cookie.
6. Customer routes to `/chat`; internal user routes to `/internal/chat`.
7. Invalid credentials return a generic error without revealing account existence.

### UF-002 — Customer cancellation question

1. Customer asks whether an order can be cancelled without a fee.
2. Agent extracts the order identifier.
3. Structured tool retrieves the order using the authenticated account predicate.
4. Document tool retrieves only that account's agreement plus current cancellation sources.
5. Reliability service checks agreement scope, current/deprecated status, and effective dates.
6. Deterministic calculation evaluates relevant order timing/status facts.
7. Agent returns the supported conclusion, explanation, citations, snapshot time, and confidence.
8. Missing, foreign, ambiguous, or conflicting evidence produces safe not-found/uncertainty behavior and optional escalation.

### UF-003 — Service-credit question

1. User describes a carrier-caused pickup delay, optionally with an order ID.
2. Structured lookup retrieves verified timestamps/fault attribution when an ID is present.
3. Document search retrieves agreement, SOP, and current policy clauses.
4. Calculation service computes delay duration and evaluates documented prerequisites.
5. The answer distinguishes general guidance from verified account-specific eligibility.
6. Issuing a credit is outside scope; the chatbot offers escalation where appropriate.

### UF-004 — Conflicting sources

1. Retrieval finds current and deprecated policies or two apparently valid conflicting sources.
2. Deprecated policy is excluded from the primary rule and may be mentioned only to explain the conflict.
3. If a valid agreement clearly overrides a general rule, the agreement applies within its subject/account/effective period.
4. If valid authoritative sources remain in conflict, confidence becomes low.
5. The assistant cites the conflict and offers escalation instead of choosing arbitrarily.

### UF-005 — Escalation confirmation

1. User requests escalation or the agent recommends it.
2. Agent action tool creates only a pending, immutable proposal.
3. UI shows reason, priority, related records, and exact effect.
4. User presses Confirm or Cancel.
5. Confirm API revalidates identity, ownership, scope, action status, expiry, and targets.
6. Transaction creates exactly one escalation and audit event.
7. Duplicate confirmation returns the original result.
8. Cancelled or expired proposals cannot execute.

### UF-006 — Internal investigation

1. Internal user opens `/internal/chat`.
2. User asks about a customer, order, ticket, SLA, or known issue.
3. Agent combines authorized structured data, agreement/policy/SOP/guide evidence, and calculations.
4. Answer includes internal-safe detail, tool trace, citations, confidence, and recommended next step.
5. Supported operational changes still require confirmation.

### UF-007 — Proactive issue dashboard (P1)

1. Internal user opens `/internal/insights`.
2. Backend calculates or reads snapshot-based insights.
3. UI ranks SLA risks, recurring categories, surges, known-issue matches, and cross-account problems.
4. User opens an insight to see affected records and deterministic detection rationale.
5. User can open internal chat with the insight context attached.

### UF-008 — Unauthorized identifier probing

1. Customer asks for another customer's order/agreement.
2. Tool receives trusted customer scope separately from the prompt.
3. Repository query includes the mandatory account predicate.
4. API/tool returns generic not found without confirming foreign data exists.
5. Safe audit event records the denied lookup category.

---

## 8. Screens and Pages

| Screen | Route | Main components | API/data | Required states | Priority |
|---|---|---|---|---|---|
| Login | `/login` | Credentials form, demo account hints, submit | Login/me | Validation, loading, generic error, success redirect | P0 |
| Customer Chat | `/chat` | Conversation list, thread, composer, tool trace, citations, confidence, action card | Chats/messages/actions/sources | First-use empty, running, partial, error, retry, confirmation, success | P0 |
| Customer Chat Detail | `/chat/:chatId` | Persisted thread | Chat detail | Loading, unauthorized/not found, pending action | P0 |
| Internal Chat | `/internal/chat` | Shared chat UI, internal context controls, snapshot badge | Same chat APIs with internal role | Same plus forbidden scope | P0 |
| Internal Chat Detail | `/internal/chat/:chatId` | Persisted internal thread | Chat detail | Loading, unauthorized/not found | P0 |
| Source Drawer | Overlay | Excerpt, title, page, status, authority label | Source endpoint | Loading, missing, redacted, success | P0 |
| Insights Dashboard | `/internal/insights` | Summary cards, filters, ranked list, charts | Insights summary | Loading, empty, partial error, success | P1 |
| Insight Detail | `/internal/insights/:id` | Rationale, affected entities, open-in-chat | Insight detail | Loading, stale, missing, forbidden | P1 |
| Ticket Queue | `/internal/tickets` | Search, filters, pagination, SLA/severity chips | Ticket list | Loading, empty filters, error | P1 |
| Ticket Detail | `/internal/tickets/:id` | Ticket/order/account detail, history warning, action proposal | Ticket detail/actions | Loading, missing, forbidden, action states | P1 |
| Forbidden | `/forbidden` | Safe permission message | None | Role-aware navigation | P0 |
| Not Found | `*` | Recovery navigation | None | Role-aware return | P0 |

---

## 9. Technology Stack and Rationale

### Frontend

- React + TypeScript + Vite: fast, standard, and interview-friendly.
- Tailwind CSS + shadcn/ui: rapid accessible UI composition without paid components.
- React Router: role-aware application routes.
- TanStack Query: server state, mutations, retries, and cache invalidation.
- Zustand: only local UI state such as drawers, sidebar, and unsent drafts.
- React Hook Form + Zod: login and filter validation.
- Recharts: free P1 dashboard charts.

### Backend

- Python + FastAPI + Pydantic: best single backend for AI, document processing, Excel ingestion, and typed APIs.
- SQLAlchemy async + Alembic: relational data access and migrations.
- LangChain integrations: OpenRouter-compatible model/tool and retrieval adapters.
- LangGraph: bounded multi-step state, branching, tool calling, retries, and action proposal workflow.
- Standard Python logging: free local observability without LangSmith.

### Database

- PostgreSQL fits relational accounts, orders, tickets, actions, auditing, transactions, and reporting.
- PGVector is appropriate because PostgreSQL is already required and RAG genuinely needs semantic retrieval.
- PostgreSQL full-text search complements vector similarity for identifiers and exact policy terms.
- MongoDB and ChromaDB are not required.

### AI

- OpenRouter exposes an OpenAI-compatible API and requires only one backend key.
- Liquid LFM2.5 is selected for low-latency tool use, with Ling and OpenRouter's free router providing availability fallbacks.
- Model choice alone is not the trust mechanism. Authorization, retrieval, calculations, precedence, citations, and confirmation are deterministic backend responsibilities.
- Local embeddings keep bulk document processing out of the hosted LLM.

---

## 10. High-Level Architecture

```text
React browser client
        |
        | HTTPS + HTTP-only session cookie
        v
FastAPI application
        |
        +-- Authentication and authorization
        +-- Chat/application services
        +-- LangGraph support agent
        |      +-- Document search tool
        |      +-- Structured lookup tool
        |      +-- Deterministic calculation tool
        |      +-- Confirmation-gated escalation tool
        |      +-- Reliability/conflict adjudication
        |
        +-- P1 operational insights
        +-- Audit and structured logging
        |
        +--------------------+
        |                    |
        v                    v
PostgreSQL + PGVector   OpenRouter API
local Docker            OpenRouter free model chain

Offline ingestion:
PDFs -> page text -> chunks -> local embeddings -> PGVector
XLSX -> validated mappings -> accounts/orders/tickets/snapshot
```

### Trust boundaries

- The model never accesses PostgreSQL directly.
- The model never generates or executes arbitrary SQL.
- The model never receives session tokens, password hashes, or unrelated customer records.
- Tool inputs and outputs use strict Pydantic schemas.
- Authorization filters are applied before retrieval/ranking.
- Retrieved documents are untrusted data, never instructions.
- Action execution requires a trusted confirmation state that the model cannot create.
- Chain-of-thought/reasoning details are not persisted or displayed.

---

## 11. Project Folder Structure

Create this structure only after adding `.gitignore` protections:

```text
CalQuity/
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   │   ├── auth/
│   │   │   ├── chat/
│   │   │   ├── citations/
│   │   │   ├── insights/
│   │   │   ├── layout/
│   │   │   └── ui/
│   │   ├── hooks/
│   │   ├── pages/
│   │   ├── routes/
│   │   ├── services/
│   │   ├── store/
│   │   ├── types/
│   │   ├── utils/
│   │   ├── main.tsx
│   │   └── index.css
│   ├── .env.example
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── dependencies/
│   │   │   └── routes/
│   │   ├── agent/
│   │   │   ├── graph/
│   │   │   ├── prompts/
│   │   │   ├── schemas/
│   │   │   └── tools/
│   │   ├── auth/
│   │   ├── calculations/
│   │   ├── config/
│   │   ├── db/
│   │   │   ├── migrations/
│   │   │   ├── models/
│   │   │   └── repositories/
│   │   ├── ingestion/
│   │   │   ├── documents/
│   │   │   ├── mappings/
│   │   │   └── workbook/
│   │   ├── insights/
│   │   ├── observability/
│   │   ├── reliability/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   ├── scripts/
│   │   ├── ingest_data_pack.py
│   │   ├── seed_demo_users.py
│   │   └── validate_ingestion.py
│   ├── tests/
│   │   ├── actions/
│   │   ├── authorization/
│   │   ├── calculations/
│   │   └── reliability/
│   ├── .env.example
│   ├── alembic.ini
│   └── pyproject.toml
├── data/
│   ├── raw/                  # already present; never commit
│   ├── README.md
│   └── manifest.example.yml
├── docs/
│   ├── architecture.md
│   ├── product-note.md
│   ├── ai-tool-usage.md
│   ├── demo-script.md
│   └── deployment.md
├── .gitignore
├── docker-compose.yml
├── PROJECT_PLAN.md
└── README.md
```

Do not introduce unused folders or a second backend language.

---

## 12. Frontend Architecture

### State ownership

Use TanStack Query for current user, chats, messages, source details, actions, tickets, and insights. Use Zustand only for sidebar state, citation drawer selection, unsent message draft, and local filter preferences.

### Chat response contract

An assistant message must be able to render:

- Answer text.
- Confidence: high, medium, low, or unresolved.
- Workbook snapshot timestamp.
- Source citations.
- Safe tool activity.
- Conflict/missing-information notices.
- Recommended next step.
- Optional pending action card.
- Retryable or terminal error information.

### Tool visibility

Display safe summaries such as:

- Looking up order `ORD-1001`.
- Searching the authenticated customer's agreement.
- Checking the current cancellation procedure.
- Calculating pickup delay.
- Preparing an escalation.

Never display model chain-of-thought, raw prompts, raw database rows, SQL, embeddings, or unrestricted internal metadata.

### Chat transport

Prefer a streaming POST response using server-sent event framing over `fetch` so the UI can show tool events while a run is active. Required event types:

- `run_started`
- `tool_started`
- `tool_completed`
- `citation_added`
- `answer_delta` or final `answer`
- `action_pending`
- `run_completed`
- `run_failed`

If streaming materially blocks P0 delivery, a synchronous response containing the final safe tool trace is acceptable, but the running UI must still show a clear progress state.

### Rendering/security

- Sanitize Markdown and disallow arbitrary HTML.
- Treat citations as application components rather than model-created links.
- Keep confirmation controls visually distinct.
- Disable duplicate sends and duplicate confirmations.
- Use an application-level error boundary.

---

## 13. Backend Architecture

### Layer responsibilities

- API routes: HTTP parsing, auth dependency, serialization, status codes.
- Application services: use-case orchestration and transactions.
- Repositories: authorization-scoped SQL only.
- Domain/calculations: deterministic business and time logic.
- Reliability service: evidence precedence, applicability, conflicts, confidence.
- Agent: intent/tool selection and response explanation.
- Tool wrappers: typed interface between agent and backend services.
- Ingestion: offline parsing, normalization, validation, and indexing.

### Authorization context

Every protected repository/tool call receives a trusted context containing:

- User ID.
- Role.
- Permitted account IDs or authorized internal scope.
- Active dataset snapshot ID/time.
- Request ID.
- Chat ID where relevant.

### Deterministic calculations

Each calculation result must contain:

- Result and units.
- Structured input facts.
- Missing required facts.
- Applied rule/source identifiers.
- Snapshot time.
- Assumptions, if any.
- Human-review requirement.

The LLM explains these results; it does not independently perform business-critical arithmetic.

---

## 14. Database Design

Use UUID primary keys, UTC timestamps, explicit foreign keys, database constraints, and indexes. Preserve workbook external identifiers separately from internal UUIDs.

### `dataset_snapshots`

- `id`: UUID primary key.
- `snapshot_at`: required timestamptz from workbook README.
- `source_filename`: required text.
- `source_sha256`: required text.
- `is_active`: boolean; one active snapshot.
- `imported_at`: required timestamptz.
- `metadata`: optional JSONB.

### `accounts`

- `id`: UUID primary key.
- `external_id`: required, unique within snapshot.
- `name`: required.
- `status`: required.
- `plan_or_tier`: optional.
- `default_support_sla_hours`: optional numeric.
- `dataset_snapshot_id`: required FK.
- `source_sheet`, `source_row`: required provenance.
- `raw_payload`: JSONB for unmapped workbook fields.
- Created/updated timestamps.

Indexes: external ID; status; snapshot.

### `orders`

- `id`: UUID primary key.
- `external_id`: required, unique within snapshot.
- `account_id`: required FK.
- `carrier`, `service_level`: optional.
- `status`: required.
- `booked_at`, `pickup_scheduled_at`, `pickup_actual_at`: optional timestamptz.
- `cancellation_requested_at`, `cancelled_at`: optional timestamptz.
- `carrier_fault`: nullable boolean when unknown.
- `shipment_charge`: optional non-negative numeric.
- `currency`: optional three-character code.
- Snapshot/source provenance and raw payload.
- Created/updated timestamps.

Indexes: account/external ID; account/status; scheduled pickup; snapshot.

### `tickets`

- `id`: UUID primary key.
- `external_id`: required, unique within snapshot.
- `account_id`: required FK.
- `order_id`: optional FK.
- `subject`: required.
- `description`, `category`: optional.
- `severity`, `status`: required.
- `created_at_source`: required source timestamp.
- `first_response_at`, `resolved_at`, `sla_due_at`: optional.
- `historical_resolution`: optional and explicitly non-authoritative.
- Snapshot/source provenance and raw payload.
- Created/updated timestamps.

Indexes: account/external ID; account/status; severity; SLA due; category/created time.

### `users`

- `id`: UUID primary key.
- `email`: required case-insensitive unique value.
- `password_hash`: required.
- `display_name`: required.
- `role`: customer, support_agent, or operations_manager.
- `is_active`: default true.
- Created/updated timestamps.

### `user_account_scopes`

- `id`: UUID primary key.
- `user_id`: required FK.
- `account_id`: required FK.
- `scope`: read or support.
- Unique user/account constraint.
- Created/updated timestamps.

### `auth_sessions`

- `id`: UUID primary key.
- `user_id`: required FK.
- `token_hash`: required unique value; plaintext token is never stored.
- `expires_at`: required.
- `revoked_at`: optional.
- `created_at`, `last_seen_at`.

Indexes: token hash; user; expiry.

### `documents`

- `id`: UUID primary key.
- `filename`, `title`.
- `document_type`: policy, SOP, product_guide, agreement.
- `version`: optional.
- `status`: current, deprecated, unknown.
- `effective_from`, `effective_to`: optional.
- `account_id`: required for agreements, null for general sources.
- `authority_class` and documented authority rank.
- `sha256`: unique.
- `page_count`, `ingestion_status`, `ingested_at`.
- `metadata`: JSONB.

Indexes: type/status; account/type; effective dates; SHA.

### `document_chunks`

- `id`: UUID primary key.
- `document_id`: required FK.
- `chunk_index`: required.
- `page_start`, `page_end`.
- `section_heading`: optional.
- `content`: required.
- `token_count`: required.
- `search_vector`: PostgreSQL full-text vector.
- `embedding`: PGVector vector(384).
- `metadata`: JSONB.
- `created_at`.

Constraints/indexes: unique document/chunk; GIN full-text index; HNSW/appropriate vector index; document/page index.

### `chat_sessions`

- `id`: UUID primary key.
- `owner_user_id`: required FK.
- `mode`: customer or internal.
- `title`: optional.
- `account_context_id`: required in customer mode; optional internal context.
- `status`: active or archived.
- Created/updated timestamps.

### `chat_messages`

- `id`: UUID primary key.
- `chat_session_id`: required FK.
- `role`: user, assistant, or system_event.
- `content`: text.
- `confidence`: optional enum.
- `snapshot_id`: FK.
- `run_status`: pending, completed, failed, awaiting_confirmation.
- `error_code`: optional.
- `created_at`.

### `message_citations`

- `id`: UUID primary key.
- `message_id`: required FK.
- `document_chunk_id`: optional FK.
- `entity_type`, `entity_id`: optional structured reference.
- `citation_label`: required.
- `reliability_class`: required.
- `supports_claim`: optional short description/index.
- `created_at`.

Exactly one document or structured citation target must be present.

### `tool_runs`

- `id`: UUID primary key.
- Chat/message IDs.
- `tool_name`.
- Safe input/output summaries.
- Status and error category.
- Start/end timestamps and duration.
- Request ID.

Raw sensitive tool payloads are not persisted by default.

### `pending_actions`

- `id`: UUID primary key.
- `owner_user_id`, `chat_session_id`.
- `action_type`: create_escalation initially; update_ticket in P1.
- Target account/entity identifiers.
- Validated `proposed_payload` JSONB.
- Human-readable immutable display summary.
- Status: pending, confirmed, executed, cancelled, expired, failed.
- Expiry, confirmation, execution timestamps.
- Result entity reference.
- Idempotency key.
- Created/updated timestamps.

### `escalations`

- `id`: UUID primary key.
- Unique human-readable reference.
- `account_id`, `created_by_user_id`, `source_chat_session_id`.
- Optional related order/ticket IDs.
- `reason`, `summary`, `priority`.
- `status`: open, acknowledged, resolved, cancelled.
- Evidence references JSONB.
- Created/updated timestamps.

### `audit_events`

- `id`: UUID primary key.
- Request ID and actor user ID.
- Event type.
- Resource type/ID.
- Outcome.
- Safe metadata JSONB.
- Created timestamp.

Indexes: actor/time; event/time; resource.

### `ingestion_runs`

- Run ID and timestamps.
- Status.
- Input manifest and checksums.
- Counts imported/skipped/failed.
- Validation errors/warnings.
- Parser and embedding versions.
- Activated snapshot ID where successful.

### `issue_insights` and `ticket_events` (P1)

Persist insight type, score, severity, time window, affected counts, detection parameters, evidence references, status, and calculation time. Ticket events retain before/after safe values and the originating confirmed action.

### Workbook mapping rule

The workbook's real sheet and column names must be inspected before migrations/import mappings are finalized. Map them explicitly into the canonical entities above, preserve unmapped fields in `raw_payload`, and fail snapshot activation when critical identifiers, relationships, or README snapshot time are missing.

---

## 15. API Specification

All application routes use `/api/v1`. JSON errors contain a stable `code`, safe `message`, `requestId`, optional field details, and retryability.

### Authentication

#### `POST /api/v1/auth/login`

- Public.
- Body: email and password.
- Validates bounded fields.
- Creates opaque session cookie and returns safe user/role/scope data.
- Errors: 400, 401, 429, 500.

#### `POST /api/v1/auth/logout`

- Authenticated.
- Revokes session and clears cookie.
- Returns 204.

#### `GET /api/v1/auth/me`

- Authenticated.
- Returns safe profile, role, account context, and permissions.
- Errors: 401.

### Chats

#### `POST /api/v1/chats`

- Authenticated.
- Body: mode, optional title, optional authorized internal account context.
- Customers can create only customer-mode chats for their own account.
- Returns chat metadata.

#### `GET /api/v1/chats`

- Authenticated.
- Query: mode, cursor/page, bounded limit.
- Returns owner-scoped paginated chat summaries.

#### `GET /api/v1/chats/{chatId}`

- Authenticated and owner/role scoped.
- Returns chat, messages, citations, safe tool events, and pending actions.
- Errors: 401, 403, 404.

#### `POST /api/v1/chats/{chatId}/messages`

- Authenticated.
- Body: content and optional client request ID.
- Validates ownership, length, and idempotency.
- Returns a streamed event sequence where feasible, ending in completed, awaiting confirmation, or failed.
- Persists user/assistant messages, safe tool runs, citations, and pending action.
- Errors: 400, 401, 403, 404, 409, 413, 429, 503.

### Actions

#### `POST /api/v1/actions/{actionId}/confirm`

- Authenticated.
- Revalidates owner/role, account scope, pending status, expiry, immutable payload, and current target.
- Transactionally executes the allowlisted action and writes audit state.
- Idempotently returns an existing successful result on duplicate confirmation.
- Errors: 401, 403, 404, 409, 422, 500.

#### `POST /api/v1/actions/{actionId}/cancel`

- Authenticated.
- Owner/authorized role only.
- Marks a pending action cancelled.
- Errors: 401, 403, 404, 409.

### Sources

#### `GET /api/v1/sources/{documentId}/chunks/{chunkId}`

- Authenticated.
- Reapplies document/account authorization.
- Returns title, type, version, status, pages, excerpt, and reliability label.
- Customer agreements are available only to the matching account.
- Errors: 401, 403, 404.

### Internal P1 APIs

#### `GET /api/v1/internal/insights`

- Support/operations role.
- Filters: type, severity, account, status, pagination, sort.
- Returns snapshot time, summary counts, charts, and ranked insight cards.

#### `GET /api/v1/internal/insights/{insightId}`

- Internal authorized role.
- Returns detection rationale, parameters, affected records, and evidence.

#### `GET /api/v1/internal/tickets`

- Internal authorized role.
- Filters: search, account, status, severity, category, SLA state, pagination.
- Returns paginated ticket summaries.

#### `GET /api/v1/internal/tickets/{ticketId}`

- Internal authorized role.
- Returns ticket, related order/account context, snapshot, and historical-resolution warning.

No direct ticket PATCH is needed. P1 updates use the generic pending-action and confirmation endpoints.

### System

#### `GET /api/v1/health`

- Public liveness only; no dependency secrets.

#### `GET /api/v1/ready`

- Restricted or minimal in production.
- Checks database, PGVector, active snapshot, and LLM configuration.
- Returns 503 when required dependencies are unavailable.

### Ingestion

Ingestion is a local administrative script, not a public HTTP endpoint. It supports validate/dry-run, ingest, and activate-snapshot modes and produces a human-readable plus machine-readable report.

---

## 16. Authentication and Security Design

### Authentication

- Seed documented demo users; no public registration.
- Hash passwords with Argon2.
- Generate cryptographically random opaque session tokens.
- Store only a hash of each token.
- Use `HttpOnly`, `SameSite=Lax`, and hosted-production `Secure` cookies.
- Configurable session expiry and revocation on logout.

### API/security controls

- Pydantic/Zod validation.
- Parameterized SQL through SQLAlchemy.
- Bounded chat length, pagination, context, and tool output.
- CORS restricted to configured frontend origin.
- Origin/CSRF protection for cookie-authenticated mutations.
- Rate limits for login, chat, and action endpoints without adding Redis initially.
- Generic login errors and customer-safe not-found responses.
- HTTPS for hosted deployment.

### Prompt injection/data controls

- Retrieved content is data, never instructions.
- The model receives no filesystem, shell, web, or arbitrary SQL tool.
- Tool schemas and allowed query shapes are fixed.
- Customer authorization is independent of prompt/model output.
- Do not log document bodies, passwords, session tokens, API keys, or unrestricted prompts.

### Raw data and secrets

Before Git initialization, `.gitignore` must exclude at least:

```text
data/raw/
backend/.env
frontend/.env
.env
*.log
__pycache__/
.pytest_cache/
node_modules/
dist/
```

The OpenRouter key belongs only in `backend/.env`. It must never use a `VITE_` name, be sent to the frontend, appear in logs, or be committed.

---

## 17. AI and Agent Architecture

### LLM configuration

- Provider: OpenRouter.
- Base URL: `https://openrouter.ai/api/v1`.
- Primary model: `liquid/lfm-2.5-2.6b:free`; fallbacks: `inclusionai/ling-3.0-flash-vl:free`, then `openrouter/free`.
- Authentication: backend-only OpenRouter API key.
- Automatic fallback: none.
- Timeout: configurable.
- Retry: at most one retry for retryable transport/provider failures, with backoff.
- Maximum LLM calls per user message: default three.

### Prompt modules

1. Core supplied-data-only policy.
2. Customer/internal role policy.
3. Source authority and effective-date policy.
4. Historical ticket context warning.
5. Tool-selection and bounded-execution policy.
6. Action confirmation policy.
7. Citation/confidence response contract.

Prompts must not contain secrets or hard-coded example answers.

### Agent tools

#### `search_documents`

Searches authorized policy, SOP, product guide, and agreement chunks through hybrid retrieval. Server injects role/account filters. Returns bounded excerpts with source metadata and authority class.

#### `lookup_operational_data`

Looks up allowlisted account, order, and ticket views. It does not accept arbitrary SQL. Customer scope is mandatory and injected server-side.

#### `calculate_support_outcome`

Runs deterministic calculation types such as pickup lateness, SLA state, cancellation facts, and documented service-credit prerequisites. Returns result, inputs, missing fields, evidence, and snapshot time.

#### `search_historical_ticket_context`

Finds similar authorized tickets for context. Output is always labeled non-authoritative and cannot establish policy or entitlement.

#### `create_escalation`

Dual-stage guarded tool:

1. Without trusted confirmation state, it creates/returns only a pending action proposal.
2. After the user confirms through the action API, the backend invokes the protected execution path with trusted confirmation state.

The model cannot fabricate trusted confirmation state.

### Agent graph

1. Load auth/chat/snapshot context.
2. Classify intent and extract record identifiers.
3. Select one or more tools.
4. Execute authorized tools, with independent validation.
5. Normalize evidence.
6. Apply source reliability and conflict rules.
7. Assign confidence.
8. Generate cited answer or pending action.
9. Persist safe outputs and audit data.
10. Stop at configured tool/LLM limits.

### Agent state

- Request/chat/user IDs.
- Role and permitted account scope.
- Active snapshot.
- Bounded recent messages.
- Intent/entities.
- Tool results/evidence.
- Conflicts and missing facts.
- Confidence.
- Pending action.
- Step counters and error state.

Do not persist hidden reasoning details or expose them in the UI.

### Confidence policy

- High: required structured facts exist and applicable authoritative sources agree.
- Medium: authoritative evidence exists but a non-critical ambiguity/missing fact requires qualification.
- Low: valid sources conflict, applicability is unclear, or required facts are missing.
- Unresolved: request is outside the supplied data or system capability.

Low/unresolved responses must avoid definitive entitlement claims and recommend human review/escalation.

---

## 18. RAG and Source Reliability

### Ingestion pipeline

1. Hash and register each PDF.
2. Parse page-aware text.
3. Remove repeated headers/footers without losing clause meaning.
4. Detect empty/unreadable pages.
5. Extract/validate title, type, version, status, account, and effective dates.
6. Split by section where possible, targeting approximately 600–900 tokens with approximately 100-token overlap.
7. Generate local 384-dimensional embeddings.
8. Store chunks, full-text vectors, embeddings, and provenance.
9. Produce ingestion report and refuse silent partial activation.

### Retrieval

1. Apply account/role/source filters before ranking.
2. Run vector similarity search.
3. Run PostgreSQL full-text search.
4. Merge ranks deterministically.
5. Adjust for applicability, current/deprecated status, customer scope, and effective dates.
6. Return a small diverse evidence set.

### Source precedence

Precedence is contextual:

1. Valid customer-specific agreement for that customer and subject.
2. Current policy or current SOP, depending on whether the question concerns entitlement or procedure.
3. Product Operations Guide for operational facts and known issues.
4. Structured account/order/ticket facts for record state.
5. Deprecated policy for conflict/audit explanation only.
6. Historical ticket resolutions as non-authoritative context only.

An agreement overrides a general commercial rule only within its customer, subject, and valid period. An SOP describes process and does not automatically override explicit contractual entitlement.

### Context sent to OpenRouter

Send only:

- User question.
- Safe authenticated-context summary.
- A bounded number of relevant excerpts.
- Required structured facts.
- Deterministic calculation results.
- Explicit evidence labels/conflicts/missing facts.

Never send the complete PDFs, workbook, database dump, API key, password/session data, or unrelated accounts.

---

## 19. Workbook Ingestion and Snapshot Rules

At implementation start:

1. Inspect every workbook sheet and column.
2. Read the README sheet and locate the stated dataset snapshot timestamp.
3. Create an explicit mapping file from source columns to canonical fields.
4. Validate account/order/ticket identifiers and relationships.
5. Normalize timestamps to UTC while preserving source values.
6. Preserve unknown columns in `raw_payload`.
7. Reject or report invalid rows with sheet/row provenance.
8. Do not activate a snapshot with missing reference time or critical integrity failures.

All questions such as "overdue," "three hours late," "within seven days," or "approaching SLA" must compare against the workbook snapshot, not the computer's current clock.

Historical ticket resolution text may be indexed for internal contextual search but must carry a hard non-authoritative flag in database results, tool schemas, prompts, and UI.

---

## 20. Proactive Issue Detection (P1)

Use deterministic, explainable analytics before considering advanced ML:

- SLA overdue: snapshot time is later than due time and ticket remains open.
- SLA at risk: configurable remaining percentage or time threshold.
- Recurring category: configurable minimum similar tickets within a window.
- Complaint surge: recent window count exceeds a configured multiplier and minimum count versus the prior window.
- Cross-account issue: same normalized category/known issue affects a configurable minimum number of accounts.
- Known-issue match: controlled semantic/category match to the product guide, with supporting excerpts.

Every insight records:

- Snapshot/time window.
- Thresholds and calculation formula.
- Affected entities.
- Supporting evidence.
- Severity/score.
- Calculation time.

The LLM may summarize an insight but does not determine the underlying counts or SLA state.

---

## 21. Environment Variables

### Frontend `.env.example`

- `VITE_API_BASE_URL`
- `VITE_APP_NAME`
- `VITE_ENABLE_INSIGHTS`

No frontend secret variables.

### Backend `.env.example`

- `APP_ENV`
- `APP_HOST`
- `APP_PORT`
- `FRONTEND_ORIGIN`
- `DATABASE_URL`
- `SESSION_COOKIE_NAME`
- `SESSION_TTL_MINUTES`
- `SESSION_COOKIE_SECURE`
- `SESSION_TOKEN_PEPPER`
- `LLM_PROVIDER=openrouter`
- `OPENROUTER_API_KEY`
- `OPENROUTER_BASE_URL=https://openrouter.ai/api/v1`
- `OPENROUTER_MODEL=liquid/lfm-2.5-2.6b:free`
- `OPENROUTER_FALLBACK_MODELS=inclusionai/ling-3.0-flash-vl:free,openrouter/free`
- `LLM_TIMEOUT_SECONDS`
- `LLM_MAX_RETRIES`
- `LLM_MAX_OUTPUT_TOKENS`
- `AGENT_MAX_LLM_CALLS`
- `AGENT_MAX_TOOL_STEPS`
- `EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2`
- `EMBEDDING_DEVICE`
- `DOCUMENT_TOP_K`
- `RAG_CHUNK_TOKENS`
- `RAG_CHUNK_OVERLAP_TOKENS`
- `DATA_PACK_DIR`
- `DATA_MANIFEST_PATH`
- `ACTION_CONFIRMATION_TTL_MINUTES`
- `LOG_LEVEL`
- `LOG_FORMAT`
- `RATE_LIMIT_LOGIN`
- `RATE_LIMIT_CHAT`
- P1 insight threshold variables.

Validate configuration on startup. Do not hard-code URLs, ports, credentials, tokens, model endpoints, limits, or environment-specific settings.

---

## 22. Error Handling

### Frontend

- Preserve unsent/failed user messages and offer Retry.
- Show a specific rate-limit message for OpenRouter 429 responses.
- Show supported partial results only when clearly labeled incomplete.
- Preserve pending action UI when a retry is safe.
- Avoid duplicate messages/actions after network reconnection.
- Isolate P1 dashboard panel failures where possible.

### Backend/database

- 400: malformed request.
- 401: unauthenticated/expired session.
- 403: forbidden internal operation.
- 404: missing resource or customer-safe unauthorized lookup.
- 409: duplicate/expired/cancelled action or run conflict.
- 413: message/request too large.
- 422: validation failure.
- 429: application or OpenRouter rate limit.
- 503: database, PGVector, active snapshot, or LLM unavailable.
- 500: safe unexpected error with request ID.

Transactions roll back fully. Stack traces and provider secrets never reach the client.

### LLM/agent

- Retry once only for retryable provider/transport failure.
- Validate every tool call before execution.
- Permit at most one model correction for malformed tool arguments where safe.
- Stop at maximum LLM/tool steps.
- If structured final output is malformed, parse/validate conservatively or return a safe error.
- Never turn no evidence into a confident answer.

### Ingestion

- Missing expected file: fail with filename.
- Duplicate checksum: report and skip/idempotently reuse.
- Unreadable critical PDF page: fail activation.
- Missing README snapshot: fail activation.
- Invalid relationships/timestamps: report source sheet/row and fail when critical.
- Unknown columns: preserve and warn.

---

## 23. Responsive and Accessibility Requirements

### Desktop

- Persistent navigation and conversation sidebar.
- Readable centered chat column.
- Citation/tool detail side panel.
- P1 grid dashboard and full tables.

### Tablet

- Collapsible navigation.
- Citation overlay/drawer.
- Two-column dashboard where space permits.
- Horizontally scrollable tables with sticky identifiers.

### Mobile

- Single-column layout from 320 px.
- Sidebar drawer.
- Composer remains reachable above safe-area inset.
- Tool trace collapses.
- Citation detail becomes full-height sheet.
- Confirmation buttons are large and clearly separated.
- Tables become cards or controlled scroll regions.
- No required hover interaction.

### Accessibility

- Keyboard-operable navigation, dialogs, drawers, and actions.
- Visible focus states.
- Semantic labels and landmarks.
- `aria-live` updates for run/action status.
- Sufficient color contrast.
- Reduced-motion support.

---

## 24. Dependencies

Exact versions should be pinned during implementation after compatibility verification.

### Frontend

- React and React DOM.
- TypeScript and Vite.
- Tailwind CSS.
- shadcn/ui dependencies and selected Radix primitives.
- React Router.
- TanStack Query.
- Zustand.
- React Hook Form and Zod.
- Recharts for P1.
- Safe Markdown renderer/sanitizer.

### Backend

- FastAPI and Uvicorn.
- Pydantic and pydantic-settings.
- SQLAlchemy 2.x, asyncpg, Alembic, pgvector adapter.
- LangChain core/community as needed, LangGraph, OpenAI-compatible client integration.
- Sentence Transformers.
- OpenPyXL.
- PyMuPDF or pypdf following license review.
- Argon2 password hashing library.
- Multipart only if later needed; no public file upload initially.
- Focused test/static-analysis dependencies.

### Infrastructure

- PostgreSQL image that includes or supports PGVector.
- Named volumes for database data and embedding/model cache.
- No Redis, message queue, Kubernetes, or extra microservices for P0.

---

## 25. Implementation Order and Checklist

### Phase 0 — Protect workspace and establish repository

- [ ] Create `.gitignore` before Git initialization.
- [ ] Ignore `data/raw/`, all `.env` files, caches, logs, builds, and dependencies.
- [ ] Confirm raw files and OpenRouter secret are not tracked.
- [ ] Initialize Git only after protections are verified.
- [ ] Preserve this `PROJECT_PLAN.md` as the source of truth.

### Phase 1 — Inspect source pack

- [ ] Extract text/page metadata from each PDF in analysis mode.
- [ ] Inspect workbook sheets, columns, README, and snapshot time.
- [ ] Record source authority/effective-date metadata.
- [ ] Create explicit data manifest and workbook mapping.
- [ ] Document any real schema deviations from the canonical plan.
- [ ] Do not hard-code sample answers.

### Phase 2 — Scaffold and configuration

- [ ] Create frontend/backend structure.
- [ ] Configure Docker Compose for frontend, backend, and PostgreSQL/PGVector.
- [ ] Create `.env.example` files.
- [ ] Have the user place the stored key in `backend/.env`; never request it in chat.
- [ ] Add startup configuration validation.
- [ ] Verify OpenRouter key/model through a minimal backend-only smoke call without logging the key or response content unnecessarily.

### Phase 3 — Database and ingestion

- [ ] Add SQLAlchemy models and Alembic migrations.
- [ ] Enable PGVector.
- [ ] Implement data-pack manifest validation.
- [ ] Implement workbook canonical mapping and snapshot activation.
- [ ] Implement PDF parsing/chunking/metadata.
- [ ] Implement local embeddings and hybrid indexes.
- [ ] Generate and review ingestion report.
- [ ] Seed demo users/scopes after account import.

### Phase 4 — Auth and authorization

- [ ] Implement opaque sessions, cookies, Argon2, login/logout/me.
- [ ] Implement role/account policies.
- [ ] Implement scoped repositories.
- [ ] Verify horizontal/vertical isolation before connecting the agent.

### Phase 5 — Deterministic services and retrieval

- [ ] Implement authorized account/order/ticket views.
- [ ] Implement snapshot-based calculations.
- [ ] Implement hybrid document retrieval.
- [ ] Implement source precedence, effective-date, conflict, and confidence services.
- [ ] Implement citation persistence and authorized source detail.

### Phase 6 — Agent and tools

- [ ] Configure the OpenRouter primary model and free fallback chain.
- [ ] Implement typed tools.
- [ ] Implement bounded LangGraph workflow.
- [ ] Enforce maximum three LLM calls by default.
- [ ] Add tool-output/model-output validation.
- [ ] Persist safe tool activity only.
- [ ] Implement rate-limit/timeout safe behavior.

### Phase 7 — Confirmation-gated escalation

- [ ] Implement pending action schema and immutable previews.
- [ ] Implement action expiry/cancellation.
- [ ] Implement confirm endpoint with reauthorization.
- [ ] Implement transactional/idempotent escalation creation.
- [ ] Audit every state transition.

### Phase 8 — Frontend P0

- [ ] Build login and protected routing.
- [ ] Build customer/internal layouts.
- [ ] Build chat list, thread, composer, tool trace, citations, and confidence UI.
- [ ] Build source drawer.
- [ ] Build confirmation card.
- [ ] Implement loading, empty, error, retry, conflict, and success states.
- [ ] Complete responsive/accessibility pass.

### Phase 9 — P1 insights if P0 is stable

- [ ] Implement deterministic insight jobs/service.
- [ ] Implement insights and ticket APIs.
- [ ] Build dashboard, charts, filters, and detail views.
- [ ] Add confirmed ticket updates only if time remains.

### Phase 10 — Verification and submission

- [ ] Test customer cross-account isolation through all surfaces.
- [ ] Test current/deprecated/contract precedence.
- [ ] Test historical ticket restriction.
- [ ] Test snapshot-time calculations.
- [ ] Test no escalation before confirmation.
- [ ] Test duplicate/cancelled/expired confirmation.
- [ ] Test malformed model tool calls and prompt injection.
- [ ] Validate example questions using imported data and additional records.
- [ ] Validate Docker cold-start instructions.
- [ ] Check frontend build and backend static/runtime checks.
- [ ] Confirm no secret or raw pack is tracked.
- [ ] Write README and required notes.
- [ ] Prepare five-minute demo video/script.
- [ ] Deploy only if a genuine free-tier option is suitable.

---

## 26. Critical Acceptance Criteria

The P0 application is complete only when all of the following are true:

1. All seven supplied files are ingested through reusable loaders.
2. The workbook snapshot time is extracted and displayed/used.
3. Example and unseen record questions are answered from loaded data, not hard-coded logic.
4. A customer cannot access another customer's structured data or agreement through any API/tool/citation/action path.
5. The chatbot uses document retrieval, structured lookup/calculation, and a state-changing action path.
6. Multi-step questions can use multiple tools in one run.
7. Current/deprecated sources and customer agreement overrides behave deliberately.
8. Historical resolutions are never treated as policy authority.
9. Supported material claims contain citations.
10. Conflicting/missing evidence produces uncertainty and escalation rather than guessing.
11. Escalation execution requires explicit confirmation and is idempotent.
12. Tool usage is visible through safe UI events.
13. OpenRouter errors and free-tier limits have clear user-facing behavior.
14. Core screens are usable on desktop and mobile.
15. Local Docker setup works without paid services or local GPU software.
16. Repository contains no raw data pack, API key, session secret, or generated secret.
17. README, architecture note, product note, AI-usage note, and demo guidance are complete.

---

## 27. Requirement Traceability Matrix

| Requirement | Frontend | Backend | Database | AI/integration | Priority |
|---|---|---|---|---|---|
| Natural-language chatbot | Chat pages | Message service | Chats/messages | OpenRouter/LangGraph | P0 |
| Supplied-data-only answers | Limitation UI | Tool allowlist | Supplied records | Prompt/RAG | P0 |
| Document retrieval | Citations/tool trace | Retrieval service | Documents/chunks | Embeddings/PGVector | P0 |
| Structured lookup/calculation | Result explanation | Repositories/calculations | Accounts/orders/tickets | Typed tools | P0 |
| Multi-step workflow | Running state | Agent service | Tool runs | LangGraph | P0 |
| Customer privacy | Protected UI | Layered authorization | Account scopes/FKs | Scoped tool wrappers | P0 |
| Internal authorization | Internal routes | RBAC | Users/scopes | Role context | P0 |
| Source reliability | Badges/warnings | Reliability service | Source metadata | Evidence policy | P0 |
| Historical context only | Warning label | Restricted service | Ticket field | Prompt/tool label | P0 |
| Citations | Source drawer | Citation service | Citation table | Retrieval provenance | P0 |
| Confirmation before action | Action card | Confirmation executor | Pending actions/escalations | Guarded action tool | P0 |
| Tool visibility | Tool timeline | Safe event stream | Tool runs | Agent events | P0 |
| Snapshot time | Snapshot badge | Calculation context | Dataset snapshots | Tool context | P0 |
| Proactive detection | Dashboard | Insights service | Insights/ticket indexes | Optional summarization | P1 |
| Responsive interface | All pages | N/A | N/A | N/A | P0 |
| Submission artifacts | N/A | N/A | N/A | Documentation/demo | P0 |

---

## 28. Assumptions and Trade-offs

| Topic | Assumption/decision | Impact |
|---|---|---|
| Assessment data | Treat as synthetic/approved for interview use, but potentially sensitive | Never use real customer data with free endpoint; send minimal excerpts |
| Raw-file redistribution | Permission is not assumed | Keep `data/raw/` out of public Git |
| Authentication | Seeded demo users are sufficient | Demonstrates real backend controls without building onboarding |
| Customer accounts | One account per demo customer initially | Schema supports broader scope later |
| Actions | Local escalation table is the mocked operational system | Satisfies action requirement without external SaaS |
| Credit/cancellation execution | Not available | Assess eligibility and escalate only |
| Model availability | Free endpoint may be slower/rate-limited | One retry, clear failure UI, test before demo; no automatic fallback |
| Strict JSON | Ultra endpoint does not enforce it | Validate tools/results and fail safely |
| Hosted link | Preferred, not mandatory | Local Docker is complete; host only on acceptable free tier |
| Source dates | Use explicit document dates when present | Missing applicability lowers confidence |
| Workbook schema | Unknown until implementation inspection | Explicit mapping layer, no guessed critical values |
| Time zones | Normalize to UTC and preserve source values | Snapshot comparisons remain reproducible |
| Insight detection | Deterministic thresholds first | Explainable and suitable for small assessment data |
| Testing | Focused high-risk tests only | Avoid unnecessary broad suite while covering privacy/trust/actions |

---

## 29. Free/Open-Source and Cost Verification

| Item | Cost position |
|---|---|
| React/Vite/TypeScript/Tailwind/shadcn/ui | Free/open-source |
| FastAPI/Pydantic/SQLAlchemy/Alembic | Free/open-source |
| PostgreSQL/PGVector | Free/open-source |
| LangChain/LangGraph | Free/open-source; LangSmith excluded |
| Sentence Transformers | Free/open-source; verify selected model license in README |
| OpenPyXL | Free/open-source |
| PDF parser | Free/open-source; review PyMuPDF AGPL compatibility and use pypdf if needed |
| Docker-based local environment | No service charge; review Docker Desktop license for organizational production use |
| OpenRouter free endpoints | Free, rate-limited prototype endpoints; not guaranteed production pricing/availability |
| Hosted PostgreSQL/frontend/backend | Optional free tier only after current terms are verified |
| Paid dependencies | None required |

If a commercial LLM endpoint is ever added, document it explicitly as: **External paid dependency — requires API credits/payment.**

---

## 30. Required Submission Notes

### Architecture note must cover

- One bounded LangGraph agent.
- Typed tools and backend authorization.
- PDF/XLSX ingestion.
- Hybrid PGVector/full-text RAG.
- Source hierarchy/conflict handling.
- Confirmation-gated actions.
- OpenRouter privacy/rate-limit trade-off.

### Product note must cover

- Trust and Reliability is the selected additional problem.
- How contracts, current/deprecated policies, conflicts, uncertainty, and history are handled.
- P1 proactive insights roadmap/implementation status.
- Intentionally omitted production integrations and autonomous financial actions.
- Primary usefulness metric: percentage of support questions resolved correctly without human rework, measured only when citations and authorization are valid.

Supporting metrics may include escalation appropriateness, median time to resolution, citation correctness, unauthorized-data leakage rate (must be zero), and confirmed-action error rate.

### AI tool usage note

State which coding assistants were used, what they helped generate/review, and that architectural/security decisions and final verification were reviewed by the candidate.

### Five-minute demo outline

1. 45 seconds: problem and architecture.
2. 90 seconds: customer multi-step cancellation/service-credit question with citations.
3. 60 seconds: source conflict/deprecated policy behavior.
4. 45 seconds: escalation proposal and explicit confirmation.
5. 45 seconds: internal investigation or P1 insights.
6. 15 seconds: trade-offs, privacy, and next steps.

---

## 31. CODEX IMPLEMENTATION INSTRUCTIONS

1. Read this entire plan before acting.
2. Inspect the existing workspace and preserve the verified `data/raw/` contents.
3. Do not open or print the user's API key.
4. Create `.gitignore` protections before initializing Git or generating project files.
5. Verify that `data/raw/` and `.env` files are ignored before the first commit.
6. Inspect every PDF and workbook sheet before finalizing mappings or business logic.
7. Preserve the exact source provenance and workbook snapshot time.
8. Create `frontend/` and `backend/` using only the selected technologies.
9. Use Docker Compose for frontend, backend, and PostgreSQL/PGVector.
10. Use `liquid/lfm-2.5-2.6b:free` through OpenRouter, with the configured free fallback chain.
11. Keep the model chain configurable through `OPENROUTER_MODEL` and `OPENROUTER_FALLBACK_MODELS`.
12. Never expose `OPENROUTER_API_KEY` to the frontend or logs.
13. Implement P0 requirements in the phase order above.
14. Do not implement P1 until all P0 privacy, trust, ingestion, citation, and confirmation checks pass.
15. Enforce authorization in routes, services, repositories, tools, citations, and action execution.
16. Do not rely on the model for authorization, calculations, source precedence, or confirmation.
17. Do not give the model arbitrary SQL, web, filesystem, or shell access.
18. Do not hard-code the example order, customers, policies, or expected answers.
19. Use deterministic calculations with the workbook snapshot time.
20. Apply the documented source reliability rules and treat historical resolutions as context only.
21. Require citations for material conclusions.
22. Implement low-confidence/conflict escalation behavior.
23. Require explicit confirmation for every operational state change.
24. Make action payloads immutable after presentation and execution idempotent.
25. Limit LLM calls/tool steps and handle OpenRouter rate limits/timeouts safely.
26. Use environment variables for every secret and environment-specific value.
27. Do not add LangSmith, n8n, Ollama, CUDA, a paid vector service, or a second backend.
28. Implement complete frontend-to-backend-to-database-to-agent flows.
29. Handle loading, empty, partial, error, retry, conflict, pending, cancelled, expired, and success states.
30. Add only focused tests for authorization, calculations, source precedence, ingestion, and actions.
31. Validate desktop and mobile behavior.
32. Prepare all required submission documentation and demo material.
33. Do not introduce paid services unless the user explicitly authorizes them.
34. Consider P0 complete only when every criterion in Section 26 passes.
