"""Guard against accidental permanent provider override in Alice launchers."""
from pathlib import Path
import re
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
KITS = ROOT / 'packaging' / 'Game_Kits'


class InitialA3D2Default(unittest.TestCase):
    def test_launchers_seed_only_once_and_keep_dynamic_selector(self):
        for game, bridge in [('Alice_2000', 'alice-a3d-bridge.exe'),
                             ('Alice_2011_VorpalFix', 'alice-a3d2011-native.exe')]:
            with self.subTest(game=game):
                folder = KITS / game / 'COPY_TO_GAME_FOLDER'
                launch = (folder / 'RUN_AUFAKE3D_WINDOWS.cmd').read_text()
                seed = (folder / 'AUFAKE3D_SET_INITIAL_A3D2.ps1').read_text()
                self.assertIn('AUFAKE3D_A3D2_INITIAL_DEFAULT_DONE.txt', launch)
                self.assertIn('AUFAKE3D_SET_INITIAL_A3D2.ps1', launch)
                self.assertIn(bridge, launch)
                self.assertIsNone(re.search(r'(?m)^\s*(?:"[^\"]*"|\S+)?\s*\+set\s+s_milesdriver', launch,
                                                  re.IGNORECASE), 'Never force CLI provider at launch')
                self.assertIn("if ([IO.File]::Exists($marker)) { exit 0 }", seed)
                self.assertIn('seta s_milesdriver "a3d2"', seed)
                self.assertIn('AUFAKE3D_before_A3D2_default.bak', seed)
                self.assertNotIn('autoexec.cfg', launch)
                self.assertNotIn('A3D_MILES_ALIAS_UNKNOWN=1', launch)
                self.assertIn('A3D_WAVEOUT_QUEUE_HEADERS=6', launch)
                self.assertIn('A3D_WAVEOUT_SUBBLOCKS=1', launch)

    def test_install_map_includes_helper_for_automatic_installers(self):
        profile_map = json.loads((KITS / 'INSTALL_MAP.json').read_text())['profiles']
        for name in ('alice2000','alice2011'):
            with self.subTest(profile=name):
                self.assertIn('AUFAKE3D_SET_INITIAL_A3D2.ps1', profile_map[name]['files'])
                self.assertEqual(len(profile_map[name]['files']), len(set(profile_map[name]['files'])))

    def test_2011_does_not_seed_multiple_configs(self):
        seed = (KITS / 'Alice_2011_VorpalFix/COPY_TO_GAME_FOLDER/AUFAKE3D_SET_INITIAL_A3D2.ps1').read_text()
        self.assertIn("My Games\\American McGee's Alice\\config.cfg", seed)
        self.assertNotIn('$targets.Add($localConfig) }', seed)


if __name__ == '__main__':
    unittest.main()
