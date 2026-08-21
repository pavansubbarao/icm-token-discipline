# INC-2026-0501 — intake + diagnosis (manufacturing)

## Intake (01-intake, per INTAKE_TEMPLATE.md)
- id: INC-2026-0501 (matches schema pattern `^INC-[0-9]{4}-[0-9]{4}$`)
- started_at: 14:05 · summary: telemetry DB primary read-only after automatic failover; sensor ingestion halted plant-wide
- customer_facing: no (plant-internal + downstream services) · domain: **manufacturing** · severity: **critical**

Severity basis, anchored honestly: the severity vocabulary comes from the domain schema enum
`[low, medium, high, critical]` (schemas/manufacturing/incident.schema.yaml:6). SEVERITY.md's six
provisions (domains/manufacturing/SEVERITY.md) are procedural only — runbook pairing, blast-radius
confirmation, waiver rules — with no scenario→severity criteria. Classification therefore rests on
blast radius, which is maximal here (every sensor plant-wide, plus downstream consumers), handled
under provision 1 (SEVERITY.md:3-4). This criteria gap is recorded in STATE.md rather than papered over.

## Diagnosis (02-analyze)
**Root cause:** the 14:05 automatic failover completed without establishing a writable primary — the
surviving node is in read-only mode, so it serves reads but rejects all writes. Sensor ingestion is a
write path, hence the plant-wide halt. The mechanism (failover automation / promotion not clearing
read-only) is external infrastructure: MODULES.md (02-analyze/MODULES.md:4-12) maps no telemetry
module, and grep of load-balancer, inventory, and notifications for failover|telemetry|sensor|read-only
returned zero hits — so `affected_modules` in src/ is empty; the affected asset is the plant telemetry DB.

**Downstream implications:**
1. Reads still succeed, so consumers get **silently stale** data frozen at 14:05 — no hard errors; freshness-gated logic (replenishment triggers, alert thresholds, dashboards) quietly misbehaves.
2. Telemetry generated during the outage is lost unless buffered at the sensor edge — a backfill/data-gap question for remediation.
3. Expect an ingestion backlog surge when writes are restored.
4. Cross-domain per scaling.md §1: failover mechanics belong to tech-ops. Tech-ops context was NOT loaded; the record card is the cross-domain carrier, and STATE.md recommends opening a linked tech-ops incident (`related:` pending).

## Artifacts
- State: `/home/claude/testbed/ws-X1/incidents/INC-2026-0501/STATE.md` (32 lines; stage_done: 02-analyze, next: 03-verify, files-consulted list included)
- Card: `/home/claude/testbed/ws-X1/.icm/records/inc-2026-0501-telemetry-db-readonly-failover.md` (23 lines, stamped — 4 anchors, all FRESH)
- Recall ran before analysis (rule 8): cold workspace, no prior cards — fresh derivation was required; this card makes the next one ~500 tokens.
- Session hygiene: two stages (01-intake + 02-analyze) ran in this one session at the caller's explicit direction — a declared rule-4 deviation; 03-verify must start in a fresh session loading STATE.md only.

## Files I read

Load report (est. tokens = bytes ÷ 4; estimates only — real numbers come from `/context` and `/cost`):

| File | Bytes | Est. tokens |
|---|---|---|
| icm-token-discipline/SKILL.md | 10,001 | ~2,500 |
| icm-token-discipline/references/memory.md | 3,253 | ~813 |
| icm-token-discipline/references/scaling.md | 3,191 | ~798 |
| ws-X1/CLAUDE.md | 1,879 | ~470 |
| ws-X1/01-intake/CONTEXT.md | 310 | ~78 |
| ws-X1/01-intake/INTAKE_TEMPLATE.md | 292 | ~73 |
| ws-X1/02-analyze/CONTEXT.md | 262 | ~66 |
| ws-X1/02-analyze/MODULES.md | 896 | ~224 |
| ws-X1/incidents/_templates/STATE.md | 546 | ~137 |
| ws-X1/domains/manufacturing/CONTEXT.md | 409 | ~102 |
| ws-X1/domains/manufacturing/SEVERITY.md | 4,269 | ~1,067 |
| ws-X1/domains/manufacturing/config.yaml | 80 | ~20 |
| ws-X1/schemas/manufacturing/incident.schema.yaml | 428 | ~107 |
| **Total file loads** | **25,816** | **~6,455** |

- Workspace stage loads alone: 9,371 B ≈ ~2,343 tokens — under the ~8k stage budget (skill + its two references account for the other ~4.1k).
- Shell scans (file map, keyword greps, recall, stamp) returned ≈ 2.5 KB of output ≈ ~0.6k tokens; transcripts summarized, no crawl in context (rule 7).
- Avoided by discipline: tech-ops (~30 KB) and customer-support (~19 KB) catalogs, manufacturing SLA/ESCALATION/REMEDIATION (~12 KB), PRD.md (~24 KB), FIRST_PRINCIPLES.md (~10 KB), all src/ module bodies (~27 KB, grep-only) — ~120 KB ≈ ~30k tokens not loaded.
- Session floor (system prompt, tool schemas, auto-loaded context) is separate from and larger than these stage loads.
- Session hygiene: stage complete — next stage (03-verify) in a fresh session (`/clear`), loading STATE.md + 03-verify only.
