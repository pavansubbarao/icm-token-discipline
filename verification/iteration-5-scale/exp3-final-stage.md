# INC-2026-0777 — Stage 04-remediate (final stage; incident → closed)

Fresh session. Domain resolved from STATE.md: **tech-ops**; every path derived from it.
Root cause trusted from FRESH card `notifications-dispatcher-slack-drop` (recall at stage
start; both anchor sets FRESH — no code re-read).

## Finding about the domain file
`domains/tech-ops/REMEDIATION.md` (8.4 KB, 38 lines — over the ~8 KB threshold, so
grep-surveyed and sliced, never whole-read) contains **no incident-specific workflows**:
12 identical boilerplate provisions (confirmed by pattern count 12/12; zero hits for
slack/dispatch/escalat/retry/rollback/webhook/transport). It contributed only procedural
hooks: blast-radius confirmation first, written waiver from the on-call lead for
deviations, metrics namespace `ops.tech-ops_remediation.pN`. Filed as card
`tech-ops-remediation-boilerplate` (stamped). Steps below therefore derive from the
root-cause card.

## Remediation steps (dispatcher Slack-drop root cause)
- **R1 — Mitigate now (rollback).** Roll the notifications service back to the last
  pre-2026-08-20 build via deploy tooling / artifact registry (workspace has no .git).
  Per REMEDIATION.md hook: confirm blast radius first — notifications primary, shared
  contributing; no other src/ module references Slack.
- **R2 — Fix forward (one PR).** Restore the real `{email, sms, slack}` transports in
  `src/notifications/dispatcher.js` (currently undefined identifiers → ReferenceError);
  wrap `dispatch()` (lines 6–10) in bounded retry + backoff with try/catch to survive
  Slack 429/timeout, honoring the MODULES.md "dispatch with retry" contract; dead-letter
  queue when retries exhaust so no alert is ever silently dropped. Implement `gauge()` in
  `src/shared/emitter.js` (currently no-op) and emit per-channel dispatch
  success/failure/retry metrics plus a Slack failure-rate alert
  (ns `ops.tech-ops_remediation.p1`) — the no-op gauge is what made this invisible.
- **R3 — Verify the fix.** Synthetic canary alert per channel (slack/email/sms); replay
  Slack alerts dropped 2026-08-20→fix from send logs; confirm where working email/SMS
  sends actually run (a legacy path would confirm the masking hypothesis).
- **R4 — Backfill the incident record to schema** (icm/incident/v2 FAILs from 03-verify):
  rename key `incident`→`id` (or map on export); `opened_at` from deploy/alert timeline;
  structured `summary` ≤500 chars; `affected_modules: [notifications, shared]`;
  determine `customer_impact`.
- **R5 — Postmortem + process.** Identify which 2026-08-20 deploy commit gutted
  dispatcher.js and the CI gap that let a file of undefined identifiers ship; any
  deviation from R1–R4 requires a written waiver from the on-call lead (weekly ops sync).

## Escalation trigger
Escalate — fresh session, load `domains/tech-ops/ESCALATION.md` (per PROMPTS.md:
"escalating? ESCALATION.md instead"; deliberately NOT loaded now) — if **any** of:
- (a) fix not verified by 3-channel canary within **4 hours** of remediation start;
- (b) **any** Slack drop after the fix (canary or replay failure);
- (c) evidence a dropped alert masked **another active incident** in the 08-20→fix window;
- (d) alerts prove **customer-facing** → set `customer_impact`, raise severity
  high→critical.

## STATE.md
Rewritten exactly once (rewrite, not append): `stage_done: 04-remediate`, `next: closed`,
**30 lines** (≤40), findings compressed to 10 bullets, cumulative files-consulted list
kept. Incident closed pending on-call execution of R1–R5.

## Files I read (this session)
| File | How | Bytes |
|---|---|---|
| /home/claude/icm-token-discipline/SKILL.md | whole (instructed first read) | 10,001 |
| /home/claude/testbed/ws-X2/CLAUDE.md | auto-loaded (harness) | 1,879 |
| /home/claude/testbed/ws-X2/incidents/INC-2026-0777/STATE.md | whole (2.4 KB < 8 KB) | 2,413 |
| .icm records recall output (2 cards, both FRESH) | script output | ~2,300 |
| /home/claude/testbed/ws-X2/domains/tech-ops/REMEDIATION.md | **sliced**: heading grep + pattern count + lines 1–13 of 38 | ~3,150 of 8,435 |
| /home/claude/testbed/ws-X2/PROMPTS.md | **sliced**: stage-prompt + load-report lines ~9–32 | ~1,450 of 2,016 |
| /home/claude/icm-token-discipline/references/memory.md | whole (card protocol, 3.3 KB < 8 KB) | 3,253 |

Deliberately NOT loaded: any `src/` file or `02-analyze/MODULES.md` (root-cause card
FRESH — rule 5/8), `domains/tech-ops/ESCALATION.md` (trigger defined; loaded only if it
fires), `04-remediate/CONTEXT.md` (routing row + stage-4 prompt say load exactly
STATE.md + REMEDIATION.md), `SEVERITY.md`, schema, PRD/FIRST_PRINCIPLES.

## Load report
```
Load report (estimates; /context and /cost have real numbers):
- icm-token-discipline/SKILL.md          10.0 KB  ~2,500 tok (skill catalog, instructed)
- CLAUDE.md (auto-loaded)                 1.9 KB    ~470 tok
- incidents/INC-2026-0777/STATE.md        2.4 KB    ~603 tok
- .icm records recall (2 cards FRESH)     2.3 KB    ~575 tok
- domains/tech-ops/REMEDIATION.md         3.2 KB    ~790 tok (sliced: lines 1–13 of 38 + heading grep)
- PROMPTS.md                              1.5 KB    ~360 tok (sliced: lines ~9–32 of 44)
- skill references/memory.md              3.3 KB    ~813 tok (card protocol, rule 8)
Stage total: ~6.1k tokens loaded (budget 2–8k) — within budget; ~3.3k of it is skill
machinery (SKILL.md + memory.md), stage-content loads alone ~2.8k. Session floor is
separate — check /context.
filed: tech-ops-remediation-boilerplate.md (stamped)
Session hygiene: stage complete and incident closed → session over now (/clear); no next
stage. If the escalation trigger fires, that is a fresh session loading STATE.md +
domains/tech-ops/ESCALATION.md. Pausing >5 min mid-anything? Close first — idle cache
expiry re-bills the whole history at write rates on the next message.
```
