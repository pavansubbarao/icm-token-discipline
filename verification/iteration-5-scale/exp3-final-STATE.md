---
incident: INC-2026-0777
domain: tech-ops
severity: high
stage_done: 04-remediate
next: closed
related:
---
# State
## Findings so far (≤10 bullets)
- Symptom: Slack alerts intermittently dropped in prod since 2026-08-20 deploy; email+SMS fine. Severity high (card tech-ops-severity-classification).
- Root cause (card notifications-dispatcher-slack-drop, anchors FRESH at remediate): gutted dispatcher.js — single-attempt dispatch(), channel transports undefined (ReferenceError as-is), no-op emitter gauge → silent drops. Modules: notifications primary, shared contributing.
- Verify: record INVALID vs schemas/tech-ops/incident.schema.yaml (icm/incident/v2) — key `incident` should be `id`; opened_at, summary, affected_modules missing. Fix folded into R4.
- domains/tech-ops/REMEDIATION.md is 12 identical boilerplate provisions, no incident semantics (card tech-ops-remediation-boilerplate); R1–R5 derived from root-cause card, keeping only its hooks (blast-radius check, on-call waiver, metrics ns).
- R1 Mitigate now: roll back notifications service to last pre-2026-08-20 build via deploy tooling/artifact registry (workspace has no .git); confirm blast radius first (notifications + shared only).
- R2 Fix forward (one PR): restore real {email,sms,slack} transports in src/notifications/dispatcher.js; wrap dispatch() in bounded retry+backoff with try/catch (Slack 429/timeout) per MODULES.md "dispatch with retry" contract; dead-letter queue on exhaustion; implement gauge() in src/shared/emitter.js and emit per-channel dispatch success/failure/retry metrics + Slack failure-rate alert (ns ops.tech-ops_remediation.p1).
- R3 Verify fix: synthetic canary alert per channel; replay Slack alerts dropped 2026-08-20→fix from send logs; confirm where working email/SMS actually run (legacy path = masking confirmed).
- R4 Backfill record to schema: rename `incident`→`id` (or map on export); opened_at from deploy/alert timeline; structured summary ≤500 chars; affected_modules [notifications, shared]; determine customer_impact.
- R5 Postmortem: identify the deploy commit that gutted dispatcher.js and the CI gap that passed it; any deviation from R1–R4 requires written waiver from on-call lead (weekly ops sync review).
- Escalation trigger: escalate (fresh session, load domains/tech-ops/ESCALATION.md) if ANY of — (a) fix not verified by 3-channel canary within 4h of remediation start; (b) any Slack drop after fix (canary or replay failure); (c) evidence a dropped alert masked another active incident in the 08-20→fix window; (d) alerts prove customer-facing → set customer_impact, raise severity high→critical.

## Open items (execution, post-close)
- Execute R1–R5 (on-call owns); replay window starts 2026-08-20.
- customer_impact unknown — feeds R4 and escalation condition (d).

## Files consulted (do NOT re-read; trust the bullets above)
- Intake: 01-intake/CONTEXT.md, 01-intake/INTAKE_TEMPLATE.md, domains/tech-ops/CONTEXT.md, domains/tech-ops/SEVERITY.md (grep survey only), incidents/_templates/STATE.md
- Analyze: 02-analyze/MODULES.md, src/notifications/dispatcher.js, src/shared/emitter.js, PROMPTS.md, CLAUDE.md (auto-loaded)
- Verify: 03-verify/CONTEXT.md, schemas/tech-ops/incident.schema.yaml, records recall (2 cards FRESH)
- Remediate: records recall (2 cards FRESH — trusted, no code re-read), domains/tech-ops/REMEDIATION.md (grep survey + lines 1–13 of 38 only), PROMPTS.md (stage-prompt/load-report slice), skill references/memory.md
