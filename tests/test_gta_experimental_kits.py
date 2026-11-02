"""Experimental GTA kit contract: no vendor DLL replacement and shared renderer."""
import json
import sys
import tempfile
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'Tools'))
from scan_game_a3d_markers import inventory

class GtaKitTests(unittest.TestCase):
    def setUp(self):
        self.kits=ROOT/'packaging/Game_Kits'
        self.profiles=json.loads((self.kits/'INSTALL_MAP.json').read_text())['profiles']

    def test_gta_kits_use_only_shared_a3d_core(self):
        for key,folder,exe in [('gta3','GTA_III','gta3.exe'),('gtavc','GTA_Vice_City','gta-vc.exe')]:
            profile=self.profiles[key]
            self.assertEqual(profile['folder'],folder)
            self.assertEqual(profile['exe'],exe)
            self.assertIn('a3d.dll',profile['files'])
            self.assertIn('a3dapi.dll',profile['files'])
            self.assertNotIn('mss32.dll',profile['files'])
            self.assertFalse(any(x.endswith('.m3d') for x in profile['files']))
            d=self.kits/folder/'COPY_TO_GAME_FOLDER'
            self.assertEqual(sorted(x.name for x in d.iterdir()),sorted(x for x in profile['files'] if x not in ('a3d.dll','a3dapi.dll')))
            cmd=(d/'RUN_AUFAKE3D_WINDOWS.cmd').read_text()
            self.assertIn('A3D_HRTF_MODE=reference',cmd)
            self.assertIn('mss32.dll',cmd)
            self.assertNotIn('A3D_MILES_ALIAS_UNKNOWN',cmd)
            self.assertNotIn('s_milesdriver',cmd)
            self.assertIn(exe,cmd)

    def test_marker_inventory_is_read_only_and_explicitly_inconclusive(self):
        with tempfile.TemporaryDirectory() as directory:
            exe=Path(directory)/'WolfSP.exe'
            original=b'MZ '+b'Mssa3d2.m3d A3DAPI.dll DSOUND.dll'
            exe.write_bytes(original)
            report=inventory(exe)
            self.assertEqual(exe.read_bytes(),original)
            self.assertEqual(report['count'],1)
            self.assertIn('MSSA3D2.M3D',report['files'][0]['markers'])
            self.assertIn('A3DAPI.DLL',report['files'][0]['markers'])
            self.assertIn('does NOT establish',report['interpretation'])

if __name__=='__main__': unittest.main()
