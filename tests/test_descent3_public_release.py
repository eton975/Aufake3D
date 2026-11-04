"""Public Descent 3 ZIP is deterministic, universal-core-only and fail-closed."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zipfile

from scripts import package_descent3_release as pkg
from scripts import verify_descent3_release as certify


def fake_pe(marker: bytes) -> bytes:
    data = bytearray(512)
    data[:2] = b'MZ'
    struct.pack_into('<I', data, 0x3C, 0x80)
    data[0x80:0x84] = b'PE\x00\x00'
    struct.pack_into('<H', data, 0x84, 0x14C)
    struct.pack_into('<H', data, 0x94, 0xE0)
    struct.pack_into('<H', data, 0x98, 0x10B)
    data[256:256+len(marker)] = marker
    return bytes(data)


class Descent3PublicRelease(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.root = Path(self.td.name)
        self.cores = {'a3d.dll': fake_pe(b'one'), 'a3dapi.dll': fake_pe(b'two')}

    def test_zip_byte_identical_and_has_fixed_metadata(self):
        contents = pkg.payload_from_core(self.cores)
        a = pkg.make_zip(contents)
        self.assertEqual(a, pkg.make_zip(dict(reversed(list(contents.items())))))
        pkg.verify_archive(a, contents)
        with zipfile.ZipFile(__import__('io').BytesIO(a)) as z:
            self.assertEqual(len(z.namelist()), 4)
            for name in pkg.CORE:
                self.assertEqual(z.read(pkg.PREFIX+pkg.GAME_FOLDER+name), self.cores[name])
            for info in z.infolist():
                self.assertEqual(info.date_time, pkg.ZIP_DATE)
                self.assertEqual(info.compress_type, zipfile.ZIP_STORED)
                self.assertEqual(info.create_system, 3)
        self.assertNotIn(b'descent3-aureal-standalone-adapter.obj', a)
        self.assertNotIn(b'contract-probe.exe', a)

    def test_no_stale_or_wrong_architecture_dll(self):
        with self.assertRaisesRegex(ValueError, 'two shared core'):
            pkg.payload_from_core({'a3d.dll': self.cores['a3d.dll']})
        with self.assertRaisesRegex(ValueError, 'PE'):
            pkg.payload_from_core({'a3d.dll': b'not a PE', 'a3dapi.dll': self.cores['a3dapi.dll']})

    def make_evidence(self):
        commit = 'a'*40
        package = pkg.make_zip(pkg.payload_from_core(self.cores))
        for target in certify.TARGETS:
            folder = self.root/target
            folder.mkdir()
            with zipfile.ZipFile(folder/certify.RUNTIME_NAME, 'w', compression=zipfile.ZIP_STORED) as z:
                for name, data in self.cores.items():
                    z.writestr(f'Aufake3D-v{pkg.VERSION}-Local/Universal_Core/{name}', data)
            runtime_hash = hashlib.sha256((folder/certify.RUNTIME_NAME).read_bytes()).hexdigest()
            (folder/pkg.FILENAME).write_bytes(package)
            (folder/'manifest.json').write_text(json.dumps({
                'target': target,
                'source_commit': commit,
                'local_verification': 'three-way-bit-identical',
                'runtime_zip_name': certify.RUNTIME_NAME,
                'runtime_zip_sha256': runtime_hash,
            }))
        cert = self.root/'base-cert.json'
        cert.write_text(json.dumps({
            'source_commit': commit,
            'targets': list(certify.TARGETS),
            'runtime_zip_name': certify.RUNTIME_NAME,
            'runtime_zip_sha256': hashlib.sha256((self.root/certify.TARGETS[0]/certify.RUNTIME_NAME).read_bytes()).hexdigest(),
        }))
        return commit, cert, {t: self.root/t for t in certify.TARGETS}

    def test_five_target_public_zip_proof_passes(self):
        commit, cert, folders = self.make_evidence()
        out = certify.certify(folders, commit, cert)
        self.assertEqual(out['targets'], list(certify.TARGETS))
        self.assertEqual(out['status'], 'five-target-byte-identical')
        self.assertEqual(out['public_zip_sha256'], pkg.sha256((folders['windows-2022']/pkg.FILENAME).read_bytes()))

    def test_malformed_or_missing_target_fails(self):
        commit, cert, folders = self.make_evidence()
        del folders['debian-13']
        with self.assertRaisesRegex(ValueError, 'five mandatory'):
            certify.certify(folders, commit, cert)

    def test_tampering_public_zip_fails_even_if_other_hosts_match(self):
        commit, cert, folders = self.make_evidence()
        target = folders['debian-13']/pkg.FILENAME
        target.write_bytes(target.read_bytes()+b'changed')
        with self.assertRaisesRegex(ValueError, 'differs from deterministic rebuild'):
            certify.certify(folders, commit, cert)

    def test_tampered_runtime_core_fails(self):
        commit, cert, folders = self.make_evidence()
        file = folders['ubuntu-26.10']/certify.RUNTIME_NAME
        file.write_bytes(file.read_bytes()+b'tampered')
        with self.assertRaisesRegex(ValueError, 'runtime differs'):
            certify.certify(folders, commit, cert)

    def test_source_commit_mismatch_fails(self):
        commit, cert, folders = self.make_evidence()
        with self.assertRaisesRegex(ValueError, 'certificate missing or inconsistent'):
            certify.certify(folders, 'b'*40, cert)

    def test_canonical_public_zip_from_current_dlls(self):
        for name, data in self.cores.items():
            target = self.root/'dist/core'/name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        out = pkg.build(self.root)
        self.assertEqual(out.parent, self.root/'dist')
        self.assertEqual(out.name, pkg.FILENAME)
        self.assertTrue((out.parent/'DESCENT3_PUBLIC_RELEASE_SHA256.json').is_file())
        self.assertEqual(pkg.sha256(out.read_bytes()), json.loads(
            (out.parent/'DESCENT3_PUBLIC_RELEASE_SHA256.json').read_text())['archive_sha256'])

if __name__ == '__main__':
    unittest.main()
