"""Offline, platform-independent tests of the pinned LLVM recovery path.

No test contacts GitHub or pulls the multi-gigabyte upstream LLVM distribution.
"""
from __future__ import annotations

import hashlib
import io
import os
from pathlib import Path
import tarfile
import tempfile
import unittest
import urllib.error
from unittest.mock import patch

from scripts import build_pinned as pin
from scripts import llvm_upstream_fallback as recovery


def fixture_archive(folder: Path, host: str, malicious: bool = False) -> tuple[Path, dict]:
    suffix = '.exe' if host == 'windows' else ''
    files = {
        'bin/clang' + suffix: b'certified-clang-fixture',
        'bin/lld-link' + suffix: b'certified-lld-fixture',
        'lib/clang/19/include/stddef.h': b'// resource header fixture',
        'share/clang/default.cfg': b'// config fixture',
        'bin/unneeded': b'NOT PART OF SLIM LLVM',
        'lib/unneeded.a': b'NOT PART OF SLIM LLVM',
    }
    if host == 'windows':
        files['bin/LLVM.dll'] = b'Windows DLL fixture'
    else:
        files['lib/libLLVM.so.19.1'] = b'Linux shared object fixture'
    if malicious:
        files['../../escape.txt'] = b'escape'
    archive = folder / 'official-upstream-fixture.tar.xz'
    with tarfile.open(archive, 'w:xz') as output:
        directory = tarfile.TarInfo('LLVM-19.1.7/lib/clang/19/include/cuda_wrappers')
        directory.type = tarfile.DIRTYPE
        output.addfile(directory)
        for name, body in files.items():
            member = tarfile.TarInfo('LLVM-19.1.7/' + name)
            member.size = len(body)
            member.mode = 0o755
            output.addfile(member, io.BytesIO(body))
    checksums = {
        'bin/clang' + suffix: hashlib.sha256(files['bin/clang' + suffix]).hexdigest(),
        'bin/lld-link' + suffix: hashlib.sha256(files['bin/lld-link' + suffix]).hexdigest(),
    }
    return archive, checksums


class LLVMUpstreamRecovery(unittest.TestCase):
    def test_independent_urls_are_exact_release_and_sha_pinned(self):
        for host in ('windows', 'linux'):
            url, digest = recovery.UPSTREAM_ASSETS[host]
            self.assertIn('github.com/llvm/llvm-project/releases/download/llvmorg-19.1.7/', url)
            self.assertRegex(digest, r'^[0-9a-f]{64}$')
            self.assertNotIn('eton975/Aufake3D', url)
            self.assertEqual(set(recovery.CI_COMPILER_SHA256[host]),
                             {'bin/clang' + ('.exe' if host == 'windows' else ''),
                              'bin/lld-link' + ('.exe' if host == 'windows' else '')})

    def test_selects_only_compiler_libraries_and_resources(self):
        for host in ('linux', 'windows'):
            with self.subTest(host=host), tempfile.TemporaryDirectory() as tmp:
                folder = Path(tmp)
                archive, digest = fixture_archive(folder, host)
                with patch.dict(recovery.CI_COMPILER_SHA256, {host: digest}):
                    manifest = recovery.extract_upstream_llvm(archive, folder / 'llvm', host)
                selected = set(manifest['files_sha256'])
                self.assertEqual(manifest['upstream_archive_sha256'], recovery.UPSTREAM_ASSETS[host][1])
                self.assertTrue(set(digest).issubset(selected))
                self.assertIn('lib/clang/19/include/stddef.h', selected)
                self.assertIn('LLVM_LICENSE.TXT', selected)
                self.assertNotIn('bin/unneeded', selected)
                self.assertNotIn('lib/unneeded.a', selected)
                self.assertFalse((folder / 'llvm/bin/unneeded').exists())
                if host == 'linux':
                    self.assertIn('lib/libLLVM.so.19.1', selected)
                else:
                    self.assertIn('bin/LLVM.dll', selected)

    def test_rejects_traversal_members(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            archive, digest = fixture_archive(folder, 'linux', malicious=True)
            with patch.dict(recovery.CI_COMPILER_SHA256, {'linux': digest}):
                with self.assertRaisesRegex(RuntimeError, 'Unsafe upstream LLVM'):
                    recovery.extract_upstream_llvm(archive, folder / 'llvm', 'linux')
            self.assertFalse((folder / 'escape.txt').exists())

    def test_rejects_different_compiler_with_same_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            archive, _ = fixture_archive(folder, 'linux')
            with self.assertRaisesRegex(RuntimeError, 'compiler differs from certified'):
                recovery.extract_upstream_llvm(archive, folder / 'llvm', 'linux')

    def test_network_failure_falls_back_and_cached_install_reused(self):
        host = 'windows' if os.name == 'nt' else 'linux'
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            archive, digest = fixture_archive(folder, host)
            observed = []
            def fake_download(url, expected_sha, target):
                observed.append((url, expected_sha))
                if len(observed) == 1:
                    raise urllib.error.URLError('slim toolchain release unavailable')
                return archive
            with patch.dict(recovery.CI_COMPILER_SHA256, {host: digest}), \
                 patch.object(pin, 'download_verified', side_effect=fake_download):
                result = pin.pinned_llvm(folder / 'cache', host)
                self.assertEqual(len(observed), 2)
                self.assertEqual(observed[1], recovery.UPSTREAM_ASSETS[host])
                self.assertTrue((result / ('clang.exe' if host == 'windows' else 'clang')).exists())
                # Cache must keep working after *both* download hosts vanish.
                with patch.object(pin, 'download_verified',
                                  side_effect=AssertionError('network access on cache hit')):
                    self.assertEqual(pin.pinned_llvm(folder / 'cache', host), result)

    def test_offline_miss_can_use_preverified_full_archive_cache(self):
        host = 'windows' if os.name == 'nt' else 'linux'
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            archive, digest = fixture_archive(folder, host)
            calls = []
            def fake_download(url, expected_sha, target):
                calls.append(url)
                if len(calls) == 1:
                    raise RuntimeError('Offline and pinned archive is missing or corrupt: ' + str(target))
                return archive
            with patch.dict(os.environ, {'A3D_PINNED_OFFLINE': '1'}), \
                 patch.dict(recovery.CI_COMPILER_SHA256, {host: digest}), \
                 patch.object(pin, 'download_verified', side_effect=fake_download):
                self.assertTrue(pin.pinned_llvm(folder / 'cache', host).is_dir())
                self.assertEqual(len(calls), 2)

    def test_integrity_failure_never_triggers_upstream_fallback(self):
        host = 'windows' if os.name == 'nt' else 'linux'
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(pin, 'download_verified',
                              side_effect=RuntimeError('Pinned download SHA-256 mismatch')) as mock_download:
                with self.assertRaisesRegex(RuntimeError, 'SHA-256 mismatch'):
                    pin.pinned_llvm(Path(tmp), host)
                mock_download.assert_called_once()

    def test_a_bad_official_archive_fails_closed(self):
        host = 'windows' if os.name == 'nt' else 'linux'
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(pin, 'download_verified',
                              side_effect=[urllib.error.URLError('release unavailable'),
                                           RuntimeError('Pinned download SHA-256 mismatch')]) as download:
                with self.assertRaisesRegex(RuntimeError, 'SHA-256 mismatch'):
                    pin.pinned_llvm(Path(tmp), host)
                self.assertEqual(download.call_count, 2)


if __name__ == '__main__':
    unittest.main()
