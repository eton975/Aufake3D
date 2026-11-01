# v0.5.0 SOURCE COMMENTARY — Regression test / harness
# Exercises the release implementation or checks its ABI/packaging contract. Do not
# treat fixture success as proof of native Wine or retail-game compatibility.
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class SpatialContractTests(unittest.TestCase):
    def test_real_audio_renderer_uses_tested_helper(self):
        content=(ROOT/'win32/waveout_renderer.inc').read_text()
        self.assertIn('#include "spatial_stereo.h"',content)
        self.assertIn('a3d_stereo_gains(src,lis,forward,up,coords,source_gain)', (ROOT/'win32/binaural_approx.h').read_text())
        self.assertIn('#include "stream_winmm.inc"',content)
        stream=(ROOT/'win32/stream_core.h').read_text()
        self.assertIn('a3d_measured_pick(spos,lpos,front,up,m->coords,amplitude,A3DMIX_RATE)',stream)
        self.assertIn('a3dmix_distance_gain(m,v,dist)',stream)
        self.assertIn('a3dmix_doppler(m,v,spos,lpos)',stream)
        self.assertIn('a3d_measured_pick(',stream)
        self.assertNotIn('listener.ori[4]*listener.ori[2]',content)
    def test_listener_default_matches_rh(self):
        self.assertIn('{0,0,-1,0,1,0}', (ROOT/'win32/listener_trace.inc').read_text())
    def test_coordinate_setting_is_honoured(self):
        c=(ROOT/'win32/a3dapi.c').read_text()
        self.assertIn('IA3d4.SetCoordinateSystem LEFT_HANDED',c)
        self.assertIn('IA3d4.SetCoordinateSystem RIGHT_HANDED',c)
if __name__=='__main__':unittest.main()
