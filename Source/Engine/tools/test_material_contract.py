# v0.5.0 SOURCE COMMENTARY — Regression test / harness
# Exercises the release implementation or checks its ABI/packaging contract. Do not
# treat fixture success as proof of native Wine or retail-game compatibility.
"""Verify the independently reconstructed vtable slots confirmed in Miles assembly.

Original mssa3d2.m3d (2000) calls IA3dMaterial::SetNameID at slot 8,
SetReflectance at slot 12 and SetTransmittance at slot 14.
"""
from pathlib import Path
import re
import unittest
P = Path(__file__).resolve().parents[1]
class MaterialContract(unittest.TestCase):
    def test_material_vtable_slots(self):
        s = (P / 'win32/geom_trace.inc').read_text()
        match = re.search(r'static const MaterialVtbl material_vt=\{(.*?)\};', s, re.S)
        self.assertIsNotNone(match)
        parts = re.sub(r'/\*.*?\*/','',match.group(1),flags=re.S).replace('\n','').split(',')
        parts = [p.strip() for p in parts]
        self.assertEqual(len(parts),16)
        self.assertEqual(parts[8], 'msetname')
        self.assertEqual(parts[12],'msetreflect')
        self.assertEqual(parts[14],'msettrans')
    def test_selftest_checks_material_roundtrip(self):
        s = (P / 'win32/selftest.c').read_text()
        for needle in ('gg->vt[35]', 'gg->vt[36]', 'mat->vt[12]', 'mat->vt[13]', 'mat->vt[14]', 'mat->vt[15]'):
            self.assertIn(needle,s)
    def test_safe_synthetic_material_no_claim_of_audio(self):
        s = (P / 'win32/geom_trace.inc').read_text()
        self.assertIn('HeapAlloc',s)
        self.assertIn('HeapFree',s)
        self.assertIn('diagnostic material object',s)
        self.assertIn('IA3dGeom.BindMaterial => S_OK',s)
if __name__=='__main__': unittest.main()
