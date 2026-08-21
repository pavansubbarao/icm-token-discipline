# TOKEN_LEAK_AUDIT.md — report template

Every audit ends by writing this report into the workspace root. Fill every `<placeholder>`; delete sections that genuinely don't apply (say so in the scorecard rather than silently dropping them). Two accuracy rules govern the whole document: every number comes from a measurement (`wc -c`, the audit script, `/context`, `/cost`) — never from vibes; and annual/dollar figures price each token once at the current model's input rate — say so explicitly, and note that per-turn resend makes real savings larger than the printed figure.

```markdown
Token Leak Audit Report — <workspace name>
Date: <YYYY-MM-DD>
Status: <PRE|POST> token discipline installation
Scan: icm_audit.sh from <skill source>

Executive Summary
✅|⚠️ <one line per major finding or fix, measured: "77.8% session floor reduction (CLAUDE.md 7.5K → 1.6K)">
Overall: <N>% of leaks fixed, <M>% remain (<where the remainder lives>).

Leak Analysis

1. Session Floor (AUTO-LOADED EVERY SESSION)
   Status: <FIXED|LEAKING>
   Before: <lines> lines, <bytes> bytes (~<tok> tokens)
   After:  <lines> lines, <bytes> bytes (~<tok> tokens)
   Savings: <tok> tokens per session (and re-billed every turn — real savings exceed this)

2. Oversize Docs (LEAKED IF LOADED)
   <for each file:> <path> — <bytes> bytes → ~<tok> tokens — Risk: <High|Medium|Low> (<why: load frequency>)
   Total if ALL loaded: <bytes> → ~<tok> tokens

3. Module map / 4. State pattern / 5. MCP floor — <status, before/after, savings>

Leak Patterns
Pattern <n>: <name> (<count> docs)
  Issue: <how the tokens actually leak — loading whole for one section, copy-paste into incidents, …>
  Fix: <concrete restructure, with target tree>
  Savings if fixed: ~<tok> per <use|lookup|incident>

Current Leaks By Risk
High (frequently loaded):   <files + tokens>  Subtotal: <tok> — at <N> loads/month = <tok>/month
Medium (occasionally):      <…>
Low (rarely):               <…>
Total leak if all loaded actively: ~<tok>/year (≈ $<amount>/year at <model> input rates — resend makes the true figure higher)

Fixable Leaks (Quick Wins)
Fix <n>: <name> (<minutes> min)
  BEFORE: <tree/line with tokens per use>
  AFTER:  <tree with index/copy-me/archive structure and tokens per use>
  Savings: <tok> per <use>; annual (<N> uses): <tok>

Remaining Structural Issues
✗ Issue <n>: <name> (Rule <n>) — Status / Impact / Fix / Savings

Audit Scorecard
| Item | Before | After | Status |
|---|---|---|---|
| Session floor | <tok> | <tok> | ✅ Fixed |
| MODULES.md | Missing | Present | ✅ Fixed |
| Oversize docs | <n> files | <n> files | ⚠️ Remain (<priority>) |
| STATE.md pattern | Missing | Template ready | ⏳ Activates next incident |

Actionable Next Steps
Immediate (done now): <what the audit already fixed>
Short-term (next incident): <rule-3 behaviors + expected savings>
Medium-term (next multi-stage incident): <STATE.md activation + expected savings>
Long-term (cleanup): <doc splits/indexes/archives + effort + savings>

Measurement Plan
Check 1 (this session): /context → <expected floor number>
Check 2 (next incident, ~1 week): /cost → expect <tok> vs baseline <tok> (<%> reduction, rule 3)
Check 3 (next multi-stage incident, ~2 weeks): sum of all stage sessions' /cost → expect <tok> vs baseline <tok> (<%> reduction, rule 4)

Leak Severity Summary
| Severity | Count | Annual cost | Fixability | Effort |
|---|---|---|---|---|
| <rows from measured data> |

Conclusion
<3–5 checkmark lines: what's fixed, what's active, what's identified, what activates next>
Bottom line: <one sentence a non-reader can act on>.
```

Why this shape: the executive summary and bottom line serve whoever pays the bill; the risk tables and patterns serve whoever does the fixes; the measurement plan makes the report falsifiable — every expected number can be checked against `/context` and `/cost` on a named date, which is what separates an audit from an opinion.
