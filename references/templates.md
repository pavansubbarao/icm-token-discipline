# Templates

Copy-paste blocks. Adjust names to the workspace's real domains and modules; keep the shapes and the size columns.

## MODULES.md (lives in 02-analyze/)

```markdown
# Module map
One line per module. Load a module only when an incident touches it; prefer grep + sliced reads over whole files.

| Module | Purpose (1 line) | Entry point | Size |
|---|---|---|---|
| auth | User authentication and sessions | src/auth/index.js | 18 KB |
| payments | Payment processing and refunds | src/payments/gateway.js | 41 KB |
| notifications | Email/SMS/Slack alert dispatch | src/notifications/dispatcher.js | 9 KB |
```

## STATE.md (lives in incidents/<id>/)

Hard cap ~40 lines — this file crosses every session boundary, so every line here is paid in every later stage.

```markdown
---
incident: INC-2026-0142
domain: tech-ops
severity: high
stage_done: 02-analyze        # last completed stage
next: 03-verify
related:                      # linked incidents in other domains, if any (INC-xxxx)
---
# State
## Findings so far (≤10 bullets)
- 503s originate in load-balancer health-check timeout (5s vs upstream p99 of 7s)
- api-gateway itself healthy; error rate tracks LB flaps

## Open questions
- Was the 5s timeout changed in last week's deploy?

## Files consulted (do NOT re-read; trust the bullets above)
- 02-analyze/MODULES.md
- src/load-balancer/health-check.js (lines 40–95)
- domains/tech-ops/SEVERITY.md
```

Discipline: each stage REWRITES findings (conclusions supersede evidence — one home per fact);
never append stage-by-stage. Overflow that must persist → `incidents/<id>/notes.md`, linked here,
loaded only on demand. Hard cap ~40 lines at every handoff ([scaling.md](scaling.md) §3).

## The four stage-start prompts

Each stage is a fresh session. `/clear` first (or open a new terminal session). `<id>` and `<domain>` come from STATE.md after stage 1.

```
1 — intake:    Fresh session. Load 01-intake/CONTEXT.md, then classify this incident:
               <paste description>. Determine domain, then load ONLY domains/<domain>/SEVERITY.md.
               Output: domain + severity. Create incidents/<id>/STATE.md. Load report. Stop.

2 — analyze:   Fresh session. Load incidents/<id>/STATE.md and 02-analyze/MODULES.md.
               Identify the 1–3 affected modules; load only those (sliced). Output analysis.
               Update STATE.md. Load report. Stop.

3 — verify:    Fresh session. Load incidents/<id>/STATE.md and schemas/<domain>/incident.schema.yaml.
               Validate. Output verdict per field. Update STATE.md. Load report. Stop.

4 — remediate: Fresh session. Load incidents/<id>/STATE.md and domains/<domain>/REMEDIATION.md.
               Output remediation steps + escalation trigger. Update STATE.md (stage_done: 04,
               next: closed). Load report. Stop.
```

## Load report (ends every stage)

```
Load report (estimates; /context and /cost have real numbers):
- incidents/INC-2026-0142/STATE.md      1.1 KB  ~280 tok
- 02-analyze/MODULES.md                 0.9 KB  ~230 tok
- src/load-balancer/health-check.js     3.4 KB  ~850 tok (sliced: lines 40–95 of 210)
Stage total: ~1.4k tokens loaded (budget 2–8k ✓). Session floor is separate — check /context.
Session hygiene: stage complete → /clear before the next stage. Pausing >5 min? Close now —
idle expiry re-bills the whole history at write rates on your next message.
```

Over ~8k → add one line: which rule broke, and the fix (e.g., "rule 1: read payments/gateway.js whole; should have sliced ~60 lines").

## Routing table rows (in CLAUDE.md)

```markdown
| Task | Stage | Load exactly |
|---|---|---|
| Classify severity | 01-intake | domains/<domain>/SEVERITY.md |
| Find affected modules | 02-analyze | 02-analyze/MODULES.md → named modules only |
| Check SLA | 02-analyze | domains/<domain>/SLA.md |
| Validate incident | 03-verify | schemas/<domain>/incident.schema.yaml |
| Escalate | 03-verify | domains/<domain>/ESCALATION.md |
| Remediate | 04-remediate | domains/<domain>/REMEDIATION.md |
```

## FREE-LANE.md (the free lane / paid lane catalog — put in workspace root)

```markdown
# Free lane first — these questions cost $0 (answer by command, not by AI)
| Question shape | Free answer |
|---|---|
| Where is X defined/used? | grep -rn "X" src/ (or the .index.md of the doc) |
| What's in module M? | 02-analyze/MODULES.md row, then M's index |
| Did we answer this before? | scripts/icm_records.sh recall <words> |
| Are our records still valid? | scripts/icm_records.sh check |
| What's leaking tokens? | scripts/icm_audit.sh |
# Paid lane (worth model tokens): design, diagnosis, tradeoffs, root cause, review.
```

## Domain lookup files as YAML (denser than prose — use for table-shaped content)

Prose explains; tables route. When a domain file is really a lookup table (severity tiers, SLA
clocks), YAML encodes it in ~40% fewer tokens and slices cleanly. Keep prose files as .md.

```yaml
# domains/tech-ops/SEVERITY.yaml (~0.6k tok; replaces a ~1.0k prose file)
critical: { impact: "production down or data loss", page: immediately, examples: [gateway-5xx-storm, db-primary-down] }
high:     { impact: "production degraded, customer-facing", page: 15m, examples: [elevated-error-rate, payment-latency] }
medium:   { impact: "internal impact or single-tenant", page: business-hours, examples: [batch-delay, report-mismatch] }
low:      { impact: "cosmetic or non-urgent", page: none, examples: [log-noise, doc-drift] }
```

Update the routing table to point at the .yaml; keep one `# comments` line for meaning.

## Minimal router variant (~12 lines — smallest auditable floor)

The always-loaded router can shrink further without giving up central routing (deleting CLAUDE.md
saves ~400 cached tokens ≈ $0.002/session and loses auditability — trim instead of removing):

```markdown
# ICM router — one incident, one stage, one session; STATE.md carries state; /clear when done.
| Task | Load exactly |
|---|---|
| Classify severity | domains/<domain>/SEVERITY.yaml |
| Affected modules | 02-analyze/MODULES.md → named modules, sliced |
| SLA / Escalation | domains/<domain>/SLA.md / ESCALATION.md |
| Validate | schemas/<domain>/incident.schema.yaml |
| Remediate | domains/<domain>/REMEDIATION.md |
Rules: one domain/session · slice >8KB files · recall .icm/records first, file after · load report + /clear.
```

## Lean CLAUDE.md skeleton (target ≤60 lines, no @imports)

```markdown
# Incident management workspace (ICM)
One incident, one stage, one session. State crosses sessions via incidents/<id>/STATE.md only.

## Layout
01-intake → 02-analyze → 03-verify → 04-remediate; domains/<d>/ per-topic files; schemas/<d>/.
Reference docs (load on demand, never auto): PRD.md, FIRST_PRINCIPLES.md.

## Routing
<table above>

## Rules
Resolve domain first; one domain per session. MODULES.md before any code. Update STATE.md and
emit a load report before stopping. Stage prompts: PROMPTS.md.
```
