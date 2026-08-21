#!/usr/bin/env bash
# icm_batch.sh — factory batching: run queued tasks as isolated fresh sessions.
# Decouples human time from model time: you queue tasks all day (free), then one
# burst runs each as its own tiny session — no idle cache expiry, no history
# compounding, results filed for batch review (the ICM human gate).
#
# Queue file: one task per line. Blank lines and #comments ignored.
# Usage:  icm_batch.sh <queue.txt> [outdir]      (default outdir: _batch/<timestamp>)
#         icm_batch.sh --dry-run <queue.txt>     show what would run, run nothing
# Runner: each task runs as   claude -p "<task>"   in the current directory.
#         Override with BATCH_CMD (e.g. BATCH_CMD="claude -p --model haiku").
set -u
DRY=0; [ "${1:-}" = "--dry-run" ] && { DRY=1; shift; }
Q="${1:-}"; [ -f "$Q" ] || { echo "usage: icm_batch.sh [--dry-run] <queue.txt> [outdir]" >&2; exit 2; }
OUT="${2:-_batch/$(date +%Y%m%d-%H%M%S)}"
RUNNER="${BATCH_CMD:-claude -p}"

n=0; ok=0; fail=0
mkdir -p "$OUT"
while IFS= read -r task; do
  case "$task" in ""|\#*) continue ;; esac
  n=$((n+1)); id=$(printf "%03d" "$n")
  if [ "$DRY" = 1 ]; then echo "[$id] would run: $RUNNER \"$task\""; continue; fi
  echo "[$id] $task"
  if $RUNNER "$task" > "$OUT/$id.md" 2> "$OUT/$id.err"; then
    ok=$((ok+1)); [ -s "$OUT/$id.err" ] || rm -f "$OUT/$id.err"
  else
    fail=$((fail+1)); echo "[$id] FAILED — see $OUT/$id.err"
  fi
done < "$Q"

[ "$DRY" = 1 ] && { echo "dry run: $n task(s), nothing executed."; exit 0; }
{ echo "# Batch summary — $(date)"
  echo "queue: $Q · tasks: $n · ok: $ok · failed: $fail"
  echo; echo "Review each $OUT/NNN.md, then act. Each task ran as an isolated fresh session:"
  echo "no shared history, no idle-expiry re-billing, floor paid once per task."
} > "$OUT/SUMMARY.md"
echo "done: $ok/$n ok → $OUT/SUMMARY.md"
[ "$fail" = 0 ]
