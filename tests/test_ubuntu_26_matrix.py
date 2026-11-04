"""Four-runner byte-identity policy: the extra Ubuntu jobs may never be optional."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from scripts import verify_cross_platform as core
from scripts import verify_matrix_reproducibility as matrix

ROOT = Path(__file__).resolve().parents[1]
COMMIT = 'a' * 40


class Ubuntu26MatrixTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.bundles = {}
        for name in [matrix.WINDOWS, *matrix.UBUNTU_TARGETS]:
            folder = root/name
            folder.mkdir()
            archive = folder/'runtime.zip'
            pe = folder/'pe-evidence.zip'
            self.make_zip(archive, b'fixed-runtime')
            self.make_zip(pe, b'MZfixed-binary')
            win = name == matrix.WINDOWS
            self.bundles[name] = ({
                'schema': core.SCHEMA,
                'target': name, 'host': 'windows' if win else 'linux',
                'os_id': 'windows' if win else 'ubuntu',
                'os_version': '20348' if win else name.replace('ubuntu-', ''),
                'source_commit': COMMIT,
                'python_version': matrix.PYTHON_VERSION,
                'llvm_versions': {'clang': matrix.LLVM_VERSION,
                                  'lld-link': matrix.LLVM_VERSION},
                'local_verification': 'three-way-bit-identical',
                'runtime_zip_name': archive.name,
                'runtime_zip_sha256': core.digest(archive),
                'runtime_entries_sha256': core.archive_entries(archive),
                'generated_pe_bundle_name': pe.name,
                'generated_pe_bundle_sha256': core.digest(pe),
                'generated_pe_sha256': core.archive_entries(pe),
                'tracked_source_sha256': {'scripts/build.py': 'a' * 64},
            }, archive, pe)

    @staticmethod
    def make_zip(path: Path, data: bytes):
        with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_STORED) as z:
            info = zipfile.ZipInfo('test/a3d.dll', (2026, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.compress_type = zipfile.ZIP_STORED
            z.writestr(info, data)

    def compare(self, target_names=None):
        names = target_names if target_names is not None else matrix.UBUNTU_TARGETS
        return matrix.compare_matrix(self.bundles[matrix.WINDOWS],
                                     {name: self.bundles[name] for name in names}, COMMIT)

    def test_all_four_identical_builds_certify(self):
        certificate, errors = self.compare()
        self.assertEqual([], errors)
        self.assertEqual(certificate['targets'], [matrix.WINDOWS, *matrix.UBUNTU_TARGETS])
        self.assertEqual(certificate['runtime_zip_sha256'], self.bundles[matrix.WINDOWS][0]['runtime_zip_sha256'])

    def test_missing_ubuntu_2610_refuses_certificate(self):
        certificate, errors = self.compare(('ubuntu-24.04', 'ubuntu-26.04'))
        self.assertIsNone(certificate)
        self.assertIn('mandatory targets', ' '.join(errors))

    def test_missing_ubuntu_2604_refuses_certificate(self):
        certificate, errors = self.compare(('ubuntu-24.04', 'ubuntu-26.10'))
        self.assertIsNone(certificate)
        self.assertIn('mandatory targets', ' '.join(errors))

    def test_fake_2610_os_identity_refuses_certificate(self):
        self.bundles['ubuntu-26.10'][0]['os_version'] = '26.04'
        certificate, errors = self.compare()
        self.assertIsNone(certificate)
        self.assertTrue(any('claimed target' in x for x in errors), errors)

    def test_changed_2610_pe_refuses_certificate(self):
        self.bundles['ubuntu-26.10'][0]['generated_pe_sha256']['test/a3d.dll'] = '0'*64
        certificate, errors = self.compare()
        self.assertIsNone(certificate)
        self.assertTrue(any('generated_pe_sha256' in x for x in errors), errors)

    def test_changed_2604_zip_refuses_certificate(self):
        m, runtime, pe = self.bundles['ubuntu-26.04']
        self.make_zip(runtime, b'changed but same filename')
        m['runtime_zip_sha256'] = core.digest(runtime)
        m['runtime_entries_sha256'] = core.archive_entries(runtime)
        certificate, errors = self.compare()
        self.assertIsNone(certificate)
        self.assertTrue(any('raw runtime ZIP' in x or 'runtime_zip_sha256' in x for x in errors), errors)

    def test_different_commit_refuses_certificate(self):
        self.bundles['ubuntu-26.10'][0]['source_commit'] = 'b'*40
        _, errors = self.compare()
        self.assertTrue(any('source commit' in x for x in errors), errors)

    def test_unpinned_llvm_refuses_certificate(self):
        self.bundles['ubuntu-26.10'][0]['llvm_versions']['clang'] = '22.1.8'
        _, errors = self.compare()
        self.assertTrue(any('LLVM must be pinned' in x for x in errors), errors)

    def test_emitter_rejects_false_2610_claim(self):
        with patch.object(core.platform, 'system', return_value='Linux'), patch.object(
                core.platform, 'freedesktop_os_release', return_value={'ID': 'ubuntu', 'VERSION_ID': '26.04'}):
            with self.assertRaisesRegex(ValueError, 'requires Ubuntu 26.10'):
                core.verify_build_target('ubuntu-26.10')

    def test_emitter_accepts_real_2610(self):
        with patch.object(core.platform, 'system', return_value='Linux'), patch.object(
                core.platform, 'freedesktop_os_release', return_value={'ID': 'ubuntu', 'VERSION_ID': '26.10'}):
            self.assertEqual(core.verify_build_target('ubuntu-26.10')['target'], 'ubuntu-26.10')

    def test_manifest_cannot_escape_artifact_directory(self):
        folder = Path(self.tmp.name)/'malicious'
        folder.mkdir()
        (folder/'manifest.json').write_text(json.dumps({
            'runtime_zip_name': '../runtime.zip', 'generated_pe_bundle_name': 'pe.zip'}))
        with self.assertRaisesRegex(ValueError, 'Invalid runtime_zip_name'):
            matrix.load_bundle(folder)

    def test_cli_failure_deletes_old_certificate(self):
        cert = Path(self.tmp.name)/'stale-certificate.json'
        cert.write_text('{"not_really": "certified"}')
        from unittest.mock import patch as mock_patch
        with mock_patch.object(matrix.sys, 'argv', [
                'verify_matrix_reproducibility.py', '--windows', str(Path(self.tmp.name)/'windows'),
                '--linux-target', 'ubuntu-24.04='+str(Path(self.tmp.name)/'ubuntu-24.04'),
                '--out', str(cert), '--expected-commit', COMMIT]):
            self.assertEqual(matrix.main(), 1)
        self.assertFalse(cert.exists())

    def test_cli_success_writes_single_four_target_certificate(self):
        from unittest.mock import patch as mock_patch
        for name, bundle in self.bundles.items():
            (Path(self.tmp.name)/name/'manifest.json').write_text(json.dumps(bundle[0]))
        cert = Path(self.tmp.name)/'certificate.json'
        arguments = ['verify_matrix_reproducibility.py', '--windows',
                     str(Path(self.tmp.name)/matrix.WINDOWS)]
        for target in matrix.UBUNTU_TARGETS:
            arguments += ['--linux-target', target+'='+str(Path(self.tmp.name)/target)]
        arguments += ['--out', str(cert), '--expected-commit', COMMIT]
        with mock_patch.object(matrix.sys, 'argv', arguments):
            self.assertEqual(matrix.main(), 0)
        contents = json.loads(cert.read_text())
        self.assertEqual(contents['targets'], [matrix.WINDOWS, *matrix.UBUNTU_TARGETS])

    def test_cli_tampered_2610_evidence_rejects_and_removes_stale_certificate(self):
        from unittest.mock import patch as mock_patch
        for name, bundle in self.bundles.items():
            (Path(self.tmp.name)/name/'manifest.json').write_text(json.dumps(bundle[0]))
        cert = Path(self.tmp.name)/'certificate.json'
        cert.write_text('old proof')
        pe = self.bundles['ubuntu-26.10'][2]
        self.make_zip(pe, b'MZmodified-real-binary')
        arguments = ['verify_matrix_reproducibility.py', '--windows',
                     str(Path(self.tmp.name)/matrix.WINDOWS)]
        for target in matrix.UBUNTU_TARGETS:
            arguments += ['--linux-target', target+'='+str(Path(self.tmp.name)/target)]
        arguments += ['--out', str(cert), '--expected-commit', COMMIT]
        with mock_patch.object(matrix.sys, 'argv', arguments):
            self.assertEqual(matrix.main(), 1)
        self.assertFalse(cert.exists())

    def test_workflow_references_four_unique_required_target_artifacts(self):
        workflow = (ROOT/'.github/workflows/source-ci.yml').read_text()
        for target in [matrix.WINDOWS, *matrix.UBUNTU_TARGETS]:
            self.assertIn('Aufake3D-cross-'+target, workflow)
            self.assertIn('verification/'+target if target.startswith('ubuntu') else 'verification/windows', workflow)
        self.assertIn('needs: [windows-and-linux, ubuntu-2610-container]', workflow)
        self.assertIn('runs-on: ubuntu-26.04', workflow)
        self.assertIn('ubuntu:26.10@sha256:', workflow)
        self.assertIn('verify_matrix_reproducibility.py', workflow)
        self.assertIn('--expected-commit', workflow)


if __name__ == '__main__':
    unittest.main()
