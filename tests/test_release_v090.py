"""v0.9.2 release integration: provider selection and queue defaults."""
from pathlib import Path
import json
import unittest
ROOT = Path(__file__).resolve().parents[1]

class Release0818(unittest.TestCase):
    def test_alice2011_bridge_source_and_kit_present(self):
        m=json.loads((ROOT/'packaging/Game_Kits/INSTALL_MAP.json').read_text())
        self.assertEqual(m['version'],'0.9.2')
        self.assertIn('alice-a3d2011-native.exe',m['profiles']['alice2011']['files'])
        self.assertTrue((ROOT/'Source/Engine/remaster2011/alice_a3d2011_bridge.c').is_file())
        build=(ROOT/'scripts/build.py').read_text()
        self.assertIn("'alice-a3d2011-native.exe': ENGINE/'remaster2011/alice-a3d2011-native.exe'",build)
    def test_2011_no_unknown_alias_and_uses_ram_bridge(self):
        base=ROOT/'packaging/Game_Kits/Alice_2011_VorpalFix/COPY_TO_GAME_FOLDER'
        for name in ('RUN_AUFAKE3D_WINDOWS.cmd','RUN_AUFAKE3D_WINE.sh'):
            with self.subTest(name=name):
                txt=(base/name).read_text()
                self.assertIn('A3D_MILES_ALIAS_UNKNOWN=0',txt)
                self.assertIn('alice-a3d2011-native.exe',txt)
                self.assertNotIn(' +set s_milesdriver a3d2',txt)
                self.assertIn('alice.exe.manifest',txt)
    def test_6_by_256_32ms_config_for_three_games(self):
        base=ROOT/'packaging/Game_Kits'
        for game in ('Alice_2000','Alice_2011_VorpalFix','Quake_III_117'):
            for name in ('RUN_AUFAKE3D_WINDOWS.cmd','RUN_AUFAKE3D_WINE.sh'):
                txt=(base/game/'COPY_TO_GAME_FOLDER'/name).read_text()
                with self.subTest(game=game,name=name):
                    self.assertIn('A3D_WAVEOUT_QUEUE_HEADERS',txt)
                    self.assertIn('A3D_WAVEOUT_SUBBLOCKS',txt)
                    self.assertIn('6',txt)
                    self.assertIn('1',txt)

if __name__ == '__main__': unittest.main()
