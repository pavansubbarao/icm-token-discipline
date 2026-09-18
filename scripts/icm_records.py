#!/usr/bin/env python3
"""Check explicitly declared evidence, without endorsing a card's conclusions.

Standard library only. The evidence lists use a constrained frontmatter format,
not general YAML. See references/memory.md for the format and exit codes.
"""
import hashlib
import os
from pathlib import Path
import re
import stat
import sys
import tempfile


NOTICE = ("Evidence hashes do not verify claim validity, scope, record prose, "
          "or undeclared dependencies; review those before reuse.")
USAGE = "usage: icm_records.sh {recall <words...> | stamp <card> | check [dir]}"
ROW = re.compile(r"^(\s*-\s+)(.+):(\*|[0-9]+-[0-9]+)(?:\s+sha:([0-9a-fA-F]{12}))?\s*$")
KEY = re.compile(r"^([A-Za-z_][\w-]*):\s*(.*)$")


class InvalidRecord(ValueError):
    pass


class MissingEvidence(ValueError):
    pass


def parse_card(raw):
    try:
        lines = raw.decode("utf-8").splitlines(keepends=True)
    except UnicodeDecodeError as exc:
        raise InvalidRecord("record must be UTF-8") from exc
    if not lines or lines[0].strip() != "---":
        raise InvalidRecord("missing opening frontmatter delimiter")
    rows, seen, section, closed = [], set(), None, False
    for index, line in enumerate(lines[1:], 1):
        content = line.rstrip("\r\n")
        if content == "---":
            closed = True
            break
        if not content.strip() or content.lstrip().startswith("#"):
            continue
        key = KEY.fullmatch(content)
        if key:
            name, value = key.groups()
            section = name if name in ("anchors", "dependencies") else None
            if section:
                if name in seen:
                    raise InvalidRecord("duplicate " + name + " section")
                seen.add(name)
                if value not in ("", "[]"):
                    raise InvalidRecord(name + " must be a block list")
            continue
        if section:
            match = ROW.fullmatch(content)
            if not match:
                raise InvalidRecord("malformed %s row at line %s" % (section, index + 1))
            prefix, path, span, digest = match.groups()
            if not path.strip() or path != path.strip():
                raise InvalidRecord("invalid evidence path at line %s" % (index + 1))
            if span != "*":
                start, end = map(int, span.split("-"))
                if start < 1 or end < start:
                    raise InvalidRecord("invalid range: " + path + ":" + span)
            rows.append((index, prefix, path, span, digest, section))
    if not closed:
        raise InvalidRecord("missing closing frontmatter delimiter")
    if not any(row[5] == "anchors" for row in rows):
        raise InvalidRecord("at least one valid frontmatter anchor is required")
    return lines, rows


def evidence_hash(path, span):
    source = Path(path)
    if not source.is_file():
        raise MissingEvidence("missing evidence: " + path)
    data = source.read_bytes()
    if span != "*":
        start, end = map(int, span.split("-"))
        # Match legacy sed line ranges: split on LF, retain the original bytes.
        lines = data.split(b"\n")
        if lines[-1] == b"":
            lines.pop()
        if end > len(lines):
            raise InvalidRecord("range exceeds file: " + path + ":" + span)
        payload = b"\n".join(lines[start - 1:end])
        if end < len(lines) or data.endswith(b"\n"):
            payload += b"\n"
    else:
        payload = data
    return hashlib.sha1(payload).hexdigest()[:12]


def check_card(raw):
    try:
        _, rows = parse_card(raw)
        if any(row[4] is None for row in rows):
            raise InvalidRecord("unstamped evidence row; verify the claim before stamping")
    except InvalidRecord as exc:
        return 2, [str(exc)]
    status, details = 0, []
    for _, _, path, span, want, section in rows:
        label = "%s %s:%s" % (section, path, span)
        try:
            have = evidence_hash(path, span)
        except MissingEvidence as exc:
            status = max(status, 1)
            details.append(str(exc))
        except (InvalidRecord, OSError) as exc:
            status = 2
            details.append(str(exc))
        else:
            if have != want.lower():
                status = max(status, 1)
                details.append("changed: " + label)
    return status, details


def report(card, raw):
    status, details = check_card(raw)
    print(("UNCHANGED_EVIDENCE", "STALE_EVIDENCE", "INVALID_RECORD")[status], card)
    for detail in details:
        print("  " + detail)
    return status


def stamp(card):
    if card.is_symlink():
        raise InvalidRecord("stamp requires a regular card, not a symbolic link")
    original = card.read_bytes()
    mode = stat.S_IMODE(card.stat().st_mode)
    lines, rows = parse_card(original)
    # Validate and hash every row before touching the card.
    for index, prefix, path, span, _, _ in rows:
        digest = evidence_hash(path, span)
        old = lines[index]
        ending = "\r\n" if old.endswith("\r\n") else "\n" if old.endswith("\n") else ""
        lines[index] = "%s%s:%s sha:%s%s" % (prefix, path, span, digest, ending)
    updated = "".join(lines).encode("utf-8")
    temp = None
    try:
        with tempfile.NamedTemporaryFile(dir=card.parent, prefix=".icm-stamp-", delete=False) as output:
            temp = Path(output.name)
            output.write(updated)
            output.flush()
            os.fsync(output.fileno())
        temp.chmod(mode)
        if card.read_bytes() != original:
            raise InvalidRecord("card changed during stamp; retry after reviewing it")
        os.replace(temp, card)
    finally:
        if temp is not None and temp.exists():
            temp.unlink()
    print("stamped evidence hashes:", card)
    print(NOTICE)
    return 0


def main(args):
    if not args:
        print(USAGE, file=sys.stderr)
        return 2
    command, rest = args[0], args[1:]
    if command == "stamp" and len(rest) == 1:
        return stamp(Path(rest[0]))
    if not ((command == "check" and len(rest) <= 1) or (command == "recall" and rest)):
        print(USAGE, file=sys.stderr)
        return 2
    directory = Path(rest[0]) if command == "check" and rest else Path(".icm/records")
    cards = sorted(directory.glob("*.md")) if directory.is_dir() else []
    if not cards:
        print("no records:", directory)
        return 1
    print(NOTICE)
    if command == "check":
        return max(report(card, card.read_bytes()) for card in cards)
    words = {word.casefold() for arg in rest for word in arg.split() if len(word) >= 3}
    hits = []
    for card in cards:
        raw = card.read_bytes()
        searchable = raw.decode("utf-8", errors="replace").casefold()
        score = sum(word in searchable for word in words)
        if score:
            hits.append((score, card, raw))
    if not hits:
        print("no matching record; continue scoped analysis")
        return 1
    status = 0
    for score, card, raw in sorted(hits, key=lambda hit: (-hit[0], str(hit[1])))[:3]:
        print("--- %s (score %s) ---" % (card, score))
        status = max(status, report(card, raw))
        print(raw.decode("utf-8", errors="replace"), end="\n")
    return status


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except MissingEvidence as exc:
        print("STALE_EVIDENCE:", exc, file=sys.stderr)
        sys.exit(1)
    except (InvalidRecord, OSError) as exc:
        print("INVALID_RECORD:", exc, file=sys.stderr)
        sys.exit(2)
