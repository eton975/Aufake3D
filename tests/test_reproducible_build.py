"""Regression tests for byte-identical release packaging and PE timestamps."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('verify_reproducible', ROOT/'scripts/verify_reproducible.py')
repro = importlib.util.module_from_spec(spec)
spec.loader.exec_module(repro)


class TestReproducibleBuild(unittest.TestCase):
    def test_alice2000_bridge_has_fixed_linker_timestamp(self):
        build = (ROOT/'scripts/build.py').read_text(encoding='utf-8')
        section = build.split('def build_alice_bridge(', 1)[1].split('\ndef ', 1)[0]
        self.assertIn("'/timestamp:0'", section)

    def test_zip_comparison_detects_content_difference(self):
        with tempfile.TemporaryDirectory() as td:
            a, b = [Path(td)/name for name in ('a.zip', 'b.zip')]
            for p, content in ((a, b'one'), (b, b'two')):
                with zipfile.ZipFile(p, 'w') as z:
                    z.writestr('sample.txt', content)
            self.assertFalse(repro.compare_zips(a, b))
            self.assertIn('Entry differs: sample.txt', repro.zip_differences(a, b))

    def test_zip_comparison_accepts_identical_archives(self):
        with tempfile.TemporaryDirectory() as td:
            a, b = [Path(td)/name for name in ('a.zip', 'b.zip')]
            with zipfile.ZipFile(a, 'w') as z:
                z.writestr('sample.txt', b'content')
            b.write_bytes(a.read_bytes())
            self.assertTrue(repro.compare_zips(a, b))

    def test_packaged_build_requires_same_toolchain_rebuilds(self):
        script=(ROOT/'scripts/build.py').read_text()
        verifier=(ROOT/'scripts/verify_reproducible.py').read_text()
        self.assertIn("'--verify-current'",script)
        self.assertIn("'--skip-repro-check'",verifier)
        self.assertIn('generated_pe_sha256',verifier)
        self.assertIn('three-way-bit-identical',verifier)
        self.assertIn('cross-host identity NOT established',verifier)

    def test_approval_report_rejects_stale_archive(self):
        import json
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/'dist').mkdir()
            zip_file=root/'dist'/'test.zip'
            with zipfile.ZipFile(zip_file, 'w') as z:
                z.writestr('alpha',b'first')
            report=root/'dist'/'approved.json'
            report.write_text(json.dumps({
                'version':'test', 'verification':'three-way-bit-identical',
                'runtime_zip':'dist/test.zip','runtime_sha256':repro.file_hash(zip_file),
                'generated_pe_sha256':{}
            }))
            with patch.object(repro,'ROOT',root),patch.object(repro,'VERSION','test'), \
                 patch.object(repro,'OUTPUT','dist/test.zip'),patch.object(repro,'REPORT','dist/approved.json'):
                self.assertTrue(repro.check_report())
                with zipfile.ZipFile(zip_file, 'w') as z:
                    z.writestr('alpha',b'changed')
                self.assertFalse(repro.check_report())

    def test_copy_excludes_build_outputs(self):
        self.assertIn('dist', repro.IGNORED_DIRS)
        self.assertIn('build', repro.IGNORED_DIRS)
        self.assertIn('.dll', repro.IGNORED_EXTENSIONS)


if __name__ == '__main__':
    unittest.main()
