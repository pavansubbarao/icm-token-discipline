# Fresh-context example: retained result

Run: 2026-09-18. Input: [PROMPT.md](PROMPT.md), a copy of the skill, and
[fixture/](fixture/). The evaluator had no implementation conversation or separate
answer key. It was restricted to those paths and read-only work. The evaluator's
answer is retained below with local absolute links normalized to fixture paths.

> This checkout's retry budget is **5 attempts**. `config.py` sets
> `MAX_ATTEMPTS = 5`; `worker.py` imports and returns it. A fresh Python process
> confirmed `retry_budget() = 5`.
>
> Do not rely on the saved “3 attempts” answer. Recall reported
> `UNCHANGED_EVIDENCE`, but the card hashes only `worker.py` and omits its
> configuration dependency. Unchanged declared evidence does not establish a
> correct conclusion.
>
> Scope: this checkout's local function and default configuration. Deployment
> settings, runtime overrides, and actual job-loop behavior were not inspected.
> The module map and routing file were absent; neither was created.

Reported commands: scoped `rg`, `wc`, `cat`, `sed`, `nl`; records `recall retry budget
attempts`; `python3 -I -B -S -c 'import sys; sys.path.insert(0, "."); import worker;
print("retry_budget() =", worker.retry_budget())'`.

The evaluator reported no edits/creation/restamping. A SHA-256 manifest comparison
before and after independently confirmed identical subject files and no additions.
The implementer reviewed the result against four criteria established before the
run: actual value with source evidence, rejection of the outdated answer despite
unchanged function bytes, limited scope/no savings claim, and no project edits.
All four were observed. This was manual review, not an automated accuracy score.

This is one illustrative smoke test aligned with examples in the skill, not a
held-out benchmark or an independent estimate of generalization. No old-skill
behavioral control was run, and no comparative latency/token/cost data was collected.
