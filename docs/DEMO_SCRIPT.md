# Five-Minute Hosted Demo Script

## Before recording

- Open the hosted app and let the free Render service wake up.
- Keep the GitHub README open in a second tab for the architecture section.
- First log in as the operations manager, pre-run the internal answer, and log out.
- Log in as Northstar, keep the saved cancellation answer, then prepare the escalation immediately before recording and leave its confirmation card pending.
- Start recording on the saved Northstar cancellation answer. Use one browser window and switch roles only once during the video.
- Close Neon, Render environment, and OpenRouter tabs so no secrets can appear.
- Record at 100% browser zoom and share only the browser window.

## 0:00–0:35 — Problem and solution

Show the hosted customer interface.

> ParcelPilot's support team currently searches policies, customer contracts, product guides, tickets, and order data manually. I built ParcelPilot Assist to bring those sources into one support agent. It answers customer questions, supports internal investigations, protects each customer's data, explains which sources it trusted, and requires confirmation before creating an escalation.

## 0:35–1:05 — Architecture

Show the GitHub README or architecture note.

> The interface is React and TypeScript. FastAPI runs the backend and a single bounded LangGraph agent. PostgreSQL stores accounts, orders, tickets, conversations, and actions, while pgvector and full-text search retrieve document evidence. FastEmbed creates embeddings locally, and fast free models are called through OpenRouter with automatic fallback. Security filters, deterministic routing, and calculations run in backend tools rather than relying on model instructions.

## 1:05–2:05 — Customer answer and source conflict

Show the saved Northstar answer for:

`Can Northstar cancel ORD-1001 without a cancellation fee? Explain why.`

> The agent looks up the real order and applies Northstar's active agreement. The normal SOP would charge INR 250 after 30 minutes, but the customer agreement explicitly waives that fee, so the higher-authority contract wins. The answer shows high confidence, an INR 0 result, the tool used, and citations to the order, agreement, and current SOP. This is advisory only; the agent does not claim that a cancellation was executed.

Expand the tool summary and point to the source chips.

## 2:05–3:00 — Confirmation before an action

Open the pending customer conversation for:

`Create an escalation for ORD-1001 because the customer needs human review.`

> The agent may prepare an escalation, but preparation has no operational effect. The confirmation card shows exactly what will be created. Confirmation is handled by a separate backend endpoint that checks the owner, account scope, expiry, and current status.

Click **Confirm & create** and show the generated escalation reference.

> Only this explicit click executes the mocked action. Repeated confirmation is idempotent and cannot create duplicate escalations.

## 3:00–4:10 — Internal multi-source investigation

Log out, sign in as the operations manager, and open the saved answer for:

`A pickup is three hours late because of carrier fault. Should ORD-2002 get a service credit?`

> The user says three hours, but the structured order record shows 4.5 hours. The agent identifies the LumenWorks account, checks its agreement and the current SOP, and applies the contract's four-hour threshold. The verified result is a fixed INR 300 credit. This demonstrates that structured records and active agreements override an assumption in the question or a general default rule.

Mention that internal roles can investigate all four supplied accounts, while customers receive only their own account scope.

## 4:10–5:00 — Trust decisions, trade-offs, and next steps

> Trust was the additional client problem I prioritised. The source order is active customer agreement, current policy and SOP, current product guide, and only then historical ticket context. Deprecated policy is excluded by default. Missing evidence or unsupported exceptions lead to human review rather than a confident guess.
>
> The main demo trade-off is the free OpenRouter endpoint, which can be rate-limited, and Render's free service, which can take about a minute to wake. For a production rollout I would add evaluation gates, ParcelPilot SSO, real ticketing integrations, and a proactive dashboard for recurring issues and SLA risk.
>
> My primary success metric would be grounded first-contact resolution rate, with zero cross-account leaks and zero unconfirmed actions as hard guardrails.

End on the hosted interface and briefly show the GitHub repository URL.
