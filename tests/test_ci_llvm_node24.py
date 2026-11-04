"""Prevent reintroduction of the deprecated Node 20 LLVM installer in CI."""
from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import ci_install_pinned_llvm as installer


class Node24LLVMWorkflow(unittest.TestCase):
    def test_workflow_no_longer_invokes_deprecated_action(self):
        workflow = (ROOT/'.github/workflows/source-ci.yml').read_text(encoding='utf-8')
        self.assertNotIn('KyleMayes/install-llvm-action', workflow)
        self.assertEqual(workflow.count('run: python scripts/ci_install_pinned_llvm.py'), 2)
        self.assertIn('ubuntu-24.04, ubuntu-26.04, windows-2022', workflow)
        self.assertIn('ubuntu-2610-container:', workflow)
        # This fix must not weaken or remove the cross-platform certificate.
        self.assertIn('cross-platform-byte-identity:', workflow)
        self.assertIn('debian-13-container:', workflow)
        self.assertIn('needs: [windows-and-linux, ubuntu-2610-container, debian-13-container]', workflow)

    def test_pinned_download_and_exports_use_temporary_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            host = 'windows' if os.name == 'nt' else 'linux'
            fake_bin = root/'aufake3d-pinned-ci-llvm'/'llvm-19.1.7'/host/'bin'
            fake_bin.mkdir(parents=True)
            suffix = '.exe' if os.name == 'nt' else ''
            for name in ('clang', 'lld-link'):
                (fake_bin/(name + suffix)).write_bytes(b'not an actual compiler')
            exports = {'RUNNER_TEMP': tmp,
                       'GITHUB_PATH': str(root/'path.txt'),
                       'GITHUB_ENV': str(root/'env.txt')}
            with patch.object(installer, 'pinned_llvm', return_value=fake_bin), \
                 patch.object(installer.platform, 'machine', return_value='x86_64'):
                got = installer.provision(exports)
            self.assertEqual(got, fake_bin)
            self.assertEqual((root/'path.txt').read_text().strip(), str(fake_bin))
            output = (root/'env.txt').read_text()
            self.assertIn('LLVM_PATH=' + str(fake_bin.parent), output)
            if os.name != 'nt':
                self.assertIn('LD_LIBRARY_PATH=' + str(fake_bin.parent/'lib'), output)
            self.assertEqual(exports['A3D_PINNED_CACHE'], str(root/'aufake3d-pinned-ci-llvm'))

    def test_missing_actions_environment_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError, 'RUNNER_TEMP'):
            installer.provision({})


if __name__ == '__main__':
    unittest.main()
