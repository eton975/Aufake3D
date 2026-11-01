"""Consolidated v0.6.0 release deployment contract tests."""
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

class FinalRelease(unittest.TestCase):
    def test_portable_bin_contains_three_game_frontends(self):
        folder=ROOT/'portable/bin'
        for n in ['a3dapi.dll','a3d.dll','alice-a3d-bridge.exe','alice-a3d2011-bridge.exe']:
            b=(folder/n).read_bytes()
            self.assertEqual(b[:2],b'MZ',n)
            off=int.from_bytes(b[0x3c:0x40],'little')
            self.assertEqual(b[off:off+4],b'PE\0\0',n)
            self.assertEqual(int.from_bytes(b[off+4:off+6],'little'),0x14c,n)

    def test_quake_preset_quality_profile(self):
        s=(ROOT/'portable/run_quake3_117_wine.sh').read_text()
        for item in ['A3D_HRTF_TAPS:=48','A3D_GEOMETRY_RETRACE_BLOCKS:=4',
                     'A3D_REVERB_WET:=0.14','A3D_VOICE_LIMIT:=128','A3D_MASTER_GAIN:=5.0',
                     '+set s_mixahead 0.35','+set s_mixPreStep 0.05']:
            self.assertIn(item,s)

    def test_alice_selectors_distinct(self):
        classic=(ROOT/'portable/run_alice2000_wine.sh').read_text()
        remaster=(ROOT/'portable/run_alice2011_wine.sh').read_text()
        self.assertIn('alice-a3d-bridge.exe',classic)
        self.assertNotIn('alice-a3d2011-bridge.exe',classic)
        self.assertIn('alice-a3d2011-bridge.exe',remaster)
        self.assertIn('winmm=n,b',remaster)
        self.assertIn('winepath -w',remaster)

    def test_documentation_does_not_claim_remaster_runtime_pass(self):
        txt=(ROOT/'portable/README.md').read_text()
        self.assertIn('playback under Wine remains unverified',txt)

if __name__ == '__main__': unittest.main()
