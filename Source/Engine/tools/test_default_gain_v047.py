# v0.5.0 SOURCE COMMENTARY — Regression test / harness
# Exercises the release implementation or checks its ABI/packaging contract. Do not
# treat fixture success as proof of native Wine or retail-game compatibility.
"""v0.4.7 default master gain contract. Static check; no Windows needed."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
class DefaultGain(unittest.TestCase):
    def test_core_default(self):
        src=(ROOT/'win32/stream_core.h').read_text()
        self.assertIn('m->master_boost=5.0f;', src)
        self.assertNotIn('m->master_boost=1.5f;', src)
    def test_both_runtime_paths(self):
        for rel in ('win32/stream_winmm.inc','win32/a3dapi.c'):
            src=(ROOT/rel).read_text()
            line='a3d_tuning_env("A3D_MASTER_GAIN",5.0f,0.1f,5.0f)'
            self.assertEqual(src.count(line),1,rel)
            self.assertNotIn('a3d_tuning_env("A3D_MASTER_GAIN",1.5f',src)
    def test_gain_diagnostic_preserved(self):
        self.assertIn('A3D.MasterGain.start.x1000',(ROOT/'win32/stream_winmm.inc').read_text())
        self.assertIn('A3D.MasterGain.Init.x1000',(ROOT/'win32/a3dapi.c').read_text())
if __name__=='__main__':unittest.main()
