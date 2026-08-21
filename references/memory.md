# The records layer — never pay for the same judgment twice

Every answer that took real reading gets filed once as an anchored card in `.icm/records/`. Every later question starts with a free grep of those cards. A fresh hit answers for the cost of a card (~300–600 tokens) instead of the cost of re-deriving it (3–10k+). Over weeks, the workspace learns and sessions get cheaper — the annuity.

Three verbs, all free (no model tokens): `scripts/icm_records.sh recall|stamp|check`.

## Protocol

**Before any analysis** (rule 8): run `icm_records.sh recall <3-6 distinctive words from the question>`.
- **FRESH hit** → answer from the card. Cite it. Load at most one anchor slice to quote exact code if the user needs it. Do not re-derive what the card already settles.
- **STALE hit** → the anchored content changed since filing. Say so, re-verify only the stale anchors (slice those ranges, compare), update the card, re-`stamp`. Never silently trust a stale card — and never silently discard one either; the diff between card and code is usually the fastest path to the new answer.
- **No hit** → proceed with normal disciplined analysis.

**After any answer that took real reading** (more than ~2k tokens of loads): file a card.
1. Write `.icm/records/<slug>.md` — question line, anchors list, answer ≤20 lines with `file:line` citations. Template below.
2. `icm_records.sh stamp .icm/records/<slug>.md` — computes the sha for each anchor range.
3. Mention the filing in the load report ("filed: <slug>.md").

**Anchors are the safety.** A card's authority comes from its anchors: exact `path:start-end` ranges whose content hash is stored. `check` (run it in every audit, and in CI freely — it's a plain script) tells you which cards still stand. A memory layer without staleness detection is a wrong-answer generator; this one refuses to be.

## Card template

```markdown
---
q: where does express set the etag header and under what conditions
anchors:
- lib/response.js:180-195 sha:000000000000
- lib/utils.js:125-155 sha:000000000000
- lib/application.js:90-100 sha:000000000000
filed: 2026-08-21
---
ETag is set in res.send (lib/response.js ~186-191): only when no ETag header exists,
app's 'etag fn' is a function, and a body is present. The fn comes from app.set('etag', v)
compiling via compileETag (lib/utils.js:130). Default: 'weak' (lib/application.js:95).
res.sendFile delegates: opts.etag = app.enabled('etag') (lib/response.js:402).
```

(Sha fields start as zeros; `stamp` fills them.)

## What deserves a card

File: root-cause conclusions, "where/how does X work" findings, configuration meanings, decisions with reasons. Don't file: trivia a grep answers instantly, anything speculative, secrets, or content from files you're not permitted to copy — cards go wherever the workspace goes.

## Hygiene

- One card per question; a new answer to the same question **updates** the card (one home per fact).
- Cards are ≤25 lines. A card that wants to be longer is a document, not a record — link it instead.
- `icm_records.sh check` in every audit; delete cards whose subject no longer exists.
- Records are plain files in the repo: they ride along in git, review like code, and cost nothing until read.
