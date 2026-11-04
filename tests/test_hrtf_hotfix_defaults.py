"""Regression contract: every public active Windows/Wine game launcher defaults to reference."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
GAMES = ('Alice_2000', 'Alice_2011_VorpalFix', 'Quake_III_117',
         'Half_Life_1011', 'Unreal_Classic', 'Return_to_Castle_Wolfenstein',
         'GTA_III', 'GTA_Vice_City')

class HrtfHotfixDefaults(unittest.TestCase):
    def test_all_sixteen_launchers_default_to_reference_with_user_overrides(self):
        for game in GAMES:
            directory = ROOT / 'packaging' / 'Game_Kits' / game / 'COPY_TO_GAME_FOLDER'
            with self.subTest(game=game, platform='Windows'):
                path = directory/'RUN_AUFAKE3D_WINDOWS.cmd'
                source = path.read_text(encoding='utf-8')
                self.assertIn('if not defined A3D_HRTF_MODE set "A3D_HRTF_MODE=reference"', source)
                self.assertNotIn('set "A3D_HRTF_MODE=fast"', source)
            with self.subTest(game=game, platform='Wine'):
                path = directory/'RUN_AUFAKE3D_WINE.sh'
                source = path.read_text(encoding='utf-8')
                self.assertIn('export A3D_HRTF_MODE="${A3D_HRTF_MODE:-reference}"', source)
                self.assertNotIn('A3D_HRTF_MODE:-fast', source)

    def test_exactly_eight_current_games_not_historical_templates(self):
        dirs = ROOT/'packaging'/'Game_Kits'
        found = {p.parent.parent.name for p in dirs.glob('*/COPY_TO_GAME_FOLDER/RUN_AUFAKE3D_WINDOWS.cmd')}
        self.assertEqual(found, set(GAMES))

if __name__ == '__main__':
    unittest.main()
