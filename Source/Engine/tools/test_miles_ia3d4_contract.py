# v0.5.0 SOURCE COMMENTARY — Regression test / harness
# Exercises the release implementation or checks its ABI/packaging contract. Do not
# treat fixture success as proof of native Wine or retail-game compatibility.
import pathlib
import unittest

R = pathlib.Path(__file__).resolve().parents[1]

class MilesIA3d4Contract(unittest.TestCase):
    def test_wrapper_has_exact_ia3d4_guid_and_methods(self):
        src=(R/'win32/a3dapi.c').read_text()
        for term in ('0xe4c40280','0xccba','0x11d2','SetRMPriorityBias','GetRMPriorityBias',
                     'DisableViewer','SetUnitsPerMeter','GetUnitsPerMeter','SetDopplerScale',
                     'GetDopplerScale','SetDistanceModelScale','GetDistanceModelScale',
                     'SetEq','GetEq','Shutdown','RegisterApp'):
            self.assertIn(term,src)
        self.assertIn('eqguid(i,&iid_ia3d4)',src)
    def test_com_and_selftest_exercise_ia3d4(self):
        for n in ['selftest.c','com_test.c']:
            src=(R/'win32'/n).read_text()
            self.assertIn('ia3d4',src)
            self.assertIn('0xe4c40280',src)
        self.assertIn('IA3d4.QueryInterface(IA3dGeom)',(R/'win32/com_test.c').read_text())
