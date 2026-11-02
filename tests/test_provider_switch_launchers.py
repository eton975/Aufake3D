"""Regression contracts for Alice's in-game 2D/A3D2 provider selection."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
KITS = ROOT / 'packaging' / 'Game_Kits'


class AliceProviderSwitch(unittest.TestCase):
    def test_alice_launchers_respect_persisted_provider(self):
        for game in ('Alice_2000', 'Alice_2011_VorpalFix'):
            base = KITS / game / 'COPY_TO_GAME_FOLDER'
            for fname in ('RUN_AUFAKE3D_WINDOWS.cmd', 'RUN_AUFAKE3D_WINE.sh'):
                with self.subTest(game=game, launcher=fname):
                    script = (base / fname).read_text()
                    self.assertNotIn(' +set s_milesdriver a3d2', script,
                                     'Launcher must not force the A3D2 choice')
                    self.assertIn('alice-a3d-bridge.exe' if game == 'Alice_2000'
                                  else 'alice-a3d2011-native.exe', script)

    def test_alice_2011_ram_bridge_replaces_unknown_alias(self):
        base = KITS / 'Alice_2011_VorpalFix' / 'COPY_TO_GAME_FOLDER'
        for fname in ('RUN_AUFAKE3D_WINDOWS.cmd', 'RUN_AUFAKE3D_WINE.sh'):
            with self.subTest(launcher=fname):
                script = (base / fname).read_text()
                self.assertIn('A3D_MILES_ALIAS_UNKNOWN=0', script)
                self.assertIn('A3D_MILES_REQUIRE_CLI_A3D2=1', script)
                self.assertNotIn('A3D_MILES_REQUIRE_CLI_A3D2=0', script)

    def test_classic_selector_bridge_is_based_on_game_token_not_cli(self):
        bridge = (ROOT / 'Source/Engine/classic2000/alice_a3d_bridge.c').read_text()
        self.assertIn('a3d2', bridge)
        self.assertIn('mov al, [ebx]', bridge)


if __name__ == '__main__':
    unittest.main()
