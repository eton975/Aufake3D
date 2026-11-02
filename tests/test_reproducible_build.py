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

    def test_copy_excludes_build_outputs(self):
        self.assertIn('dist', repro.IGNORED_DIRS)
        self.assertIn('build', repro.IGNORED_DIRS)
        self.assertIn('.dll', repro.IGNORED_EXTENSIONS)


if __name__ == '__main__':
    unittest.main()
