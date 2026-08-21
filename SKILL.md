---
name: icm-token-discipline
description: Enforce per-stage token discipline inside an ICM workspace and audit where API spend actually comes from. Use whenever working in an ICM-structured workspace (numbered stage folders like 01-intake/…/04-remediate, domains/ with CONTEXT files, a routing CLAUDE.md), whenever the user mentions token usage, token bloat, context bloat, API cost, cost per interaction, "why is this so expensive", or asks to audit, restructure, or course-correct context loading — even if they never say "ICM". Also use at the start of any incident-pipeline task (intake, classify, analyze, verify, remediate) so only that stage's files get loaded.
---

# ICM Token Discipline

Companion to `icm-architect`: that skill builds the shelves; this one polices what gets carried off them — and finds where the bill actually comes from. The two concerns are different. Folder structure controls what *can* be loaded per stage. The bill is controlled by session shape: what loads automatically at session start, how long conversations run, and how often files re-enter context. A workspace can be perfectly structured and still expensive.

This skill is itself ICM-shaped: this file is the catalog (~1.3k tokens). Read a reference only when a step below says so, never all of them.

## Triage — pick a mode

- User asks to **audit, fix, restructure, course-correct, or explain cost** → Audit mode: run `scripts/icm_audit.sh` from the workspace root, follow [references/audit.md](references/audit.md) step by step, and write the findings as `TOKEN_LEAK_AUDIT.md` using [references/report-template.md](references/report-template.md). Read [references/mechanics.md](references/mechanics.md) before promising any savings number.
- User is **working an incident or a stage** → Discipline mode: apply the seven rules below. If the workspace has never been audited, offer the audit once, in one line, and carry on.
- User names a **monthly dollar target**, says "strict mode", or the workspace CLAUDE.md declares it → read [references/strict-mode.md](references/strict-mode.md) and run under it: halved budgets, batched tool calls, dollar-priced load reports against a daily allowance.

## Why structure alone didn't cut the bill

Every API call re-sends the entire conversation so far as input. There is no "session memory" that makes previously loaded files free — a file read on turn 2 is re-billed (cache-discounted, not free) on every turn after it. On top of that, every session starts with a fixed floor — system prompt, tool and MCP schemas, auto-loaded CLAUDE.md and its imports — that dwarfs a 2–8k stage budget when it's bloated. Detail and the honest math: [references/mechanics.md](references/mechanics.md). Read it before estimating, measuring, or explaining costs to the user.

## The eight rules (Discipline mode)

**1. Measure before reading.** Check size first (`wc -c file` — ls is fine too). Over ~8 KB (~2k tokens): don't read whole; `grep -n` for the section you need, then Read with offset/limit. Every byte loaded stays in this session's context and is re-sent on every remaining turn, so a narrow read pays off repeatedly.

**2. Resolve the domain first; derive every path from it.** Classify the incident's domain before loading anything domain-specific, then build paths as `domains/<domain>/…` and `schemas/<domain>/…`. Never glob or read across `domains/` or `schemas/` after that. One domain per session — a tech-ops incident never justifies opening a manufacturing file.

**3. Map before code.** Read `02-analyze/MODULES.md` (create it from [references/templates.md](references/templates.md) if missing) and let it name the 1–3 relevant modules. Load only those, and prefer slicing: `grep -n` the symbol, read the surrounding lines, not the whole file. Loading a 500-line module to use 40 lines of it charges the other 460 on every subsequent turn.

**4. One stage per session; state lives on disk.** End every stage by writing `incidents/<id>/STATE.md` (≤40 lines, template in templates.md), including the *files already consulted* list. Then tell the user the stage is done and the next stage should start after `/clear` (or in a fresh session). The next stage loads STATE.md plus its own stage folder — never conversation scrollback. This is the single biggest lever: four short sessions with a 40-line handoff re-bill a 40-line file; four stages in one conversation re-bill everything, every turn.

**Guardrail:** when a stage completes, the session is over. If asked to continue into the next stage in the same conversation, write STATE.md first and recommend `/clear` — proceed only if the user explicitly declines after hearing why (each further turn re-bills everything loaded so far). And if a pause longer than ~5 minutes is coming mid-stage, close the stage now: the prompt cache expires on idle, so the next message after a break re-bills the entire history at write rates (~12× the cached price). Sessions measured in hours are the leak; sessions measured in minutes are the fix.

**5. Never re-read.** If a file is already in context this session (including CLAUDE.md, which Claude Code auto-loads), reference it — a second Read doubles the charge for zero new information. Across sessions, STATE.md's consulted-files list plays the same role: trust recorded conclusions instead of re-deriving them.

**6. Close every stage with a load report — and a short one.** Exact format in templates.md: each file read → bytes → est. tokens (bytes ÷ 4), one total, one line naming the session floor as separate, one session-hygiene line (`/clear` next). If the stage total exceeds ~8k, say which rule was broken and what to change — don't just report the overrun. State that these are estimates; real numbers come from `/context` (composition) and `/cost` (spend) in Claude Code. The stage output itself is part of the budget: conclusions only, ≤~40 lines, never restating loaded file content — output tokens bill ~5× input, and everything echoed rides along in every later turn.

**7. Crawling goes to scripts and subagents, not the main context.** Status scans, index rebuilds, file maps: shell one-liners, results summarized. Broad exploration ("which modules touch retry logic?"): a subagent that returns a ≤10-line answer, so the search transcript never enters this session. Subagent tokens still bill — the win is that a short summary replaces a long transcript in every later turn — so give subagents narrow questions, not open wanders.

**8. Recall before analysis; file after judgment.** Before analyzing anything, run `scripts/icm_records.sh recall <distinctive words>` — a FRESH card answers for ~500 tokens instead of a re-derivation; a STALE card gets its changed anchors re-verified, never silently trusted. After any answer that took real reading, file a ≤20-line anchored card and `stamp` it. Protocol and card format: [references/memory.md](references/memory.md). This is the compounding rule — the workspace gets cheaper the longer it's used.

## Model per stage

Intake/classification and schema verification are mechanical — run them on the cheapest model tier; analysis and remediation earn a mid tier. In Claude Code, `/model` switches, and since rule 4 makes each stage its own session, per-stage models are free to set. When the user is already on cheap models and still overspending, the cause is almost always volume × floor × session length — say so and point at the audit, not at further model downgrades.

## References

- [references/audit.md](references/audit.md) — the course-correction procedure: baseline measurement, floor trim, monolith splits, MODULES.md, state pattern, re-measure. Read in Audit mode.
- [references/mechanics.md](references/mechanics.md) — how Claude Code API billing actually works: per-turn resend, prompt caching, the session floor, why staged messages in one chat don't save much, where real numbers live. Read before explaining or estimating cost.
- [references/templates.md](references/templates.md) — copy-paste blocks: MODULES.md, STATE.md, the four stage-start prompts, load report, routing rows, lean CLAUDE.md skeleton.
- [references/report-template.md](references/report-template.md) — the TOKEN_LEAK_AUDIT.md structure every audit delivers: findings by risk, quick wins with effort, scorecard, measurement plan. Read in Audit mode when writing the report.
- [references/strict-mode.md](references/strict-mode.md) — budget-target operation: halved stage budgets, tool-call batching, 25-line outputs, ten-turn ceiling, per-session dollar pricing. Read when a monthly target or "strict mode" is declared.
- [references/scaling.md](references/scaling.md) — the load patterns that bend the base rules: cross-domain incidents (knowledge crosses via records; contexts don't), module maps past ~25 entries (hierarchy, triage, subagent survey, stage splitting), and state bloat (rewrite-don't-append, notes.md overflow). Read when an incident spans domains, a module map outgrows flatness, or STATE.md flags over 50 lines.
- [scripts/icm_audit.sh](scripts/icm_audit.sh) — mechanical audit: sizes, oversize files, CLAUDE.md imports, MCP config, missing map/state files. Run it; don't re-derive its findings by reading files.
- [scripts/make_index.sh](scripts/make_index.sh) — generates a section index (headings, line numbers, per-section token estimates) for any large markdown file. Use it to build `.index.md` files instead of hand-writing them.
- [scripts/icm_records.sh](scripts/icm_records.sh) — the records layer: `recall` (free card search with freshness), `stamp` (anchor sha computation), `check` (staleness audit). [references/memory.md](references/memory.md) has the protocol.
- [scripts/icm_batch.sh](scripts/icm_batch.sh) — factory batching: run a queue file of tasks as isolated fresh sessions and file results for batch review. Decouples human pacing (which expires caches) from model runs.
