# Strict mode — run under a monthly dollar target

Activate when the user says "strict mode", names a monthly budget ("keep me under $100/month"), or the workspace CLAUDE.md contains a line like `icm-token-discipline: strict, budget $100/month`. Strict mode tightens every rule and prices every session in dollars, not just tokens. Deactivate the moment the user says so — this mode trades some convenience for money, and that trade is theirs to make.

## The daily allowance

Monthly target ÷ 30 = daily allowance (e.g. $100/month → ~$3.30/day). Every load report ends with the running position: estimated $ this session, and this session against the daily allowance. Price with the current model's public rates (state them once per session); tokens ÷ 1M × rate. These are estimates — `/cost` is the truth — but a session that *estimates* over allowance is over.

## Tightened rules

1. **Budgets halved.** Stage loads 1–4k tokens (was 2–8k). Session floor target ≤1k. A stage that needs more gets split, not excused.
2. **Batch tool calls — the hidden multiplier.** Every tool call is an API round trip that re-reads the whole session context. Ten small greps cost ten context re-reads; one script that does all ten costs one. In strict mode: combine file inspections into single bash commands, target ≤12 tool calls per stage, and say in the load report how many were used.
3. **Output ≤25 lines.** Conclusions and diffs only. Never restate file content, never narrate what the tool output already shows. Output tokens bill ~5× input.
4. **Subagent mandatory for exploration.** Any search that would touch more than 2 files runs in a subagent that returns ≤10 lines. The transcript never enters the main session.
5. **/clear after every completed task** — not every stage, every *task*. Ten short sessions beat one clever long one, every time, arithmetically.
6. **Ten-turn ceiling.** At 10 turns in one session, stop and recommend /clear with a STATE.md handoff, whatever the task state. Long sessions are where allowances die.
7. **No speculative loading.** Nothing is read "for context" or "just in case." If the current step doesn't need it, it isn't loaded — the index or map is consulted instead.

## Strict load report (replaces the standard one)

```
Load report (strict):
- <file>                          <KB>  ~<tok> (sliced: <range>)
Tool calls this stage: <n> (target ≤12)
Stage total: ~<tok> tokens ≈ $<amount> at <model> rates (budget 1–4k ✓/✗)
Session position: ~$<amount> of $<daily allowance> daily allowance
Session hygiene: task complete → /clear now.
```

## The two levers the model cannot pull — say them once per audit

- **Lingering sessions:** if the usage panel shows a large share from 8+ hour sessions, no in-session discipline can save the budget — the user must close leftover terminals and background loops. Name it plainly.
- **Plan sizing:** a monthly dollar target is only guaranteed by a plan whose ceiling *is* the target. If two disciplined weeks of `/cost` data fit inside a flat-rate subscription at the target price, recommend the user check current plan pricing and switch — the discipline then makes the flat plan sufficient, and the ceiling does the rest.
