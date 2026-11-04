"""Tests binary scanner without inspecting or distributing any commercial file."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('d3scanner',ROOT/'Tools/inspect_descent3_executable.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def _probe_path():
    # Prefer the new explicit, persistent experimental target but retain
    # compatibility with the original independent probe builder.
    current=ROOT/'dist/descent3/a3d-descent3-contract-probe.exe'
    older=ROOT/'dist/experimental-descent3/a3d-descent3-contract-probe.exe'
    return current if current.is_file() else older

class Descent3PEInventory(unittest.TestCase):
    def test_rejects_garbage_and_missing(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'main.exe'
            with self.assertRaises(ValueError):m.inspect(p)
            p.write_bytes(b'not a PE')
            with self.assertRaises(ValueError):m.inspect(p)

    def test_own_synthetic_pe(self):
        p=_probe_path()
        if not p.exists(): self.skipTest('probe build not present')
        r=m.inspect(p)
        self.assertEqual(r['architecture'],'x86')
        self.assertFalse(r['a3d_path_confirmed'])
        self.assertFalse(r['gameplay_verified'])
        self.assertTrue(any('LoadLibraryA' in s for s in r['possible_activation_imports']))
        self.assertIn('a3dapi.dll',r['static_text_markers'])
        self.assertEqual(r['aureal_static_imports'],[])

    def test_deterministic_report_and_no_executable_writes(self):
        p=_probe_path()
        if not p.exists(): self.skipTest('probe build not present')
        before=p.read_bytes()
        self.assertEqual(m.inspect(p),m.inspect(p))
        self.assertEqual(p.read_bytes(),before)

if __name__=='__main__':unittest.main()
