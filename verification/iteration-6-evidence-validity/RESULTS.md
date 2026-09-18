# Evidence validity and bounded reframing validation

Date: 2026-09-18. Baseline: `675d725b8cf94e8402933c2f8628203ef55fc508`.
This revision changes evidence-check semantics and agent instructions. It does not
claim that a creativity philosophy has been scientifically validated for software.

## What changed and why

| Change | Intended benefit | Validation |
|---|---|---|
| `UNCHANGED_EVIDENCE` replaces an unconditional trust message | Avoid endorsing conclusions from matching source bytes alone | Reproduction, CLI tests, fresh-context example |
| Optional dependency ranges or whole-file hashes | Detect a declared setting change outside the cited function | Actual function output changes 3 → 5; declared config change returns exit 1 |
| Strict evidence parsing and atomic stamp | Reject missing/malformed evidence; preserve cards after failed writes | Isolated regression tests, including permissions and line endings |
| Scope/conditions/checks/unknowns in records and handoffs | Make reuse decisions reviewable across sessions | Templates plus scoped answer in the fresh-context example |
| Conditional bounded reframing | Reopen a contradicted assumption using one discriminating check | Instruction inspection and one example; general benefit unmeasured |

## Executed checks

- **19/19 standard-library unittest methods passed**, including invalid-range
  subcases. Tests exercise the public Bash CLI in temporary directories. Coverage:
  legacy hashes, body/metadata integrity, paths with spaces, literal search, absent
  and malformed anchors, dependency drift, source deletion/change, mixed-result exit
  codes, empty directories, atomic failures, CRLF and partial-range compatibility.
- [reproduce.py](reproduce.py) passed its assertions; exact captured outputs are in
  [reproduction.json](reproduction.json). It loads the old script via `git show`
  at the baseline commit and runs the actual Python fixture in clean processes.
- Fresh-context example: four prewritten checks observed, with a manifest-confirmed
  unchanged subject. See [PROMPT.md](PROMPT.md), [fixture/](fixture/), and
  [AGENT_RESULT.md](AGENT_RESULT.md). It follows an illustrative skill example;
  it is not a held-out benchmark.
- Skill frontmatter validation (`quick_validate.py`): passed.
- Bash syntax for the public wrapper and `git diff --check`: passed.
- Packaged `.skill` ZIP: all 15 members byte-match their source; integrity passed.
- Relative Markdown link targets outside fenced examples: checked for existence.

## Controlled reproduction

| Case after config changes from 3 to 5 | Old script | New script |
|---|---|---|
| Config omitted from evidence | Calls card “trustworthy as-is”; actual answer is 5 | Reports `UNCHANGED_EVIDENCE` and explicitly says claim validity/omitted dependencies are unverified |
| Config explicitly declared with `config.py:*` | New format not supported | Reports `STALE_EVIDENCE`, names config.py, returns 1 |

The first row remains a deliberate limitation: no dependency inference was added.
Similarly, editing card prose can leave its evidence hashes unchanged. Tests preserve
these limitations explicitly rather than pretending the tool can detect them.

## Reproduce locally

```bash
python3 -m unittest discover -s tests -v
python3 verification/iteration-6-evidence-validity/reproduce.py
bash -n scripts/icm_records.sh
```

The comparison needs the baseline commit available in local git history. If using
a shallow clone that does not contain it, fetch that commit first. Python 3.8+ and
Bash are required. The tests/reproduction write only temporary fixtures.

## Limits and next measurement

These tests prove the exercised CLI contracts and show one expected instruction-following
result. They do not prove semantic truth, complete transitive/external dependency
coverage, production safety, or faster/cheaper engineering. Hashes are truncated SHA-1
for backward compatibility, not authenticated provenance. Concurrent source mutation
is not locked. Historical benchmark reports elsewhere were not rerun.

To measure broader benefit, compare A: previous skill, B: corrected records only,
and C: B plus conditional reframing on the same fixed tasks and acceptance checks.
Hold model/tool budget constant, include clear tasks that should skip reframing,
repeat with task order varied, and retain unsuccessful runs. Record task correctness,
unsupported claims, repeated attempts, loaded tokens, elapsed time, and review work.
An extra procedure is useful only if the outcome improves enough to justify its cost.
