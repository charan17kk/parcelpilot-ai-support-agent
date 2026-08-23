# Product Note

## Additional problem chosen: trust and reliability

The submission prioritises ParcelPilot's trust problem. A support tool loses credibility quickly if it applies an old policy, ignores a contract override, exposes another customer's record, or claims an action completed when it did not.

The product therefore shows evidence, source authority, tool activity, confidence, and the fixed workbook snapshot date. The backend deliberately treats agreements as higher authority than general rules, excludes deprecated policy by default, and labels historical resolutions as untrusted context. When required evidence or a business calendar is absent, the output calls for human review.

Actions use a visible confirmation card. Preparing an escalation has no operational effect; the user can inspect, confirm, or cancel it. This makes the boundary between an AI suggestion and an executed operation obvious.

## What I would build next

1. **Evaluation set and release gate.** Build representative questions from the supplied records plus adversarial cross-account/conflict tests. Measure grounded correctness, citation validity, access-control leakage, tool selection, and escalation precision before changing prompts or models.
2. **Proactive issue detection.** Add an internal dashboard that clusters ticket descriptions, highlights cross-customer known-issue patterns, and shows high-severity tickets approaching SLA. Start with deterministic counts and thresholds before adding AI summaries.
3. **Production identity and approvals.** Integrate SSO, team/region permissions, service-credit approval thresholds, and a real ticketing connector with the same confirmation and idempotency contract.
4. **Source operations.** Add document review/activation workflow, expiry warnings, owner metadata, ingestion diffs, and an admin conflict queue.
5. **Agent quality improvements.** Add streaming tool progress, conversation summarisation, structured final-answer validation, and provider/model fallback after a formal evaluation.

## Intentionally left out

- Real carrier, ticketing, or shipment mutations: the assessment requests a mocked local action and supplies no external credentials.
- Exact business-hours SLA breach timestamps: no working-hours/holiday calendar is supplied.
- Automatic service-credit issuance: credits are advisory and can require approval or monthly-cap data not present in the pack.
- Proactive issue dashboard: trust/reliability received the available implementation time first.

The submitted application is hosted as a single Docker web service on Render with Neon PostgreSQL/pgvector. The free service may spin down when idle, so the first request after inactivity can take about a minute.

## Primary usefulness metric

**Grounded first-contact resolution rate:** the percentage of support questions resolved without human rework where every material claim is supported by the correct authorised source or structured record.

This metric should be paired with hard guardrails: zero confirmed cross-account disclosures and zero actions executed without explicit confirmation.
