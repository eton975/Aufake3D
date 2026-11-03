"""Source-only independent audio-reference target smoke tests (no NumPy needed)."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / 'scripts' / 'build_audio_reference.py'

spec = importlib.util.spec_from_file_location('audio_reference_builder', BUILDER)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class AudioReferenceBuildTargetTests(unittest.TestCase):
    def test_audio_source_files_are_allowlisted_and_captured_data_excluded(self):
        names = module.INPUTS
        self.assertEqual(len(names), 19)
        self.assertEqual(len(set(names)), len(names))
        self.assertNotIn('SHA256SUMS.txt', names)
        self.assertTrue(all(not n.endswith(('.wav', '.dm3', '.pk3', '.exe', '.dll')) for n in names))
        self.assertTrue(all((module.SRC / n).is_file() for n in names))

    def test_archive_is_deterministic_and_manifest_valid(self):
        a = module.produce_zip()
        b = module.produce_zip()
        self.assertEqual(a, b)
        self.assertEqual(module._verify_zip(a), module._verify_zip(b))
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'audit.zip'
            p.write_bytes(a)
            with zipfile.ZipFile(p) as z:
                self.assertEqual(len(z.infolist()), len(module.INPUTS)+1)
                self.assertTrue(all(i.date_time[:3] == (1980,1,1) for i in z.infolist()))

    def test_legacy_build_entry_points_are_separate(self):
        self.assertNotIn('scripts/build.py', BUILDER.read_text())
        self.assertTrue((ROOT / 'BUILD_AUDIO_REFERENCE_WINDOWS.cmd').is_file())
        self.assertTrue((ROOT / 'BUILD_AUDIO_REFERENCE_LINUX.sh').is_file())

    def test_corrupt_zip_rejected(self):
        a = bytearray(module.produce_zip())
        with zipfile.ZipFile(__import__('io').BytesIO(a)) as z:
            info = z.infolist()[0]
            # For stored members the payload begins immediately after filename.
            pos = info.header_offset + 30 + len(info.filename.encode('utf-8'))
        a[pos] ^= 0x01
        with self.assertRaises((SystemExit, zipfile.BadZipFile)):
            module._verify_zip(bytes(a))

if __name__ == '__main__':
    unittest.main()
