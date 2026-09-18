#!/usr/bin/env python3
"""Replay a changed imported setting while the cited function is unchanged.

Run from any directory. Requires git with the baseline commit locally available,
Bash, and Python 3.8+. Writes only an isolated temporary workspace; prints JSON.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
BASELINE = "675d725b8cf94e8402933c2f8628203ef55fc508"


def main():
    original = subprocess.run(
        ["git", "show", BASELINE + ":scripts/icm_records.sh"], cwd=ROOT,
        check=True, capture_output=True).stdout
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        old = root / "old-records.sh"
        old.write_bytes(original)
        (root / "worker.py").write_text(
            "from config import MAX_ATTEMPTS\ndef retry_budget():\n    return MAX_ATTEMPTS\n")
        config = root / "config.py"
        config.write_text("MAX_ATTEMPTS = 3\n")
        card = root / ".icm/records/retry.md"
        card.parent.mkdir(parents=True)
        card.write_text("---\nq: retry budget\nanchors:\n"
                        "- worker.py:1-3 sha:000000000000\n---\n"
                        "The local retry budget is 3.\n")

        def cli(script, *args):
            p = subprocess.run(["bash", str(script), *map(str, args)],
                               cwd=root, capture_output=True, text=True)
            return {"exit": p.returncode, "stdout": p.stdout, "stderr": p.stderr}

        def actual():
            return int(subprocess.run(
                [sys.executable, "-B", "-c", "import worker; print(worker.retry_budget())"],
                cwd=root, capture_output=True, text=True, check=True).stdout)

        new = ROOT / "scripts/icm_records.sh"
        assert cli(old, "stamp", card)["exit"] == 0
        before = actual()
        config.write_text("MAX_ATTEMPTS = 5\n")
        after = actual()
        old_hit = cli(old, "recall", "retry", "budget")
        new_undeclared = cli(new, "recall", "retry", "budget")
        config.write_text("MAX_ATTEMPTS = 3\n")
        card.write_text(card.read_text().replace("\n---\nThe", "\ndependencies:\n"
                        "- config.py:* sha:000000000000\n---\nThe"))
        assert cli(new, "stamp", card)["exit"] == 0
        config.write_text("MAX_ATTEMPTS = 5\n")
        new_declared = cli(new, "recall", "retry", "budget")
        assert (before, after) == (3, 5)
        assert "trustworthy as-is" in old_hit["stdout"]
        assert new_undeclared["exit"] == 0
        assert "UNCHANGED_EVIDENCE" in new_undeclared["stdout"]
        assert "claim validity" in new_undeclared["stdout"]
        assert new_declared["exit"] == 1 and "config.py" in new_declared["stdout"]
        result = {
            "baseline_commit": BASELINE,
            "baseline_script_sha256": hashlib.sha256(original).hexdigest(),
            "actual_budget_before": before, "actual_budget_after": after,
            "old_undeclared_dependency": old_hit,
            "new_undeclared_dependency": new_undeclared,
            "new_declared_dependency": new_declared,
            "limit": "Declared byte drift only; omitted dependencies and semantic validity require review."
        }
        # Replace ephemeral absolute paths with a stable fixture label.
        print(json.dumps(result, indent=2).replace(str(root), "<fixture>"))


if __name__ == "__main__":
    main()
