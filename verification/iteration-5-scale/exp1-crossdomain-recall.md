# INC-2026-0502 — intake + analysis (tech-ops)

## Classification (01-intake)
- id: INC-2026-0502 · reported_by: tech-ops · started_at: ~14:10 · customer_facing: yes
- Domain: **tech-ops** (symptom lives in gateway/load-balancer infrastructure; confirmed initial guess)
- Severity: **high** — hard total outage (503s + empty dashboards) of one customer-facing surface. Vocabulary from the schema enum `low|medium|high|critical` (schemas/tech-ops/incident.schema.yaml:6). domains/tech-ops/SEVERITY.md is 12 procedural provisions with no scenario→severity criteria (same pattern the INC-2026-0501 card recorded for manufacturing), so classification rests on blast radius, handled under provision 1 (SEVERITY.md:3-4). Escalation path to critical noted below.

## Root cause (02-analyze)
**Recalled, not re-derived:** `icm_records.sh recall` returned a FRESH card (`inc-2026-0501-telemetry-db-readonly-failover.md`, all anchors verified) — at 14:05 an automatic failover left the plant telemetry DB cluster with no writable primary; the surviving node is read-only. The card had pre-declared itself the cross-domain carrier into tech-ops.

**Derived this session (propagation mechanism, grep-grounded in the 2 MODULES.md-named modules):**
1. Post-failover, the upstream data-feed nodes behind the metrics API start failing/timing out their `/healthz` probes.
2. Two failed probes eject a node: `UNHEALTHY_AFTER = 2` (src/load-balancer/health-check.js:6, ejection at :24-26 — comment: "with slow-but-fine upstreams this drains the pool").
3. Pool drains → `pickUpstream` returns null (src/load-balancer/pool.js:8-9 — "callers translate null into a 503").
4. Gateway surfaces exactly the reported symptom: 503 `no healthy upstream` (src/api-gateway/index.js:9-12) → empty dashboards.
5. "API pods look healthy" because ejection is LB-side bookkeeping, not pod state. Timing fits: 14:05 failover + 2 probe cycles ≈ 14:10 onset.
- Contributing defect: `PROBE_TIMEOUT_MS = 5000` ejects slow-but-serving upstreams (health-check.js:5), converting a degraded read-only feed into a hard outage rather than stale data.
- affected_modules: api-gateway, load-balancer; external asset plant-telemetry-db (ledgered under INC-2026-0501).

## Linkage (scaling.md §1 — knowledge crosses via records, contexts don't)
- INC-2026-0502 is precisely the "linked tech-ops incident" INC-2026-0501's STATE.md open question called for.
- `related: INC-2026-0501` set in incidents/INC-2026-0502/STATE.md; `related: INC-2026-0502` added to incidents/INC-2026-0501/STATE.md (open question resolved in place).
- No manufacturing catalogs were loaded — the record card carried the cross-domain knowledge (~450 tokens instead of re-deriving the failover analysis).

## Records (rule 8)
- Recall hit used: inc-2026-0501-telemetry-db-readonly-failover.md (FRESH — trusted as-is, cited, not re-derived; left unmodified, its facts are unchanged).
- Filed + stamped: `.icm/records/inc-2026-0502-metrics-api-503-pool-drain.md` — 6 anchors, all FRESH (health-check.js:5-6, :24-28; pool.js:6-9; api-gateway/index.js:9-12; schema enum :6-6; SEVERITY.md:3-4).

## Open for 03-verify (in STATE.md)
- Validate against schemas/tech-ops/incident.schema.yaml; confirm blast radius per provision 1 — pool.js:6 keeps a *single global* node list: if other gateway surfaces share the drained pool, severity escalates high → critical.
- Recovery: probes self-heal nodes (health-check.js:27-28) once INC-2026-0501's remediation restores DB writes; verify no manual pool reset, and whether the 5000ms probe timeout should be raised.

Session hygiene: intake + analysis ran in one session because the task explicitly requested both; per rule 4's guardrail STATE.md is written and 03-verify should start in a fresh session (`/clear`).

## Files I read
Full reads (small files):
- /home/claude/icm-token-discipline/SKILL.md
- /home/claude/icm-token-discipline/references/memory.md
- /home/claude/testbed/ws-X1/CLAUDE.md
- /home/claude/testbed/ws-X1/01-intake/CONTEXT.md
- /home/claude/testbed/ws-X1/01-intake/INTAKE_TEMPLATE.md
- /home/claude/testbed/ws-X1/incidents/_templates/STATE.md
- /home/claude/testbed/ws-X1/02-analyze/CONTEXT.md
- /home/claude/testbed/ws-X1/02-analyze/MODULES.md
- /home/claude/testbed/ws-X1/incidents/INC-2026-0501/STATE.md
- /home/claude/testbed/ws-X1/.icm/records/inc-2026-0501-telemetry-db-readonly-failover.md (via recall output)

Sliced reads (rule 1 — never whole):
- /home/claude/icm-token-discipline/references/scaling.md lines 7–20 (§1 only, of 3.2 KB)
- /home/claude/icm-token-discipline/references/templates.md lines 70–83 (load-report block only, of 7 KB)

Grep-only (no file bodies loaded):
- domains/tech-ops/SEVERITY.md (headings + provision keyword lines; 8.3 KB file never read whole)
- schemas/tech-ops/incident.schema.yaml (enum line only)
- src/api-gateway/{index,routes}.js, src/load-balancer/{health-check,pool}.js (symptom-keyword lines only)

Deliberately NOT loaded: tech-ops SLA/ESCALATION/REMEDIATION (later stages), PRD.md, FIRST_PRINCIPLES.md, PROMPTS.md, TOKEN_LEAK_AUDIT.md, all manufacturing and customer-support files, all module bodies.

## Load report (estimates; /context and /cost have real numbers)
- CLAUDE.md                                   1.9 KB  ~470 tok
- 01-intake/CONTEXT.md                        0.3 KB   ~80 tok
- 01-intake/INTAKE_TEMPLATE.md                0.3 KB   ~75 tok
- incidents/_templates/STATE.md               0.5 KB  ~135 tok
- 02-analyze/CONTEXT.md                       0.3 KB   ~65 tok
- 02-analyze/MODULES.md                       0.9 KB  ~225 tok
- incidents/INC-2026-0501/STATE.md            2.7 KB  ~670 tok
- recall: 0501 card + freshness verdicts      1.8 KB  ~450 tok
- grep: SEVERITY.md + schema (sliced)         2.8 KB  ~700 tok (8.3 KB + 0.4 KB files never read whole)
- grep: 4 src module files (sliced)           8.5 KB  ~2.1k tok (no bodies loaded)
- dir listings + size checks                  1.5 KB  ~380 tok
- scaling.md 7–20 + templates.md 70–83        1.8 KB  ~440 tok (sliced)
Stage total: ~5.8k tokens loaded across intake+analysis combined (budget 2–8k ✓; two stages in one session by explicit task instruction).
Skill overhead, separate: SKILL.md 10.0 KB ~2.5k + memory.md 3.3 KB ~810. Session floor is separate — check /context.
Filed: inc-2026-0502-metrics-api-503-pool-drain.md (stamped, 6/6 anchors FRESH).
Session hygiene: stage complete → /clear before 03-verify. Pausing >5 min? Close now — idle expiry re-bills the whole history at write rates on the next message.
