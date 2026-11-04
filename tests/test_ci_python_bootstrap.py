"""Prevent missing runner Python releases from bypassing the reproducibility gate."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/source-ci.yml'
SCRIPT = ROOT / 'scripts/ci_install_pinned_python.sh'
UV_ACTION = 'astral-sh/setup-uv@c771a70e6277c0a99b617c7a806ffedaca235ff9'


class PinnedPythonBootstrap(unittest.TestCase):
    def test_setup_python_is_windows_only(self):
        workflow = WORKFLOW.read_text()
        self.assertEqual(workflow.count('uses: actions/setup-python@v7'), 1)
        self.assertIn("- uses: actions/setup-python@v7\n        if: runner.os == 'Windows'", workflow)
        self.assertEqual(workflow.count("python-version: '3.13.7'"), 1)

    def test_all_four_target_jobs_use_exact_managed_python(self):
        workflow = WORKFLOW.read_text()
        self.assertEqual(workflow.count('uses: '+UV_ACTION), 3)
        self.assertEqual(workflow.count("version: '0.10.0'"), 3)
        self.assertEqual(workflow.count('run: bash scripts/ci_install_pinned_python.sh'), 3)
        self.assertEqual(workflow.count('Verify the active Python is exactly 3.13.7'), 3)
        self.assertIn('ubuntu-26.04', workflow)
        self.assertIn('ubuntu:26.10@sha256:', workflow)
        self.assertIn('needs: [windows-and-linux, ubuntu-2610-container]', workflow)
        self.assertIn('--linux-target ubuntu-26.10=verification/ubuntu-26.10', workflow)

    def test_bootstrap_fails_closed_without_pin(self):
        content = SCRIPT.read_text()
        self.assertIn("readonly VERSION='3.13.7'", content)
        self.assertIn('uv python install "${VERSION}" --managed-python --no-bin', content)
        self.assertIn('uv python find --managed-python "${VERSION}"', content)
        self.assertIn('UV_PYTHON_INSTALL_DIR="${RUNNER_TEMP}/aufake3d-managed-python"', content)
        self.assertIn('sys.version_info[:3] == (3, 13, 7)', content)
        self.assertIn('>> "${GITHUB_PATH}"', content)
        self.assertNotIn('|| true', content)

    @unittest.skipUnless(shutil.which('bash') and os.name != 'nt', 'Bash bootstrap smoke test on Linux')
    def test_bash_bootstrap_rejects_wrong_python(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root/'bin'
            bin_dir.mkdir()
            uv = bin_dir/'uv'
            uv.write_text('#!/bin/sh\n'
                          'if [ "$1" = python ] && [ "$2" = install ]; then exit 0; fi\n'
                          'if [ "$1" = python ] && [ "$2" = find ]; then echo "$CI_FAKE_PYTHON"; exit 0; fi\n'
                          'exit 2\n')
            uv.chmod(0o755)
            fake = root/'wrong-python'
            fake.write_text('#!/bin/sh\nexit 7\n')
            fake.chmod(0o755)
            gpath = root/'github_path'
            env = dict(os.environ, PATH=str(bin_dir)+os.pathsep+os.environ['PATH'],
                       RUNNER_TEMP=str(root/'temp'), GITHUB_PATH=str(gpath),
                       CI_FAKE_PYTHON=str(fake))
            proc = subprocess.run(['bash', str(SCRIPT)], env=env, capture_output=True, text=True)
            self.assertNotEqual(proc.returncode, 0)
            self.assertFalse(gpath.exists())


    @unittest.skipUnless(shutil.which('bash') and os.name != 'nt', 'Bash bootstrap smoke test on Linux')
    def test_bash_bootstrap_creates_pinned_python_shims(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bindir = root/'bin'
            bindir.mkdir()
            fake = root/'pinned-cpython-3.13.7'
            fake.write_text('#!/bin/sh\nexit 0\n')
            fake.chmod(0o755)
            uv = bindir/'uv'
            uv.write_text('#!/bin/sh\n'
                          'if [ "$1" = python ] && [ "$2" = install ]; then exit 0; fi\n'
                          'if [ "$1" = python ] && [ "$2" = find ]; then echo "$CI_FAKE_PYTHON"; exit 0; fi\n'
                          'exit 2\n')
            uv.chmod(0o755)
            gpath = root/'github_path'
            env = dict(os.environ, PATH=str(bindir)+os.pathsep+os.environ['PATH'],
                       RUNNER_TEMP=str(root/'temp'), GITHUB_PATH=str(gpath),
                       CI_FAKE_PYTHON=str(fake))
            proc = subprocess.run(['bash', str(SCRIPT)], env=env, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            shim = root/'temp'/'aufake3d-python-shims'
            self.assertEqual(gpath.read_text().strip(), str(shim))
            self.assertEqual((shim/'python').resolve(), fake)
            self.assertEqual((shim/'python3').resolve(), fake)


if __name__ == '__main__':
    unittest.main()
