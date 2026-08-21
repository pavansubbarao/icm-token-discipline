# Course-correction audit

One pass that finds and fixes the actual token leaks in an existing ICM workspace. Run it in a **fresh, dedicated session** (the audit itself should not ride on top of a fat incident conversation). Follow the steps in order — measurement first, structure second — and keep the human gate before any file moves. Read `mechanics.md` first if you haven't; you'll be explaining these findings.

## Step 0 — Baseline (do not skip)

Numbers first, so the after can be compared to the before:

1. Fresh session in the workspace → `/context` → record the floor (total, plus the MCP/skills/CLAUDE.md breakdown it shows).
2. From the user or the Console usage page: sessions per day, typical turns per incident, `/cost` of one typical incident run if available.
3. Write these into `_audit/BASELINE.md` (create the folder). Five lines is enough.

If the floor is a large multiple of the 2–8k stage budget, say so now — it reframes everything that follows.

## Step 1 — Mechanical scan

Run `scripts/icm_audit.sh` from the workspace root and read its report. It surfaces: entry-file size and `@`-imports, oversize markdown, CONTEXT.md monoliths, missing MODULES.md, missing state pattern, MCP config. Don't re-derive any of this by reading files — the script exists so model tokens go to judgment, not crawling.

## Step 2 — Trim the floor

Usually the biggest single win, because it's paid in *every* session:

- **CLAUDE.md → catalog only.** Target ≤60 lines: identity, the routing table, where things live. Content it currently holds moves down into the file it points at. (This is icm-architect invariant 2 — enforce it, don't re-litigate it.)
- **Kill auto-imports.** Every `@path` line in CLAUDE.md loads that file into every session. PRD.md, FIRST_PRINCIPLES.md and friends become plain paths in the routing table ("read when deciding X"), loaded only by the stage that needs them.
- **Check `~/.claude/CLAUDE.md` too** — user-level, rides into every project's sessions.
- **Prune MCP servers** for this workspace to the ones the pipeline calls. Verify the floor dropped: fresh session, `/context`, compare to baseline.

## Step 3 — Split the monoliths

For each `domains/<d>/CONTEXT.md` the scan flagged (> ~12 KB, or clearly multi-topic):

1. Split by its own headings into `SEVERITY.md`, `SLA.md`, `ESCALATION.md`, `REMEDIATION.md` (use the domain's real topics — don't force these four names onto content that has different seams).
2. Shrink CONTEXT.md to a ≤10-line catalog pointing at the new files.
3. Update the routing table with per-task rows (format in `templates.md`).

Propose the split as a plan plus a plain `git mv`/write script, get approval, then execute — moves are a human gate. Don't split files under ~2 KB; below that, the extra routing hop costs more than it saves.

## Step 4 — Build the module map

If `02-analyze/MODULES.md` is missing or stale: generate the row skeleton by script (`ls` over the source tree, `wc -c` for sizes), then fill the one-line purpose per module from headers/READMEs — narrow reads only. Template in `templates.md`. One line per module; entry point and size columns are what make rule 3 (map before code) work.

## Step 5 — Install the state pattern

This is what makes stage-per-session possible:

1. Create `incidents/` with a `_templates/STATE.md` copy (template in `templates.md`).
2. Wire the four stage-start prompts (also in `templates.md`) into the workspace — a `PROMPTS.md` in the root, or into each stage folder's CONTEXT.md — so the user runs each stage as a fresh session that loads `incidents/<id>/STATE.md` + that stage's files, nothing else.
3. Make each stage's contract end with: update STATE.md (including files-consulted), emit the load report, stop.

## Step 6 — Re-measure

Run one representative incident through the four fresh-session stages. Record `/cost` per stage and the load reports into `_audit/RESULTS.md` next to the baseline, with the delta. If the drop is small, the residue is almost always floor (back to step 2) or session shape (stages still run inside one conversation — check how the user is actually invoking them).

## What not to do

- Don't shard further "to be safe" — more files below 2 KB adds hops, not savings.
- Don't add hierarchy for stages that don't exist (icm-architect guardrail: three real stages beat seven imagined ones).
- Don't promise a number before step 6 produces one; estimates are for planning, `/cost` is for claims.
- Don't run stages for different domains, or different incidents, in one session — one incident, one stage, one session.
