#!/usr/bin/env bash
# icm_audit.sh — mechanical token-leak scan for an ICM workspace.
# Run from the workspace root:  bash scripts/icm_audit.sh  (or bash path/to/icm_audit.sh)
# Read-only: prints a report, changes nothing. Portable bash 3.2+ (macOS ok).

set -u
ROOT="${1:-.}"
cd "$ROOT" || { echo "cannot cd to $ROOT"; exit 1; }

FLAGS=0
est_tok() { echo $(( ${1:-0} / 4 )); }
fsize() { wc -c < "$1" 2>/dev/null | tr -d ' '; }
flines() { wc -l < "$1" 2>/dev/null | tr -d ' '; }
flag() { FLAGS=$((FLAGS+1)); printf '  [FIX] %s\n' "$1"; }
ok()   { printf '  [ok]  %s\n' "$1"; }

echo "=== ICM token audit — $(pwd) ==="
echo
echo "-- 1. Entry file (auto-loaded into EVERY session)"
ENTRY=""
for f in CLAUDE.md AGENTS.md; do [ -f "$f" ] && ENTRY="$f" && break; done
if [ -z "$ENTRY" ]; then
  flag "no CLAUDE.md at root — routing lives nowhere stable"
else
  L=$(flines "$ENTRY"); B=$(fsize "$ENTRY")
  printf '  %s: %s lines, %s bytes (~%s tok) auto-loaded per session\n' "$ENTRY" "$L" "$B" "$(est_tok "$B")"
  [ "$L" -gt 60 ] && flag "$ENTRY over 60 lines — move content down, keep routing only" || ok "size within catalog budget"
  IMPORTS=$(grep -nE '(^|[[:space:]])@[[:alnum:]_./-]+' "$ENTRY" 2>/dev/null || true)
  if [ -n "$IMPORTS" ]; then
    flag "@-imports found — each one auto-loads that file into every session:"
    echo "$IMPORTS" | while IFS= read -r line; do printf '        %s\n' "$line"; done
  else
    ok "no @-imports"
  fi
fi
[ -f "$HOME/.claude/CLAUDE.md" ] && {
  B=$(fsize "$HOME/.claude/CLAUDE.md")
  [ "${B:-0}" -gt 2000 ] && flag "~/.claude/CLAUDE.md is $B bytes (~$(est_tok "$B") tok) — user-level, rides into every session of every project" \
                         || ok "~/.claude/CLAUDE.md small ($B bytes)"
}

echo
echo "-- 2. Oversize markdown (whole-file loads that bust a 2-8k stage budget)"
find . \( -path ./node_modules -o -path ./.git -o -path ./_archive \) -prune -o -type f -name '*.md' -print 2>/dev/null |
while IFS= read -r f; do
  B=$(fsize "$f")
  [ "${B:-0}" -gt 24000 ] && printf '  [FIX] %-52s %7s bytes ~%s tok — split or slice; never load whole\n' "$f" "$B" "$(est_tok "$B")"
done > /tmp/icm_audit_big.$$ || true
if [ -s /tmp/icm_audit_big.$$ ]; then sort -rn -k2 /tmp/icm_audit_big.$$; FLAGS=$((FLAGS+1)); else ok "no markdown over ~6k tokens"; fi
rm -f /tmp/icm_audit_big.$$

echo
echo "-- 3. Domain CONTEXT monoliths (split into SEVERITY/SLA/ESCALATION/REMEDIATION)"
FOUND_D=0
for f in domains/*/CONTEXT.md; do
  [ -f "$f" ] || continue
  FOUND_D=1; B=$(fsize "$f")
  if [ "${B:-0}" -gt 12000 ]; then
    flag "$f: $B bytes (~$(est_tok "$B") tok) — multi-topic monolith; split by heading (audit.md step 3)"
  else
    d=$(dirname "$f")
    SPLITS=$(ls "$d" 2>/dev/null | grep -cE '^(SEVERITY|SLA|ESCALATION|REMEDIATION)\.md$')
    ok "$f: $B bytes; $SPLITS/4 per-topic files present"
  fi
done
[ "$FOUND_D" -eq 0 ] && echo "  (no domains/*/CONTEXT.md found)"

echo
echo "-- 4. Module map (rule 3: map before code)"
if [ -f 02-analyze/MODULES.md ]; then
  ok "02-analyze/MODULES.md present ($(fsize 02-analyze/MODULES.md) bytes)"
else
  M=$(find . -maxdepth 3 -name 'MODULES.md' -not -path './.git/*' 2>/dev/null | head -1)
  [ -n "$M" ] && ok "module map at $M" || flag "no MODULES.md — code gets loaded unmapped; create from templates.md (audit.md step 4)"
fi

echo
echo "-- 5. State pattern (rule 4: one stage per session needs STATE.md handoff)"
if find incidents -name 'STATE.md' -print -quit 2>/dev/null | grep -q . ; then
  N=$(find incidents -name 'STATE.md' 2>/dev/null | wc -l | tr -d ' ')
  ok "incidents/ state pattern in use ($N STATE.md files)"
  find incidents -name 'STATE.md' 2>/dev/null | while IFS= read -r f; do
    L=$(flines "$f"); [ "${L:-0}" -gt 50 ] && printf '  [FIX] %s is %s lines — cap ~40; it is re-paid in every later stage\n' "$f" "$L"
  done
else
  flag "no incidents/*/STATE.md — stages cannot hand off without dragging conversation history (audit.md step 5)"
fi

echo
echo "-- 6. MCP servers (schemas load into every session's floor)"
if [ -f .mcp.json ]; then
  N=$(grep -cE '"[^"]+"[[:space:]]*:[[:space:]]*\{' .mcp.json 2>/dev/null); [ -n "$N" ] || N=1
  grep -q '"mcpServers"' .mcp.json 2>/dev/null && [ "$N" != "?" ] && N=$((N-1))
  echo "  .mcp.json present (~$N server entries) — each adds schema tokens to every session; prune unused (mechanics.md §9)"
else
  echo "  no project .mcp.json — check 'claude mcp list' for user-level servers riding into this workspace"
fi

echo
echo "=== Result: $FLAGS structural flag group(s) above marked [FIX] ==="
echo "Next: fix floor items first (section 1, 6), then splits (2, 3), then map/state (4, 5)."
echo "Real numbers: fresh session -> /context for the floor; /cost after a typical incident."
