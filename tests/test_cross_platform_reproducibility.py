"""Fail-closed tests for cross-host evidence and exact release bytes."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('verify_cross_platform', ROOT/'scripts/verify_cross_platform.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class CrossPlatformReproducibilityTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        root = Path(self.directory.name)
        self.a = root/'windows.zip'
        self.b = root/'linux.zip'
        self.make_zip(self.a)
        self.b.write_bytes(self.a.read_bytes())
        self.wp = root/'win-pe.zip'
        self.lp = root/'lin-pe.zip'
        self.make_pe_zip(self.wp)
        self.lp.write_bytes(self.wp.read_bytes())
        self.win = self.manifest('windows', self.a, self.wp)
        self.linux = self.manifest('linux', self.b, self.lp)

    @staticmethod
    def make_zip(path, entry=b'same', *, creator=3):
        with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_STORED) as z:
            info = zipfile.ZipInfo('test/a3d.dll', (2026, 1, 1, 0, 0, 0))
            info.create_system = creator
            info.compress_type = zipfile.ZIP_STORED
            z.writestr(info, entry)

    @staticmethod
    def make_pe_zip(path, entry=b'MZfake-PE-fixture'):
        with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_STORED) as z:
            info = zipfile.ZipInfo('dist/core/a3d.dll', (2026, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.compress_type = zipfile.ZIP_STORED
            z.writestr(info, entry)

    @staticmethod
    def manifest(host, archive, pe_archive):
        return {
            'schema': mod.SCHEMA, 'host': host, 'source_commit': '0123456789abcdef',
            'llvm_versions': {'clang': '19.1.7', 'lld-link': '19.1.7'},
            'python_version': '3.13.7',
            'local_verification': 'three-way-bit-identical',
            'runtime_zip_name': archive.name,
            'runtime_zip_sha256': mod.digest(archive),
            'runtime_entries_sha256': mod.archive_entries(archive),
            'generated_pe_sha256': mod.archive_entries(pe_archive),
            'generated_pe_bundle_name': pe_archive.name,
            'generated_pe_bundle_sha256': mod.digest(pe_archive),
            'tracked_source_sha256': {'scripts/build.py': 'b' * 64}
        }

    def assert_failed(self, needle):
        _, errors = mod.compare_builds(self.win, self.linux, self.a, self.b,
                                       self.wp, self.lp)
        self.assertTrue(any(needle in x for x in errors), errors)

    def test_two_equivalent_builds_get_certificate(self):
        # Artifact downloads are in distinct directories but share a basename.
        aa = self.a.parent/'win'/'runtime.zip'
        bb = self.a.parent/'linux'/'runtime.zip'
        aa.parent.mkdir()
        bb.parent.mkdir()
        aa.write_bytes(self.a.read_bytes())
        bb.write_bytes(self.b.read_bytes())
        self.win['runtime_zip_name'] = self.linux['runtime_zip_name'] = 'runtime.zip'
        self.a, self.b = aa, bb
        self.win['generated_pe_bundle_name'] = self.linux['generated_pe_bundle_name'] = 'pe.zip'
        self.wp = self.wp.parent/'win'/'pe.zip'
        self.lp = self.lp.parent/'linux'/'pe.zip'
        self.wp.write_bytes((self.wp.parent.parent/'win-pe.zip').read_bytes())
        self.lp.write_bytes((self.lp.parent.parent/'lin-pe.zip').read_bytes())
        certificate, errors = mod.compare_builds(self.win, self.linux, self.a, self.b,
                                                 self.wp, self.lp,
                                                 expected_commit='0123456789abcdef')
        self.assertFalse(errors, errors)
        self.assertEqual(certificate['verification'], 'windows-linux-byte-identical')

    def test_different_pe_is_rejected(self):
        self.linux['generated_pe_sha256']['dist/core/a3d.dll'] = 'f' * 64
        self.assert_failed('generated_pe_sha256')

    def test_tampered_raw_pe_bundle_is_rejected(self):
        self.make_pe_zip(self.lp, b'MZmodified-binary')
        self.assert_failed('PE evidence archive changed')

    def test_raw_pe_mismatch_even_with_updated_manifest_is_rejected(self):
        self.make_pe_zip(self.lp, b'MZmodified-binary')
        self.linux['generated_pe_sha256'] = mod.archive_entries(self.lp)
        self.linux['generated_pe_bundle_sha256'] = mod.digest(self.lp)
        self.assert_failed('generated_pe_sha256')

    def test_missing_raw_pe_bundle_is_rejected(self):
        self.lp.unlink()
        self.assert_failed('Missing raw PE evidence archive')

    def test_compiled_pe_archive_contains_real_file_bytes(self):
        from hashlib import sha256
        root = Path(self.directory.name)/'source'
        pe_file = root/'dist'/'core'/'a3d.dll'
        pe_file.parent.mkdir(parents=True)
        pe_file.write_bytes(b'MZactual-probe-binary')
        expected = {'dist/core/a3d.dll': sha256(pe_file.read_bytes()).hexdigest()}
        evidence = root/'dist'/mod.PE_EVIDENCE_NAME
        mod.write_pe_evidence(root, evidence, expected)
        self.assertEqual(mod.archive_entries(evidence), expected)
        with zipfile.ZipFile(evidence) as z:
            self.assertEqual(z.read('dist/core/a3d.dll'), pe_file.read_bytes())
            self.assertEqual(z.infolist()[0].create_system, 3)
            self.assertEqual(z.infolist()[0].compress_type, zipfile.ZIP_STORED)

    def test_compiled_pe_archive_rejects_stale_digest(self):
        root = Path(self.directory.name)/'source'
        pe_file = root/'dist'/'core'/'a3d.dll'
        pe_file.parent.mkdir(parents=True)
        pe_file.write_bytes(b'MZactual-probe-binary')
        with self.assertRaisesRegex(ValueError, 'changed during evidence'):
            mod.write_pe_evidence(root, root/'evidence.zip',
                                  {'dist/core/a3d.dll': 'f'*64})

    def test_failed_manifest_emit_removes_stale_output(self):
        from unittest.mock import patch
        out = Path(self.directory.name)/'stale-manifest.json'
        out.write_text('{"stale":true}')
        with patch.object(mod, 'create_manifest', side_effect=ValueError('deliberate failure')):
            with patch.object(mod.sys, 'argv', ['verify_cross_platform.py', 'emit',
                                                '--llvm', '19.1.7', '--out', str(out)]):
                self.assertEqual(mod.main(), 1)
        self.assertFalse(out.exists())

    def test_certificate_emitter_rejects_dirty_checkout(self):
        from unittest.mock import patch
        values = iter(['a'*40, ' M scripts/build.py'])
        with patch.object(mod, 'command_stdout', side_effect=lambda *a, **k: next(values)):
            with self.assertRaisesRegex(ValueError, 'dirty checkout'):
                mod.clean_checkout_commit(ROOT)

    def test_ci_checkout_commit_mismatch_is_rejected(self):
        _, errors = mod.compare_builds(self.win, self.linux, self.a, self.b,
                                       self.wp, self.lp,
                                       expected_commit='different_commit')
        self.assertTrue(any('source commit is not CI checkout' in x for x in errors), errors)

    def test_different_source_bytes_are_rejected(self):
        self.linux['tracked_source_sha256']['scripts/build.py'] = 'f' * 64
        self.assert_failed('tracked_source_sha256')

    def test_missing_local_proof_is_rejected(self):
        self.linux['local_verification'] = 'unverified'
        self.assert_failed('missing same-host verification')

    def test_wrong_host_is_rejected(self):
        self.linux['host'] = 'windows'
        self.assert_failed('expected')

    def test_zip_contents_changed_after_emit_is_rejected(self):
        self.make_zip(self.b, b'changed')
        self.assert_failed('ZIP changed after manifest emission')

    def test_zip_metadata_difference_detected_even_if_entries_equal(self):
        self.make_zip(self.b, creator=0)
        self.linux['runtime_zip_sha256'] = mod.digest(self.b)
        self.linux['runtime_entries_sha256'] = mod.archive_entries(self.b)
        self.assertEqual(self.win['runtime_entries_sha256'], self.linux['runtime_entries_sha256'])
        self.assert_failed('Raw runtime ZIPs are NOT byte-for-byte identical')

    def test_missing_source_manifest_is_rejected(self):
        self.linux['tracked_source_sha256'] = {}
        self.assert_failed('missing/empty tracked_source_sha256')

    def test_archive_duplicate_members_rejected(self):
        with zipfile.ZipFile(self.b, 'a') as z:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', UserWarning)
                z.writestr('test/a3d.dll', b'bad')
        with self.assertRaises(ValueError):
            mod.archive_entries(self.b)

    def test_zip_creation_has_host_independent_metadata(self):
        contents = (ROOT/'scripts/build.py').read_text()
        self.assertIn('info.create_system = 3', contents)
        self.assertIn('zipfile.ZIP_STORED', contents)
        self.assertNotIn('zipfile.ZIP_DEFLATED', contents)

    def test_ci_build_and_compare_both_os(self):
        workflow = (ROOT/'.github/workflows/source-ci.yml').read_text()
        self.assertIn('matrix:', workflow)
        self.assertIn('ubuntu-24.04, windows-2022', workflow)
        self.assertIn('cross-platform-byte-identity:', workflow)
        self.assertIn('verify_cross_platform.py compare', workflow)
        self.assertIn('Aufake3D_Generated_PE_Evidence.zip', workflow)
        self.assertIn('--expected-commit', workflow)
        self.assertIn('19.1.7', workflow)
        self.assertIn('3.13.7', workflow)


if __name__ == '__main__':
    unittest.main()
