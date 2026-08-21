#!/usr/bin/env bash
# icm_records.sh — the knowledge annuity: file answered judgments once, recall them free.
# Records live in .icm/records/*.md with SHA-anchored citations, so staleness is detectable.
#
# Usage (from the workspace root):
#   icm_records.sh recall <query words...>   find matching records, show freshness (free, no AI)
#   icm_records.sh stamp  <card.md>          compute/refresh the sha for each anchor line-range
#   icm_records.sh check  [records_dir]      verify every record's anchors; report FRESH/STALE
#
# Card format (markdown, ≤ ~25 lines):
#   ---
#   q: where does express set the etag header
#   anchors:
#   - lib/response.js:180-195 sha:xxxxxxxxxxxx
#   - lib/utils.js:125-155 sha:xxxxxxxxxxxx
#   filed: 2026-08-21
#   ---
#   <the answer, with file:line citations>
# Portable bash 3.2+; read-only except 'stamp' (rewrites sha fields in the named card).

set -u
CMD="${1:-}"; shift 2>/dev/null || true
DIR=".icm/records"

range_sha() { # $1=path $2=start $3=end -> 12-hex sha of that line range's content
  sed -n "${2},${3}p" "$1" 2>/dev/null | sha1sum | cut -c1-12
}

anchor_status() { # $1=card -> prints per-anchor lines "FRESH|STALE|MISSING path:range"; rc: 0 all fresh
  local rc=0 line path range start end want have
  while IFS= read -r line; do
    case "$line" in
      "- "*" sha:"*)
        path="${line#- }"; path="${path%% *}"
        range="${path##*:}"; path="${path%:*}"
        start="${range%-*}"; end="${range#*-}"
        want="${line##*sha:}"
        if [ ! -f "$path" ]; then echo "MISSING $path:$range"; rc=1; continue; fi
        have=$(range_sha "$path" "$start" "$end")
        if [ "$have" = "$want" ]; then echo "FRESH $path:$range"
        else echo "STALE $path:$range (content changed)"; rc=1; fi ;;
    esac
  done < "$1"
  return $rc
}

case "$CMD" in
  recall)
    [ $# -ge 1 ] || { echo "usage: icm_records.sh recall <query words...>" >&2; exit 2; }
    [ -d "$DIR" ] || { echo "no records yet ($DIR absent) — cold workspace, proceed with analysis and file a card after."; exit 1; }
    # score every card by how many query words it contains (case-insensitive)
    best=""; for f in "$DIR"/*.md; do
      [ -f "$f" ] || continue
      score=0
      for w in "$@"; do
        [ ${#w} -lt 3 ] && continue
        grep -q -i -- "$w" "$f" && score=$((score+1))
      done
      [ "$score" -gt 0 ] && best="$best$score $f\n"
    done
    hits=$(printf "%b" "$best" | sort -rn | head -3)
    [ -n "$hits" ] || { echo "no matching record — proceed with analysis and file a card after."; exit 1; }
    echo "=== record hits (best first) ==="
    printf "%s\n" "$hits" | while read -r score f; do
      [ -n "${f:-}" ] || continue
      echo "--- $f (score $score) ---"
      if anchor_status "$f" >/tmp/icm_anch.$$ 2>&1; then echo "[ALL ANCHORS FRESH — the card below is trustworthy as-is]"
      else echo "[STALE ANCHORS — content moved since filing; re-verify before trusting]"; fi
      cat /tmp/icm_anch.$$; rm -f /tmp/icm_anch.$$
      cat "$f"
    done
    ;;
  stamp)
    CARD="${1:-}"; [ -f "$CARD" ] || { echo "usage: icm_records.sh stamp <card.md>" >&2; exit 2; }
    TMP=$(mktemp)
    while IFS= read -r line; do
      case "$line" in
        "- "*:*-*)
          spec="${line#- }"; spec="${spec%% sha:*}"
          path="${spec%:*}"; range="${spec##*:}"
          start="${range%-*}"; end="${range#*-}"
          if [ -f "$path" ]; then echo "- $spec sha:$(range_sha "$path" "$start" "$end")"
          else echo "$line  # WARNING: file not found"; fi ;;
        *) echo "$line" ;;
      esac
    done < "$CARD" > "$TMP" && mv "$TMP" "$CARD"
    echo "stamped: $CARD"; anchor_status "$CARD"
    ;;
  check)
    D="${1:-$DIR}"; [ -d "$D" ] || { echo "no records dir: $D"; exit 1; }
    rc=0
    for f in "$D"/*.md; do
      [ -f "$f" ] || continue
      if out=$(anchor_status "$f") && true; then echo "FRESH  $f"
      else echo "STALE  $f"; echo "$out" | grep -vE "^FRESH" | sed 's/^/       /'; rc=1; fi
    done
    exit $rc
    ;;
  *)
    echo "usage: icm_records.sh {recall <words...> | stamp <card> | check [dir]}" >&2; exit 2 ;;
esac
