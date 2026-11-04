"""No-network regression checks for the optional full-CI-reference local builder.

A successful CI checksum, not a matching compiler version string, is the gate.
The original build recipe stays unchanged; neither test downloads LLVM.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from scripts import build_pinned as pin


class PinnedBuild(unittest.TestCase):
    def test_fixed_input_hashes_are_valid_and_distinct(self):
        for host in ('linux', 'windows'):
            for kind in ('llvm', 'uv'):
                url, digest = pin.ASSETS[host][kind]
                self.assertTrue(url.startswith('https://github.com/'))
                self.assertRegex(digest, r'^[0-9a-f]{64}$')
        self.assertNotEqual(pin.ASSETS['linux']['llvm'][1], pin.ASSETS['windows']['llvm'][1])
        self.assertEqual(pin.REFERENCE_ZIP_SHA256,
                         'a64f99e63e235e310c4d8dd45dff05f7b77271d744c9d060a9ca84a9b28f3848')

    def test_download_requires_archive_sha_and_does_not_publish_bad_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'fixture.tar'
            source.write_bytes(b'pinned-test-asset')
            target = root / 'cache' / 'fixture.tar'
            with patch.dict(os.environ, {'A3D_PINNED_OFFLINE': '0'}):
                with self.assertRaisesRegex(RuntimeError, 'SHA-256 mismatch'):
                    pin.download_verified(source.as_uri(), '0' * 64, target)
                self.assertFalse(target.exists())
                expected = hashlib.sha256(source.read_bytes()).hexdigest()
                self.assertEqual(pin.download_verified(source.as_uri(), expected, target), target)
                self.assertEqual(target.read_bytes(), source.read_bytes())
            # An offline cached hit does not access the network.
            with patch.dict(os.environ, {'A3D_PINNED_OFFLINE': '1'}):
                self.assertEqual(pin.download_verified('https://invalid.example/file', expected, target), target)

    def test_reference_lists_all_twenty_real_ci_pe_outputs(self):
        ref = pin.load_reference(pin.DEFAULT_REFERENCE)
        self.assertEqual(ref['runtime_zip_sha256'], pin.REFERENCE_ZIP_SHA256)
        self.assertEqual(len(ref['generated_pe_sha256']),20)
        self.assertIn('dist/miles-local/mss32.dll',ref['generated_pe_sha256'])

    def test_upstream_uv_version_metadata_is_accepted_but_not_a_different_release(self):
        self.assertTrue(pin.uv_version_matches('uv 0.10.0 (0ba432459 2026-02-05)\\n'))
        self.assertTrue(pin.uv_version_matches('uv 0.10.0'))
        for output in ('uv 0.10.1', 'uv 0.10.0.1', 'uv 0.10.0-malicious',
                       'uv 0.10.0\\nuv 0.10.1', 'uv 0.9.99'):
            with self.subTest(output=output):
                self.assertFalse(pin.uv_version_matches(output))

    def test_direct_pinned_script_can_import_project_verifier(self):
        # Running a file under scripts/ instead of -m may hide ROOT on sys.path.
        command = [sys.executable, str(pin.ROOT/'scripts/build_pinned.py'), '--doctor']
        result = subprocess.run(command, cwd=pin.ROOT.parent,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_cached_tool_directory_must_be_outside_repo(self):
        with self.assertRaisesRegex(RuntimeError, 'outside'):
            pin.cache_root({'A3D_PINNED_CACHE': str(pin.ROOT / 'llvm')})
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(pin.cache_root({'A3D_PINNED_CACHE': tmp}), Path(tmp).resolve())

    def test_child_processes_inherit_pinned_tools_and_deterministic_env(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp)
            env = pin.build_env(cache, cache / 'python3', cache / 'llvm' / 'bin')
            self.assertEqual(env['PYTHONHASHSEED'], '0')
            self.assertEqual(env['SOURCE_DATE_EPOCH'], '1767225600')
            self.assertEqual(env['PATH'].split(os.pathsep)[0], str(cache / 'llvm' / 'bin'))

    def test_pinned_release_refuses_unverified_build_shortcuts(self):
        with tempfile.TemporaryDirectory() as tmp:
            for option in ('--skip-repro-check', '--no-package', '--no-tests'):
                with self.subTest(option=option), self.assertRaisesRegex(RuntimeError, 'cannot skip'):
                    pin.run_build(Path(tmp), [option], pin.load_reference(pin.DEFAULT_REFERENCE))

    def test_reference_hash_mismatch_is_a_hard_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp)
            with patch.object(pin, 'pinned_uv', return_value=cache/'uv'), \
                 patch.object(pin, 'pinned_python', return_value=Path(sys.executable)), \
                 patch.object(pin, 'pinned_llvm', return_value=cache/'llvm'), \
                 patch.object(pin, 'assert_versions'), \
                 patch.object(pin, 'sha_file', return_value='b'*64), \
                 patch.object(pin.subprocess, 'run') as run:
                with self.assertRaisesRegex(RuntimeError, 'differs from certified CI'):
                    pin.run_build(cache, ['--no-acoustics'], {'runtime_zip_sha256':'a'*64})
                self.assertEqual(run.call_count, 3 if os.name != 'nt' else 2)  # optional Linux ELF probe
                self.assertTrue(any('verify_reproducible.py' in str(c) for c in run.call_args_list))

    def test_reference_hash_match_requires_mandatory_check_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp)
            with patch.object(pin, 'pinned_uv', return_value=cache/'uv'), \
                 patch.object(pin, 'pinned_python', return_value=Path(sys.executable)), \
                 patch.object(pin, 'pinned_llvm', return_value=cache/'llvm'), \
                 patch.object(pin, 'assert_versions'), \
                 patch.object(pin, 'sha_file', return_value='a'*64), \
                 patch.object(pin, 'check_compiled_pe_bytes'), \
                 patch.object(pin.subprocess, 'run') as run:
                self.assertEqual(pin.run_build(cache, [], {'runtime_zip_sha256':'a'*64, 'generated_pe_sha256':{}}), 0)
                self.assertEqual(run.call_count, 3 if os.name != 'nt' else 2)
                build_args = run.call_args_list[-2].args[0]
                proof_args = run.call_args_list[-1].args[0]
                self.assertIn('scripts/build.py', Path(build_args[1]).as_posix())
                self.assertIn('--check-report', proof_args)
                self.assertEqual(run.call_args_list[-2].kwargs['env']['PYTHONHASHSEED'], '0')

    def test_automatic_entrypoints_use_pinned_builder(self):
        root = pin.ROOT
        self.assertIn('scripts/build_pinned.py', (root / 'BUILD_LINUX.sh').read_text())
        self.assertIn('scripts\\build_pinned.py', (root / 'BUILD_WINDOWS.cmd').read_text())
        if os.name != 'nt':
            self.assertEqual(subprocess.run(['bash', '-n', str(root/'scripts/local_prepare_llvm_compat.sh')],
                                           capture_output=True).returncode, 0)

    def test_doctor_does_not_trigger_downloads(self):
        with patch.object(pin, 'download_verified', side_effect=AssertionError('network called')):
            self.assertEqual(pin.main(['--doctor']), 0)
        with tempfile.TemporaryDirectory() as tmp:
            bad=Path(tmp)/'bad.json'; bad.write_text('{}')
            self.assertEqual(pin.main(['--reference-file', str(bad), '--doctor']), 1)


if __name__ == '__main__':
    unittest.main()
