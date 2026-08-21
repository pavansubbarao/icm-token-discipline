#!/usr/bin/env bash
# make_index.sh — generate a section index for a large markdown file.
# Usage: bash scripts/make_index.sh path/to/doc.md > path/to/doc.index.md
# Readers load the index (1-2 KB), find their section, then slice just that
# line range — instead of loading the whole document.
# Read-only; portable bash 3.2+ / awk.

set -u
F="${1:-}"
[ -f "$F" ] || { echo "usage: make_index.sh <file.md>" >&2; exit 1; }

B=$(wc -c < "$F" | tr -d ' ')
L=$(wc -l < "$F" | tr -d ' ')
printf '# Index of %s\n' "$(basename "$F")"
printf 'Whole file: %s lines, %s bytes (~%s tokens). Load a SECTION via its line range, not the file.\n\n' \
  "$L" "$B" "$((B / 4))"
printf '| Section | Lines | ~Tokens |\n|---|---|---|\n'

awk -v total_lines="$L" '
  /^#{1,3} / {
    if (n > 0) { end[n] = NR - 1 }
    n++
    start[n] = NR
    title[n] = $0
    sub(/^#+[ \t]+/, "", title[n])
    gsub(/\|/, "/", title[n])
  }
  { bytes[NR] = length($0) + 1 }
  END {
    if (n == 0) { print "| (no headings found — split by content instead) | – | – |"; exit }
    end[n] = total_lines
    for (i = 1; i <= n; i++) {
      sec = 0
      for (r = start[i]; r <= end[i]; r++) sec += bytes[r]
      printf "| %s | %d–%d | ~%d |\n", title[i], start[i], end[i], int(sec / 4)
    }
  }
' "$F"

printf '\nSlice a section: Read with offset=<start line> limit=<lines>, or `sed -n "<start>,<end>p" %s`.\n' "$F"
