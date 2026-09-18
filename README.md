# icm-token-discipline

A Claude skill that enforces per-stage token discipline inside an [ICM](https://arxiv.org/abs/2603.16021)-style filesystem workspace — and audits where your Claude Code API spend actually comes from.

Folder structure controls what *can* be loaded per stage. Your bill is controlled by something else: what auto-loads at session start (CLAUDE.md and its `@`-imports, MCP tool schemas), how long conversations run (every turn re-sends the whole history — prompt caching discounts it to ~10%, it never makes it free), and how often files re-enter context. A workspace can be perfectly structured and still expensive. This skill closes that gap.

## What it does

**Audit mode** — say *"audit this workspace for token leaks"*. Runs a bundled mechanical scan (`scripts/icm_audit.sh`: entry-file size and `@`-imports, oversize markdown, CONTEXT monoliths, missing module map, missing state pattern, MCP config), then walks a measured course-correction: trim the session floor, split monoliths, build `MODULES.md`, install the `STATE.md` stage-handoff pattern, re-measure with `/context` and `/cost`.

**Discipline mode** — applies eight rules during normal work: measure before reading (grep + sliced reads, never whole files over ~8 KB); resolve the domain first and never cross into another; map before code via `MODULES.md`; one stage per session with a ≤40-line `STATE.md` handoff on disk; reuse evidence within its scope; close every stage with a per-file load report; send crawling to scripts and scoped exploration; recall and file verified, conditional records.

`references/mechanics.md` documents the billing model the rules come from — per-turn resend, cache write/read economics and the ~5-minute TTL trap for human-paced sessions, the fixed per-session floor, why "four messages in one chat" barely saves anything, and where the real numbers live.

## Install

- **Claude app / Cowork:** open `dist/icm-token-discipline.skill` in a conversation and save it, or attach the file to a chat.
- **Claude Code:** clone this repo into `~/.claude/skills/icm-token-discipline` (SKILL.md sits at the repo root, so the clone is the skill).
- **Slash command (Claude Code, optional):** copy `commands/audit-token-leaks.md` into `~/.claude/commands/` (or a project's `.claude/commands/`) — then `/audit-token-leaks` runs the full audit in one keystroke. Prefer `/audittokenleaks`? Rename the file to `audittokenleaks.md`; the filename is the command.

Pairs with the [icm-architect](https://arxiv.org/abs/2603.16021) skill: that one designs the workspace; this one polices what gets loaded from it and what it costs.

## Evidence validity and conditional reframing

The records checker reports `UNCHANGED_EVIDENCE`, not "trustworthy as-is". Cards can
track configuration and other known dependencies as well as source ranges. Invalid
records fail explicitly; failed stamping leaves the card intact. Scope, conditions,
verification, and unknowns remain human/agent judgments, not hash guarantees.

When a contradiction or repeated unproductive investigation occurs, a small optional
[reframing procedure](references/reframe.md) fixes the acceptance check, compares up
to three explanations, and runs one discriminating check. Normal tasks skip it.

| Change | Practical purpose | What remains unproven |
|---|---|---|
| Declared dependency hashes | Catch configuration drift even when the cited function is unchanged | Automatic discovery of omitted/transitive dependencies |
| Scoped record reuse | Prevent an unchanged hash from being presented as proof of the answer | Semantic correctness of every stored conclusion |
| Conditional reframing | Make a stalled assumption testable without a permanent extra stage | Lower total tokens, time, or cost on real tasks |
| Fixed acceptance and source ownership | Preserve the goal; repair the owning record after evidence | General productivity improvement |

See [current validation](verification/iteration-6-evidence-validity/RESULTS.md) for
reproduction, checks, limits, and behavioral evaluation. To run the regression suite:

```bash
python3 -m unittest discover -s tests -v
python3 verification/iteration-6-evidence-validity/reproduce.py
```

The records CLI now requires Python 3.8+ (standard library only) as well as Bash.
Existing valid range hashes remain compatible. Output labels and `recall` exit codes
changed; see the [migration contract](references/memory.md#format-and-cli-contract).

## Historical recorded examples

Earlier reports describe paired agent runs against selected tasks and assertions. They were not rerun for this change and do not establish sustained savings or general answer accuracy. Artifacts are in `verification/`.

| Round | Testbed | With skill | Baseline |
|---|---|---|---|
| 1 | Synthetic incident workspace with seeded leaks | 14/14 checks | 6/14 (no skill) |
| 2 | Real public repos: OpenAI Codex monorepo, Express, Flask | 21/21 checks | 19/21 (no skill) |
| 3 | All five testbeds, v1.1 vs v1 | 42/43 checks | 36/43 (v1) |
| 4 | Records layer on real Express + Flask | warm runs: −23–28% tokens, −46–65% time, **0 source files read**; poison test caught a deliberately falsified card | cold runs (same skill, empty memory) |

v1.3 introduced SHA-anchored records. The current revision narrows its original trust claim: unchanged cited bytes cannot rule out an outdated or incorrect answer, and hashes do not authenticate record prose. Plus `scripts/icm_batch.sh` (run a queue of tasks as isolated fresh sessions) and the free-lane/paid-lane catalog template. v1.2 adds strict mode (`references/strict-mode.md`): monthly budget targets, halved stage budgets, batched tool calls, dollar-priced load reports.

v1.1 adds: a session guardrail (stage done → `/clear`, idle-gap warning for the ~5-minute cache expiry), the `TOKEN_LEAK_AUDIT.md` report template every audit delivers, `scripts/make_index.sh` (section indexes for big docs — in round 3 it indexed a 44k-token README without ever reading it), and conclusions-only output caps.

Highlights: on the seeded workspace the audit removed all 8 mechanical flags and cut the intake stage's resident context from ~17k to ~2.6k tokens; on the Codex monorepo the audit used 18% fewer tokens and 39% less time than baseline while finding a real leak (a 22.5 KB root AGENTS.md ≈ 5.6k tokens auto-loaded per session) and changing zero existing files. These are selected historical observations. Billing estimates in `references/mechanics.md` depend on model, caching, session shape, and workload; they are not measurements of the present revision.

## Repo layout

```
SKILL.md               the skill catalog (see current validation for measured size)
references/            mechanics.md, audit.md, templates.md (loaded on demand)
scripts/               audit, records CLI (Bash + Python), indexing, batching
tests/                 isolated records CLI regressions
dist/                  packaged .skill file for the Claude app
verification/          paired-run benchmarks and interactive reports
```

## Attribution

ICM (Interpretable Context Methodology) is by Van Clief & McDermott ([arXiv:2603.16021](https://arxiv.org/abs/2603.16021), MIT-licensed). This skill is an independent runtime/cost companion written from scratch; it imports none of their files.

Architecture reference: [Jake Van Clief's ICM Architect snapshot](https://github.com/RinDig/icm-architect/tree/e16cafe6a664dcf6d787a726b452adba77d913f4), especially scoped inputs, source ownership, and progressive loading.
The reframing procedure is our engineering adaptation of [Amit Goswami's discussion
of do-be-do and conditioning](https://amitgoswami.org/2024/07/01/the-awakening-of-intelligence/).
It does not attribute these software instructions to Goswami or claim a quantum
mechanism. Engineering benefit is assessed with ordinary tests and task outcomes.

Earlier versions and paired-run harness: built with Claude (Anthropic).

## License

MIT — see [LICENSE](LICENSE).
