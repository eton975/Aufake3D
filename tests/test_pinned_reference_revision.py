"""Frozen CI reference is checked only for the exact clean source revision."""
from __future__ import annotations
import subprocess
import unittest
from unittest.mock import patch
from scripts import build_pinned as pinned

REFERENCE = {'source_commit': 'e390fdb3063d01ae56e09d84c5930124c324e4af'}


class RevisionAwareReference(unittest.TestCase):
    def git_results(self, head: str, status: str):
        return [subprocess.CompletedProcess(['git'], 0, head + '\n', ''),
                subprocess.CompletedProcess(['git'], 0, status, '')]

    def test_exact_clean_reference_is_still_strictly_checked(self):
        with patch.object(pinned.subprocess, 'run', side_effect=self.git_results(
                REFERENCE['source_commit'], '')):
            self.assertTrue(pinned.reference_checkout_is_exact(REFERENCE))

    def test_newer_commit_is_not_compared_with_older_zip(self):
        with patch.object(pinned.subprocess, 'run', side_effect=self.git_results(
                '09fe6424728374bacf2f612c245f132bf2aeac7e', '')):
            self.assertFalse(pinned.reference_checkout_is_exact(REFERENCE))

    def test_dirty_reference_commit_is_not_certified_as_exact(self):
        with patch.object(pinned.subprocess, 'run', side_effect=self.git_results(
                REFERENCE['source_commit'], ' M README.md\n')):
            self.assertFalse(pinned.reference_checkout_is_exact(REFERENCE))

    def test_missing_git_is_not_mistaken_for_reference_checkout(self):
        with patch.object(pinned.subprocess, 'run', side_effect=FileNotFoundError('git')):
            self.assertFalse(pinned.reference_checkout_is_exact(REFERENCE))

    def test_malformed_reference_commit_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError, 'Invalid historical CI reference'):
            pinned.reference_checkout_is_exact({'source_commit': 'unverified'})

    def test_historical_gate_runs_after_local_verification(self):
        from pathlib import Path
        script = Path(pinned.__file__).read_text(encoding='utf-8')
        self.assertLess(script.index("'--check-report'"),
                        script.index('if not reference_checkout_is_exact(reference):'))
        self.assertLess(script.index('if not reference_checkout_is_exact(reference):'),
                        script.index("expected_sha256 = reference['runtime_zip_sha256']", script.index('def run_build(')))
        self.assertIn('check_compiled_pe_bytes(reference)', script)
        self.assertIn('CROSS-PLATFORM CERTIFICATION: PENDING', script)


if __name__ == '__main__':
    unittest.main()
