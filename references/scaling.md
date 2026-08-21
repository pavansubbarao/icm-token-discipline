# Scaling — where the architecture bends before it breaks

Three load patterns stress the base rules: incidents that span domains, module maps that outgrow
flatness, and state that accumulates across stages. Each has a protocol. The base rules never
break silently — every exception is declared in the load report.

## 1. Cross-domain incidents — knowledge crosses, contexts don't

"One domain per session" stands. What crosses domains is *findings*, carried by the records layer:

1. The incident lands in its **primary** domain (where the symptom is). Work it normally.
2. When the cause points into another domain, do NOT load that domain's catalogs. First
   `icm_records.sh recall` — a sibling incident may already have filed the answer as a card.
3. If no card exists, open a **linked incident** in the other domain (its own sessions, its own
   budget). Both STATE.md files carry `related: INC-xxxx`. The diagnosing session files a card;
   the symptom session recalls it (~500 tokens) instead of re-deriving.
4. Declared exception: when one session genuinely must weigh both domains at once, load at most
   the two SEVERITY/topic files it needs (~2k), never both full catalogs, and say so in the load
   report ("cross-domain exception: tech-ops + manufacturing severity files").

## 2. Module explosion — hierarchy, triage, survey, split

A flat MODULES.md works to ~25 modules. Beyond that:

- **Go hierarchical.** MODULES.md becomes a catalog of subsystems (one line each) pointing at
  per-subsystem maps (`02-analyze/maps/<subsystem>.md`). Each level links down and stops.
- **Triage before reading.** An incident that "touches 8–12 modules" almost never has 8–12 causes.
  Use the map + dependency lines to pick the 2–3 causal candidates; slice only those.
- **Survey by subagent.** The remaining suspects get one subagent sweep ("check these N modules
  for <symptom>; return ≤10 lines") — the survey transcript never enters the main session.
- **Split the stage, not the budget.** If candidate reads still exceed ~8k, the stage divides:
  02a-locate (map + triage + survey, ≤4k) hands STATE.md to 02b-inspect (sliced reads of the
  named candidates). Two small sessions beat one bloated one — same arithmetic as always.

## 3. State bloat — rewrite, don't append

STATE.md is a bus, not a journal. Hard cap ~40 lines at every handoff:

- Each stage **rewrites** the findings section — conclusions supersede their evidence trail
  (one home per fact). Stage 4's STATE.md is not stage 1's plus three appendices.
- Overflow that genuinely must persist (long evidence, command output, timelines) goes to
  `incidents/<id>/notes.md` — linked from STATE.md, loaded only on demand, never by default.
- The files-consulted list stays, but collapsed: paths only, superseded slices pruned.
- Mechanical check: `wc -l incidents/*/STATE.md` in every audit; >50 lines is a flag.

## When to act

Adopt these the day the trigger appears in real data — a first cross-domain incident, a MODULES.md
crossing ~25 rows, a STATE.md flagged over 50 lines — not before. Premature hierarchy is its own
token tax: an extra catalog level costs a hop on every walk.
