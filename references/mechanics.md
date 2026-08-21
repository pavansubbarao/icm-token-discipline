# How the bill actually works (Claude Code on API billing)

Read this before explaining, estimating, or promising token savings. Every claim here is about mechanics the folder structure cannot see. Prices and cache parameters drift — treat the ratios below as typical and check docs.claude.com/en/docs/about-claude/pricing for current numbers before quoting any.

## 1. Every turn re-sends the whole conversation

An API call's input is the entire conversation so far: system prompt, tool schemas, every file ever read this session, every tool result, every reply. "Claude remembers CLAUDE.md from session memory" means Claude doesn't need to *re-read the file* — it does **not** mean those tokens stop being billed. They ride along as input on every remaining turn.

Consequences:

- Cost per turn grows roughly linearly with session length. A 40-turn session ends up paying for its early file loads dozens of times (at cache-read discount).
- A file read **late** in a session costs less over its lifetime than the same file read early.
- Ending a session is the only way to stop paying for its history.

## 2. Prompt caching softens this — it doesn't remove it

Claude Code caches automatically. Roughly: writing new content to cache costs a small premium over base input (~1.25×); re-reading cached content costs ~0.1× base input. The cache expires after a few minutes of inactivity (TTL refreshes on use), so a session resumed after a break re-pays cache writes on its whole history.

So the steady state of a long session is: each turn pays ~10% price on everything old plus full price on everything new. Ten percent of a 150k-token history, every turn, on every incident, every day — that is where "structure improved but the bill didn't" usually lives.

## 3. The session floor

Before any workspace file is loaded, every session already carries: the system prompt and built-in tool schemas, every connected MCP server's tool schemas, installed skills' metadata, the project CLAUDE.md, the user-level `~/.claude/CLAUDE.md`, and **every file CLAUDE.md `@`-imports**. This floor is paid at session start and rides in every turn.

Measure it: fresh session, `/context`, before doing anything. If the floor is 20k tokens, a stage that loads a disciplined 2k of workspace files still bills 22k+ on its first turn — the stage budget is invisible in the bill. Trimming the floor (audit.md steps 2) is usually worth more than any single file split.

## 4. Why "four messages in one chat" barely saves anything

The staged-messages pattern is often taught as: message 1 loads ~1.5k, message 2 ~4k, message 3 ~1.5k, message 4 ~2.5k → "total ~9.5k instead of 25k". That accounting counts only *newly loaded files*. In one conversation, message 4's input actually contains messages 1–3, their file loads, and their outputs — plus the floor, four times. The version of staging that genuinely works:

- **Four sessions**, not four messages.
- A ≤40-line `STATE.md` on disk is the only thing that crosses the boundary.
- Each session = floor + STATE.md + that stage's files, and dies before its history compounds.

Worked comparison (floor 15k, stages loading 2k/4k/2k/3k of files, ~3 turns per stage, ignoring outputs): one conversation ≈ floor + accumulating history re-sent each of ~12 turns — order 300–400k billed input-token-equivalents; four fresh sessions ≈ 4 × (floor + stage files) × ~3 turns with cache discounts — order 150–200k, and the gap widens with every extra turn and every extra incident. Numbers are illustrative; the shape is not.

## 5. Tool results are permanent residents

Every Read result, grep output, and command output stays in the session context. A 3k-token file read on turn 3 of a 30-turn session is paid once at full rate and ~27 more times at cache rate. This is why rule 1 (measure, then read narrow) and rule 4 (short sessions) work: they shrink the resident set and how long it stays resident.

## 6. Output tokens cost ~5× input

Verbose stage reports can cost more than the files the stage loaded. Keep stage outputs to the contract: classification, findings, validation verdict, steps — no restating file contents back at the user.

## 7. "Already on Haiku and still expensive" — the volume diagnosis

Cheap models make per-token cost low; steady daily spend on cheap models means input volume is enormous — floor × sessions/day × turns/session × history length. The levers in order of typical impact:

1. Session length (rule 4 — stage-per-session with STATE.md)
2. Session floor (MCP pruning, CLAUDE.md imports — audit.md)
3. Resident set per session (rules 1, 3, 5 — narrow reads, no re-reads)
4. Output verbosity (rule 6)
5. Model tier per stage (last, and already partly done if on a mix)

## 8. Where real numbers live

Claude cannot see the billing meter; bytes ÷ 4 is an estimate for planning only. Real numbers: `/context` (what's in the window right now, including the floor), `/cost` (this session's spend on API billing), and the Anthropic Console usage page (daily totals per model, cache hit rates). Anchor before/after claims to `/cost` on a comparable incident, never to estimates.

## 9. MCP and skills hygiene

Every connected MCP server contributes tool schemas to every session's floor, used or not. For a dedicated incident-management workspace, keep only the servers the pipeline actually calls (project-scoped `.mcp.json`; `claude mcp list` to see what's connected). Skill metadata also sits in the floor — keep installed-skill descriptions short and few.

## 10. The billing-plan check

A steady $25–30/day of metered API spend is ~$750–900/month. Claude Code also runs on Pro/Max subscriptions, which are flat-rate with usage limits. Whether a subscription beats metered at the user's volume depends on current plan pricing and limits — flag the comparison, point at anthropic.com/pricing and the Console's usage page, and let the user do the arithmetic with live numbers. For sustained daily use, this single administrative change often outweighs every prompt-level optimization combined; it changes what a token costs instead of how many are spent.
