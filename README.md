# icm-token-discipline

A Claude skill that enforces per-stage token discipline inside an [ICM](https://arxiv.org/abs/2603.16021)-style filesystem workspace — and audits where your Claude Code API spend actually comes from.

Folder structure controls what *can* be loaded per stage. Your bill is controlled by something else: what auto-loads at session start (CLAUDE.md and its `@`-imports, MCP tool schemas), how long conversations run (every turn re-sends the whole history — prompt caching discounts it to ~10%, it never makes it free), and how often files re-enter context. A workspace can be perfectly structured and still expensive. This skill closes that gap.

## What it does

**Audit mode** — say *"audit this workspace for token leaks"*. Runs a bundled mechanical scan (`scripts/icm_audit.sh`: entry-file size and `@`-imports, oversize markdown, CONTEXT monoliths, missing module map, missing state pattern, MCP config), then walks a measured course-correction: trim the session floor, split monoliths, build `MODULES.md`, install the `STATE.md` stage-handoff pattern, re-measure with `/context` and `/cost`.

**Discipline mode** — applies seven rules during normal work: measure before reading (grep + sliced reads, never whole files over ~8 KB); resolve the domain first and never cross into another; map before code via `MODULES.md`; one stage per session with a ≤40-line `STATE.md` handoff on disk; never re-read what's in context; close every stage with a per-file load report; send crawling to scripts and subagents.

`references/mechanics.md` documents the billing model the rules come from — per-turn resend, cache write/read economics and the ~5-minute TTL trap for human-paced sessions, the fixed per-session floor, why "four messages in one chat" barely saves anything, and where the real numbers live.

## Install

- **Claude app / Cowork:** open `dist/icm-token-discipline.skill` in a conversation and save it, or attach the file to a chat.
- **Claude Code:** clone this repo into `~/.claude/skills/icm-token-discipline` (SKILL.md sits at the repo root, so the clone is the skill).
- **Slash command (Claude Code, optional):** copy `commands/audit-token-leaks.md` into `~/.claude/commands/` (or a project's `.claude/commands/`) — then `/audit-token-leaks` runs the full audit in one keystroke. Prefer `/audittokenleaks`? Rename the file to `audittokenleaks.md`; the filename is the command.

Pairs with the [icm-architect](https://arxiv.org/abs/2603.16021) skill: that one designs the workspace; this one polices what gets loaded from it and what it costs.

## Verified results

Tested with paired agent runs — identical tasks, one agent with the skill, one without — graded against pre-established assertions. Full interactive reports are in `verification/`.

| Round | Testbed | With skill | Baseline |
|---|---|---|---|
| 1 | Synthetic incident workspace with seeded leaks | 14/14 checks | 6/14 (no skill) |
| 2 | Real public repos: OpenAI Codex monorepo, Express, Flask | 21/21 checks | 19/21 (no skill) |
| 3 | All five testbeds, v1.1 vs v1 | 42/43 checks | 36/43 (v1) |

v1.1 adds: a session guardrail (stage done → `/clear`, idle-gap warning for the ~5-minute cache expiry), the `TOKEN_LEAK_AUDIT.md` report template every audit delivers, `scripts/make_index.sh` (section indexes for big docs — in round 3 it indexed a 44k-token README without ever reading it), and conclusions-only output caps.

Highlights: on the seeded workspace the audit removed all 8 mechanical flags and cut the intake stage's resident context from ~17k to ~2.6k tokens; on the Codex monorepo the audit used 18% fewer tokens and 39% less time than baseline while finding a real leak (a 22.5 KB root AGENTS.md ≈ 5.6k tokens auto-loaded per session) and changing zero existing files. On small scoped tasks the skill's ~2k self-load makes it roughly break-even on raw tokens — its wins compound with context size and session length, which is where real bills live. Modeled per-incident cost under the skill's session pattern: 3.5–8× lower (assumptions in `references/mechanics.md`).

## Repo layout

```
SKILL.md               the skill (catalog; ~1.7k tokens when triggered)
references/            mechanics.md, audit.md, templates.md (loaded on demand)
scripts/icm_audit.sh   read-only mechanical leak scan
dist/                  packaged .skill file for the Claude app
verification/          paired-run benchmarks and interactive reports
```

## Attribution

ICM (Interpretable Context Methodology) is by Van Clief & McDermott ([arXiv:2603.16021](https://arxiv.org/abs/2603.16021), MIT-licensed). This skill is an independent runtime/cost companion written from scratch; it imports none of their files.

Built with Claude (Anthropic), including the paired-run verification harness.

## License

MIT — see [LICENSE](LICENSE).
