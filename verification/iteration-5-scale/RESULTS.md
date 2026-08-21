# Iteration 5 — the three scale stress-cases, implemented and verified
Date: 2026-08-21 · Skill: v1.4 (references/scaling.md + STATE/MODULES template upgrades)
Stress-cases posed by external ICM review: cross-domain incidents, module explosion, state bloat.

## Experiment 1 — cross-domain incident (audited fixture workspace)
Session A (manufacturing): telemetry-DB read-only failover diagnosed, card filed (INC-2026-0501).
Session B (tech-ops, fresh): metrics-API 503s — must explain them without entering manufacturing.
**Verified on disk:** Session B read **zero** `domains/manufacturing/` files; recalled the FRESH
card (~450 tokens) for the entire failover root cause; attributed the 503s through the real
LB-pool-drain chain with line cites; `related:` set **in both** STATE.md files; both cards FRESH;
workspace loads ~5.8k (≤ budget). Protocol confirmed: knowledge crosses via records; contexts don't.
Tokens: A 75.6k · B 79.4k (subagent totals incl. fixed overhead).

## Experiment 2 — module explosion (real 102-crate Codex monorepo)
Task: locate the 2–3 causal crates for an app-server hang without reading the workspace flat.
**Verified on disk:** "Files I read" totals 13 entries against 102 crates; hierarchy built by shell
(names → dependency edges → sizes), triage to 3 real, coherent candidates (`codex-app-server`,
`app-server-transport`, `app-server-daemon` — with specific untimed-await line cites;
`app-server-protocol` cleared as pure types); one subagent survey of 6 secondary crates returned
exactly 10 lines; main-session repo loads ~5.0k of the ≤8k budget — no stage split needed.
Deviation: the agent claimed a filed record card that is absent on disk — one over-claim caught by
verification; the locating behavior itself passed every check. Tokens: 75.4k.

## Experiment 3 — state bloat (full 4-stage incident, fresh session per stage)
INC-2026-0777 (dispatcher dropping Slack alerts) through intake → analyze → verify → remediate.
**Verified on disk:** STATE.md at every handoff: 25 → 27 → 31 → **30 lines** (cap 40); exactly one
Findings section at the end (rewrite-not-append held — stage 4 is not stage 1 plus appendices);
`stage_done: 04-remediate / next: closed`; 4 record cards accumulated; per-stage loads 2.2–6.1k,
all within budget. Root-cause chain (gutted dispatcher: no retry, undefined transports, no-op
metrics) consistent across stages via the handoff alone.
Bonus safety finding: a verify-stage session accidentally launched against a workspace with **no**
STATE.md refused to fabricate one and reported itself blocked — the discipline fails safe.

## Honest notes
Subagent totals include ~40k+ fixed overhead each; per-stage load reports are the comparable
figures. Two orchestration attempts in this round initially reported agents that had never
launched — caught both times by checking the filesystem before believing the claim, which is the
same measure-first method the skill itself enforces. One agent over-claimed a filed card (above).
