# Conditional reframing

Load only when evidence contradicts the current explanation, a material dependency
is unknown, or two attempts repeat the same explanation without new evidence.
A clear task with matching evidence proceeds normally. This is an optional procedure
inside the active stage, not another mandatory stage or another agent.

## One bounded pass

1. **Fix the contract.** State the requested result and the acceptance check. Keep
   the domain, permitted changes, and output artifact from the current stage.
   Resolve input paths for this incident now; a generic folder name is not an input.
2. **Separate observation from assumption.** Record the observed failure and the
   unsupported premise in at most two bullets. Pause commitment to that premise;
   waiting, meditation, or extra sampling is not required.
3. **Compare at most three explanations.** Include a different mechanism or layer
   (for example configuration vs implementation). For each, give one observation
   that would support or rule it out. Use short decision notes, not a reasoning dump.
4. **Run one discriminating check.** Choose the smallest authorized read, test, or
   experiment whose possible outcomes separate the explanations. Repeating the same
   search or asking a model to agree is not independent evidence. Use a fixture for
   mutations. Never broaden permissions because an investigation stalled.
5. **Close with evidence.** Update the owning record or stage state: observation,
   affected conclusion, scope, dependencies, verification, and remaining unknowns.
   Preserve the original acceptance check. If unresolved, record the precise missing
   input and stop this pass; do not loop or turn a hypothesis into a verified card.

The next action may be another already-authorized task step. Reframing itself stops
after this pass; escalating its budget requires a concrete reason, not more guesses.

## Compact decision record

Use the existing STATE.md or a linked incident note; do not create a parallel memory
system. Keep stable procedures in stage references and this incident's evidence in
its state/outputs. Repair the stage reference only when evidence supports a reusable
rule, and retain any failing fixture as a regression test.

```markdown
Contract: <result, allowed scope, acceptance check>
Observed: <result with source/check>
Assumption reopened: <specific premise>
Candidates: <up to three; each with a distinguishing observation>
Check: <one command/read and result>
Decision: <supported conclusion or unresolved; conditions and unknowns>
Owner updated: <record/state/reference path>
```

Example: a cached record says a retry budget is 3; its function hash is unchanged,
but a fresh local run returns 5. Compare a function change, imported configuration,
and a runtime override. Inspect the import/configuration and run a clean process.
A changed config can explain the mismatch; the unchanged function alone cannot.
Declare that dependency in the corrected record. Do not infer production behavior
from a local test with no deployment evidence.

## Why this belongs in ICM

This adapts the requested Goswami-inspired alternation between focused effort and
reconsideration into an observable engineering procedure. It makes no claim that
consciousness or quantum effects improve software. ICM supplies the routing, scoped
inputs, reviewable outputs, and source ownership. Benefits must be measured against
ordinary ICM: fewer unsupported conclusions or repeated attempts, without unacceptable
extra tokens, time, or review work. No speed or cost improvement is assumed.
