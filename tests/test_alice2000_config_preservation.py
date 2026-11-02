"""Regression guard: the Alice 2000 launcher must not reset game video options."""
from pathlib import Path
import json
import re
import re
import unittest
ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / 'packaging/Game_Kits/Alice_2000/COPY_TO_GAME_FOLDER'

class Alice2000Configuration(unittest.TestCase):
    def test_no_startup_video_overrides_or_backup_restore(self):
        launch = (KIT / 'RUN_AUFAKE3D_WINDOWS.cmd').read_text()
        self.assertNotIn('+set r_mode', launch.lower())
        self.assertIsNone(re.search(r'(?im)^(?!\s*rem\b)[^\r\n]*\+set\s+s_milesdriver', launch))
        self.assertNotIn('config.cfg.AUFAKE3D_before_A3D2_default.bak', launch)
        self.assertIn('AUFAKE3D_A3D2_INITIAL_DEFAULT_DONE.txt', launch)
        self.assertIn('AUFAKE3D_DEFER_A3D2_SEED', launch)
        self.assertIn('if exist "base\\config.cfg"', launch)
        self.assertIn('AUFAKE3D_GAME_EXIT_STATUS', launch)
        self.assertIn(' -OnlyIfAuto', launch)
        self.assertIn('A3D_WAVEOUT_QUEUE_HEADERS=6', launch)
        self.assertIn('A3D_WAVEOUT_SUBBLOCKS=1', launch)

    def test_seed_never_creates_skeletal_config(self):
        seed = (KIT / 'AUFAKE3D_SET_INITIAL_A3D2.ps1').read_text()
        self.assertIn("$Game -eq 'Alice2000' -and -not [IO.File]::Exists($target)", seed)
        self.assertIn('initial A3D2 preference deferred', seed)
        self.assertIn('No marker is placed', seed)
        self.assertIn('preserved the game-selected sound provider', seed)
        self.assertIn("$choice -ine 'auto'", seed)
        self.assertIn('Safety check rejected config edit', seed)
        self.assertIn('AUFAKE3D_before_A3D2_default.bak', seed)

    def test_display_recovery_is_opt_in_and_does_not_restore_sound(self):
        launch = (KIT / 'RUN_AUFAKE3D_WINDOWS.cmd').read_text()
        recovery = (KIT / 'AUFAKE3D_RESTORE_DISPLAY_SETTINGS.ps1').read_text()
        self.assertNotIn('AUFAKE3D_RESTORE_DISPLAY_SETTINGS.ps1', launch)
        self.assertIn("(?:r|vid|gl)_", recovery)
        self.assertNotIn("$restore['s_milesdriver']", recovery)
        self.assertIn('AUFAKE3D_before_display_repair_', recovery)
        manifest = json.loads((ROOT/'packaging/Game_Kits/INSTALL_MAP.json').read_text())
        self.assertIn('AUFAKE3D_RESTORE_DISPLAY_SETTINGS.ps1', manifest['profiles']['alice2000']['files'])

if __name__ == '__main__': unittest.main()
