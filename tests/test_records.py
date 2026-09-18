"""Behavioral checks for the public records CLI; all fixtures are isolated."""
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(os.environ.get(
    "ICM_RECORDS_SCRIPT",
    str(Path(__file__).resolve().parents[1] / "scripts/icm_records.sh"),
)).resolve()


class RecordsCLI(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.cards = self.root / ".icm/records"
        self.cards.mkdir(parents=True)
        self.source = self.root / "worker.py"
        self.source.write_text("from config import MAX_ATTEMPTS\n"
                               "def retry_budget():\n"
                               "    return MAX_ATTEMPTS\n")
        (self.root / "config.py").write_text("MAX_ATTEMPTS = 3\n")
        self.card = self.cards / "retry-budget.md"

    def run_cli(self, *args):
        return subprocess.run(["bash", str(SCRIPT), *map(str, args)],
                              cwd=self.root, text=True, capture_output=True)

    def make_card(self, anchors="- worker.py:1-3 sha:000000000000",
                  dependencies="", body="The retry budget is 3 attempts."):
        extra = "\ndependencies:\n" + dependencies if dependencies else ""
        self.card.write_text("---\nq: what is the retry budget\nanchors:\n"
                             + anchors + extra
                             + "\nclaim_status: verified\nscope: fixture configuration\n"
                             "filed: 2026-09-18\n---\n" + body + "\n")

    def stamp(self):
        result = self.run_cli("stamp", self.card)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def actual_value(self):
        result = subprocess.run(
            [sys.executable, "-B", "-c",
             "import worker; print(worker.retry_budget())"],
            cwd=self.root, text=True, capture_output=True, check=True)
        return int(result.stdout)

    def test_legacy_anchor_remains_compatible_without_truth_endorsement(self):
        digest = hashlib.sha1(self.source.read_bytes()).hexdigest()[:12]
        self.make_card(anchors="- worker.py:1-3 sha:" + digest)
        self.assertEqual(self.run_cli("check").returncode, 0)
        result = self.run_cli("recall", "retry", "budget")
        self.assertEqual(result.returncode, 0)
        self.assertIn("UNCHANGED_EVIDENCE", result.stdout)
        self.assertNotIn("trustworthy as-is", result.stdout)

    def test_record_without_anchors_is_not_unchanged(self):
        self.make_card(anchors="")
        self.assertNotEqual(self.run_cli("check").returncode, 0)
        self.assertNotEqual(self.run_cli("recall", "retry").returncode, 0)

    def test_malformed_row_does_not_hide_beside_valid_anchor(self):
        self.make_card()
        self.stamp()
        self.card.write_text(self.card.read_text().replace(
            "claim_status:", "- this is not an anchor\nclaim_status:"))
        self.assertNotEqual(self.run_cli("check").returncode, 0)

    def test_body_cannot_supply_missing_frontmatter_anchors(self):
        self.card.write_text("---\nq: retry budget\n---\n"
                             "- worker.py:1-3 sha:"
                             + hashlib.sha1(self.source.read_bytes()).hexdigest()[:12]
                             + "\n")
        self.assertNotEqual(self.run_cli("check").returncode, 0)

    def test_hashless_anchor_can_be_stamped_but_not_checked_as_unchanged(self):
        self.make_card(anchors="- worker.py:1-3")
        self.assertNotEqual(self.run_cli("check").returncode, 0)
        self.stamp()
        self.assertEqual(self.run_cli("check").returncode, 0)

    def test_invalid_ranges_do_not_get_stamped(self):
        for span in ("0-1", "3-1", "1-99", "8-9", "one-three"):
            with self.subTest(span=span):
                self.make_card(anchors="- worker.py:" + span + " sha:000000000000")
                original = self.card.read_bytes()
                self.assertNotEqual(self.run_cli("stamp", self.card).returncode, 0)
                self.assertEqual(self.card.read_bytes(), original)

    def test_failed_stamp_is_atomic(self):
        self.make_card(anchors="- worker.py:1-3 sha:000000000000\n"
                               "- absent.py:1-2 sha:000000000000")
        original = self.card.read_bytes()
        self.assertNotEqual(self.run_cli("stamp", self.card).returncode, 0)
        self.assertEqual(self.card.read_bytes(), original)

    def test_dependency_drift_is_detected_when_declared(self):
        self.make_card(dependencies="- config.py:* sha:000000000000")
        self.stamp()
        self.assertEqual(self.actual_value(), 3)
        self.assertEqual(self.run_cli("check").returncode, 0)
        (self.root / "config.py").write_text("MAX_ATTEMPTS = 5\n")
        self.assertEqual(self.actual_value(), 5)
        result = self.run_cli("check")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("config.py", result.stdout)
        self.assertEqual(self.run_cli("recall", "retry").returncode, 1)

    def test_undeclared_dependency_remains_a_stated_limit(self):
        self.make_card()
        self.stamp()
        (self.root / "config.py").write_text("MAX_ATTEMPTS = 5\n")
        self.assertEqual(self.actual_value(), 5)
        result = self.run_cli("recall", "retry")
        self.assertEqual(result.returncode, 0)
        self.assertIn("UNCHANGED_EVIDENCE", result.stdout)
        self.assertIn("claim validity", result.stdout)
        self.assertNotIn("trustworthy as-is", result.stdout)

    def test_changed_cited_source_is_detected(self):
        self.make_card()
        self.stamp()
        self.source.write_text(self.source.read_text().replace(
            "return MAX_ATTEMPTS", "return MAX_ATTEMPTS + 1"))
        self.assertEqual(self.actual_value(), 4)
        self.assertEqual(self.run_cli("check").returncode, 1)

    def test_deleted_evidence_is_detected(self):
        self.make_card()
        self.stamp()
        self.source.unlink()
        self.assertEqual(self.run_cli("check").returncode, 1)

    def test_paths_with_spaces_and_literal_query(self):
        (self.root / "config with spaces.py").write_text("VALUE = 3\n")
        self.make_card(anchors="- config with spaces.py:1-1 sha:000000000000",
                       body="Literal lookup [retry] budget.")
        self.stamp()
        result = self.run_cli("recall", "[retry]")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("UNCHANGED_EVIDENCE", result.stdout)

    def test_empty_directory_is_not_a_successful_check(self):
        self.assertNotEqual(self.run_cli("check").returncode, 0)

    def test_read_commands_preserve_records_and_source(self):
        self.make_card()
        self.card.chmod(0o640)
        self.stamp()
        self.assertEqual(self.card.stat().st_mode & 0o777, 0o640)
        before = {p: p.read_bytes() for p in (self.card, self.source)}
        self.assertEqual(self.run_cli("check").returncode, 0)
        self.assertEqual(self.run_cli("recall", "retry").returncode, 0)
        self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_body_change_does_not_masquerade_as_claim_verification(self):
        self.make_card()
        self.stamp()
        self.card.write_text(self.card.read_text().replace(
            "3 attempts", "900 attempts"))
        result = self.run_cli("recall", "retry")
        self.assertEqual(result.returncode, 0)
        self.assertIn("claim validity", result.stdout)
        self.assertNotIn("trustworthy as-is", result.stdout)

    def test_unclosed_frontmatter_and_duplicate_sections_are_invalid(self):
        self.make_card()
        self.stamp()
        original = self.card.read_text()
        self.card.write_text(original.replace("\n---\nThe", "\nThe"))
        self.assertNotEqual(self.run_cli("check").returncode, 0)
        self.card.write_text(original.replace("claim_status:", "anchors: []\nclaim_status:"))
        self.assertNotEqual(self.run_cli("check").returncode, 0)

    def test_legacy_partial_range_preserves_crlf_and_no_final_newline(self):
        self.source.write_bytes(b"ignore\r\nVALUE = 3\r\nlast")
        digest = hashlib.sha1(b"VALUE = 3\r\nlast").hexdigest()[:12]
        self.make_card(anchors="- worker.py:2-3 sha:" + digest)
        self.assertEqual(self.run_cli("check").returncode, 0)

    def test_stamp_preserves_non_evidence_text_and_line_endings(self):
        self.make_card()
        raw = self.card.read_bytes().replace(b"\n", b"\r\n").rstrip(b"\r\n")
        self.card.write_bytes(raw)
        self.stamp()
        digest = hashlib.sha1(self.source.read_bytes()).hexdigest()[:12].encode()
        self.assertEqual(self.card.read_bytes(), raw.replace(b"000000000000", digest))

    def test_mixed_recall_returns_worst_status(self):
        self.make_card()
        self.stamp()
        other = self.cards / "invalid.md"
        other.write_text("---\nq: retry budget\nanchors: []\n---\nUnknown.\n")
        result = self.run_cli("recall", "retry", "budget")
        self.assertEqual(result.returncode, 2)
        self.assertIn("UNCHANGED_EVIDENCE", result.stdout)
        self.assertIn("INVALID_RECORD", result.stdout)


if __name__ == "__main__":
    unittest.main()
