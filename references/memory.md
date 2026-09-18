# Records: reuse a conclusion within its evidence and scope

Keep answered questions in `.icm/records/`. Recall can avoid repeated exploration,
but matching hashes establish only that declared source bytes have not changed.
They cannot establish that a conclusion was correct, is applicable now, or lists
every dependency. Reading command output still consumes model context.

Run `scripts/icm_records.sh recall|stamp|check` from the subject workspace root.
Requires Bash and Python 3.8+; no third-party Python packages or model calls.

## Reuse protocol

Before analysis, `recall <3-6 distinctive words>`. Search is case-insensitive,
literal, and returns at most three cards; query words shorter than three characters
are ignored. Discovery is a convenience, not a completeness check.

| Result | What to do |
|---|---|
| `UNCHANGED_EVIDENCE` | Check that the question, configuration, scope, verification method, and known dependencies match. Reuse a supported conclusion only within those conditions. |
| `STALE_EVIDENCE` | Inspect the changed/missing evidence and its effect on the claim. Update the answer and verification before restamping. |
| `INVALID_RECORD` | Repair the format or citation; do not treat a parsing failure as evidence of freshness. |
| No hit | Continue scoped analysis. |

Legacy cards still load, but absent scope/dependency/check metadata is **unknown**,
not implicit verification. A contradiction overrides an unchanged hash: inspect
the smallest relevant source or configuration, even if it was consulted before.
If the investigation repeats without new evidence, use [reframe.md](reframe.md).
Never restamp merely to silence a failure.

## Card template

The example is illustrative; substitute real paths, scope, revision, and checks.
Keep a card around 25 lines. Link a longer evidence record rather than copying it.

```markdown
---
q: what is the retry budget
claim_status: verified
scope: local worker with repository defaults
conditions: no runtime override; config loaded at process start
anchors:
- worker.py:1-3 sha:000000000000
dependencies:
- config.py:* sha:000000000000
verified_at_revision: <immutable commit>
verification: <command or source check and observed result>
unknowns: deployed overrides not inspected
filed: YYYY-MM-DD
---
The local retry budget is 3 (worker.py:retry_budget, config.py:MAX_ATTEMPTS).
Deployment values are outside this claim's scope.
```

`claim_status: verified` is an author's evidence-backed judgment. The script never
sets or validates it. Record hypotheses in STATE.md/open questions instead of
presenting them as established answers. Metadata carries scope, not extra authority.

After a useful answer: write the scoped conclusion and its verification, list
its anchors **and the known dependencies capable of changing it**, then `stamp`
the card and mention it in the load report. Configuration, schemas, registries,
consumers, and external versions may matter even when the cited function is stable.
For external evidence, cite its version in prose; a local hash does not check a
remote service. If a material dependency is unknown, narrow the answer or inspect it.

## Format and CLI contract

- Frontmatter starts and ends with `---`. Exactly one `anchors:` block contains
  at least one `- path:start-end sha:xxxxxxxxxxxx` row. Optional `dependencies:`
  uses the same syntax. `path:*` hashes the whole file. Paths are relative to the
  workspace root (spaces supported); ranges are inclusive, one-based, and in bounds.
- This is a constrained evidence-list format, not a general YAML parser: no quoted
  paths, inline lists of citations, or multiline evidence rows. Other metadata is
  preserved, not semantically validated. Empty `dependencies: []` is allowed.
- SHA values retain the legacy 12-hex SHA-1 format for compatibility. They detect
  ordinary byte drift; they are not cryptographic provenance or a security boundary.
- `stamp <card>` permits omitted hashes/zero placeholders. It validates all evidence
  before atomically replacing the card, preserving its permissions and other text.
  Missing evidence or invalid ranges leave the card unchanged. It does not verify
  the answer, lock the source tree, or discover transitive dependencies.
- `check [records_dir]` checks all top-level `*.md` cards. `recall` checks returned
  hits. Exit **0**: all checked evidence unchanged; **1**: stale/missing evidence,
  no records, or no search hit; **2**: invalid record, usage, or I/O error. Mixed
  results return the highest code. These codes do not score answer correctness.

Migration: old `FRESH`/`STALE` output labels are replaced. `recall` now returns a
nonzero status for stale/invalid hits, and empty directories no longer pass.
Update callers that parse those labels or run under `set -e`. Existing valid range
hashes remain compatible; reviewing legacy cards does not require mass restamping.

One question has one owning card. Keep citations and unresolved limits when rewriting
it. Run `check` during an audit, then review scope and coverage separately. Remove or
archive obsolete cards deliberately; do not delete merely because a citation moved.
