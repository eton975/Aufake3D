"""One renderer for all game kits; game-specific selector bridges are not forks.

Tests intentionally do not claim successful playback in Alice 2011. They
prevent the packaging of stale per-game DLLs and accidental A3D2 stickiness.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build import assert_unified_core


class UnifiedAlice2011Renderer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile_root = ROOT / 'packaging' / 'Game_Kits'
        cls.installer = json.loads((cls.profile_root / 'INSTALL_MAP.json').read_text())

    def test_alice2011_modes_are_shared_and_overrideable(self):
        profile = self.profile_root / 'Alice_2011_VorpalFix' / 'COPY_TO_GAME_FOLDER'
        win = (profile / 'RUN_AUFAKE3D_WINDOWS.cmd').read_text()
        wine = (profile / 'RUN_AUFAKE3D_WINE.sh').read_text()
        self.assertIn('if not defined A3D_HRTF_MODE set "A3D_HRTF_MODE=reference"', win)
        self.assertIn('A3D_HRTF_MODE="${A3D_HRTF_MODE:-reference}"', wine)
        for script in (win, wine):
            active_lines = [line.strip() for line in script.splitlines()
                            if not line.lstrip().lower().startswith(('rem ', '#'))]
            self.assertFalse(any(' +set s_milesdriver' in line for line in active_lines))
            self.assertIn('A3D_MILES_ALIAS_UNKNOWN=0', script)
            self.assertIn('A3D_WAVEOUT_QUEUE_HEADERS=6', script)
            self.assertIn('A3D_WAVEOUT_SUBBLOCKS=1', script)
            self.assertIn('alice-a3d2011-native.exe', script)

    def _make_contents(self):
        contents = {'Universal_Core/a3d.dll': b'MZ SHARED A3D',
                    'Universal_Core/a3dapi.dll': b'MZ SHARED A3DAPI'}
        for profile in self.installer['profiles'].values():
            prefix = 'Game_Kits/' + profile['folder'] + '/COPY_TO_GAME_FOLDER/'
            for relative in profile['files']:
                if Path(relative).name in ('a3d.dll', 'a3dapi.dll'):
                    contents[prefix+relative] = contents['Universal_Core/'+Path(relative).name]
        return contents

    def test_every_game_uses_identical_renderer_bytes(self):
        results = assert_unified_core(self._make_contents(), self.installer)
        self.assertEqual(len(results['game_kit_core_sha256']), len(self.installer['profiles']))
        self.assertEqual(results['architecture'], 'single-shared-win32-engine')
        alice = results['game_kit_core_sha256']['alice2011']
        self.assertEqual(alice['a3d.dll'], results['core_sha256']['a3d.dll'])
        self.assertEqual(alice['SndDrivers/a3dapi.dll'], results['core_sha256']['a3dapi.dll'])

    def test_rejects_alice2011_shadow_engine(self):
        contents = self._make_contents()
        prefix = 'Game_Kits/Alice_2011_VorpalFix/COPY_TO_GAME_FOLDER/'
        for target in ('a3dapi.dll', 'SndDrivers/a3d.dll'):
            with self.subTest(target=target):
                mutated = dict(contents)
                mutated[prefix+target] = b'MZ STALE CUSTOM GAME DLL'
                with self.assertRaisesRegex(RuntimeError, 'renderer fork or stale component'):
                    assert_unified_core(mutated, self.installer)

    def test_rejects_missing_secondary_core(self):
        contents = self._make_contents()
        del contents['Game_Kits/Alice_2011_VorpalFix/COPY_TO_GAME_FOLDER/SndDrivers/a3dapi.dll']
        with self.assertRaisesRegex(RuntimeError, 'missing rendered core'):
            assert_unified_core(contents, self.installer)

    def test_same_hardware_derived_renderer_source_for_all(self):
        engine = (ROOT/'Source/Engine/win32/a3dapi.c').read_text()
        hrtf = (ROOT/'Source/Engine/win32/stream_core.h').read_text()
        self.assertIn('GetEnvironmentVariableA("A3D_HRTF_MODE"', engine)
        self.assertIn('mixer.hrtf_mode', engine)
        self.assertIn('v2_fir_history', hrtf)
        self.assertIn('for(unsigned k=0;k<56u;k++)', hrtf)
        self.assertNotIn('alice2011', hrtf.lower())


if __name__ == '__main__':
    unittest.main()
