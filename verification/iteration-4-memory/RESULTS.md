# Iteration 4 — records layer ("knowledge annuity") verified on real repos
Date: 2026-08-21 · Repos: expressjs/express, pallets/flask (fresh clones) · Skill: v1.3

## Design
Cold run: agent answers a real code question with full discipline AND files an anchored record card
(.icm/records/*.md, per-anchor line-range SHA). Warm run: fresh agent, same question — must recall the
card, sha-verify anchors, and answer without re-deriving. Poison run (express): anchored code mutated
(default 'weak'→'strong') so the card is factually wrong — the guard must catch it, not serve it.

## Results (subagent totals incl. fixed overhead; correctness checked against pre-established ground truth)
| Run | Tokens | Tool calls | Time | Behavior |
|---|---|---|---|---|
| express cold | 62,079 | 19 | 188s | derived from source, filed 6-anchor card |
| express warm | 47,474 (−23.5%) | 6 | 101s | answered from FRESH card, 0 source files read |
| express poison | 49,850 | 10 | 97s | detected 1 STALE anchor, re-verified only that slice, reported the NEW truth ('strong'), updated + re-stamped card |
| flask cold | 62,562 | 16 | 206s | derived, filed 6-anchor card |
| flask warm | 45,306 (−27.6%) | 4 | 73s | answered entirely from FRESH card, 0 source reads |

Marginal analysis load (excluding fixed skill/system overhead): cold ~2.6–4.4k tokens of repo reads →
warm ~0.45–0.85k (card + one insurance grep): a 70–80% collapse in the part that compounds per-turn.
All five answers matched ground truth; the poison run corrected the card rather than serving it.

## Mechanical tests (free, scripted)
- recall precision: correct card ranked first among decoys, anchors inline-verified
- staleness: mutating one anchored line flips exactly that card to STALE (exit 1); restore → FRESH
- batch runner: dry-run + stub execution verified (per-task isolation, outputs, summary). The
  `claude -p` invocation itself was not executable in the build sandbox — harness-level verification only.

## Honest limits
Two repos, one question each; totals include ~40k+ fixed agent overhead on both sides (the delta
understates interactive savings, where the recalled card also keeps the resident context small);
card quality depends on the cold run's diligence; records ride in git — do not file secrets.
