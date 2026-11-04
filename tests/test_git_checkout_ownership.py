"""Verify CI checkout ownership safety without disabling clean-tree checks."""
from pathlib import Path
import subprocess
import tempfile
import unittest

from scripts import verify_cross_platform as verifier


class GitCheckoutOwnership(unittest.TestCase):
    def test_scoped_git_trust_and_clean_repository_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            def git(*args):
                return subprocess.run(['git', *args], cwd=root, check=True,
                                      capture_output=True, text=True).stdout.strip()
            git('init', '-q')
            git('config', 'user.email', 'ci@example.invalid')
            git('config', 'user.name', 'Aufake3D CI Test')
            (root/'source.txt').write_text('deterministic\n')
            git('add', 'source.txt')
            git('commit', '-qm', 'test')
            self.assertEqual(verifier.clean_checkout_commit(root), git('rev-parse', 'HEAD'))
            self.assertEqual(set(verifier.tracked_source_hashes(root)), {'source.txt'})
            command = verifier.checked_out_git(root, 'rev-parse', 'HEAD')
            self.assertEqual(command[:3], ['git', '-c', f'safe.directory={root.resolve().as_posix()}'])
            self.assertEqual(command[3:], ['rev-parse', 'HEAD'])
            (root/'source.txt').write_text('changed\n')
            with self.assertRaisesRegex(ValueError, 'dirty checkout'):
                verifier.clean_checkout_commit(root)

    def test_git_trust_is_per_command_only(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            command = verifier.checked_out_git(root, 'status', '--porcelain')
            self.assertNotIn('--global', command)
            self.assertEqual(command[-2:], ['status', '--porcelain'])


if __name__ == '__main__':
    unittest.main()
