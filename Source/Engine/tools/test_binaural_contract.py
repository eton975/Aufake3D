# v0.5.0 SOURCE COMMENTARY — Regression test / harness
# Exercises the release implementation or checks its ABI/packaging contract. Do not
# treat fixture success as proof of native Wine or retail-game compatibility.
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class BinauralContract(unittest.TestCase):
 def test_binaural_dsp_enabled(self):
  renderer=(ROOT/'win32/waveout_renderer.inc').read_text()
  self.assertIn('#include "binaural_approx.h"',renderer)
  self.assertIn('#include "stream_winmm.inc"',renderer)
  stream=(ROOT/'win32/stream_core.h').read_text()
  self.assertIn('a3d_measured_pick(',stream)
  self.assertIn('a3d_mhrir_48000',stream)
  self.assertIn('A3DMIX_HISTORY',stream)
 def test_spatial_cues(self):
  h=(ROOT/'win32/binaural_approx.h').read_text()
  self.assertIn('0.00065f',h)
  self.assertIn('c.delay_l=g.pan>0.0f?',h)
  self.assertIn('c.delay_r=g.pan<0.0f?',h)
  self.assertIn('rear_filtered',h)
  self.assertIn('elevation',h)
 def test_documented_prototype_limitation(self):
  self.assertIn('NOT Aureal', (ROOT/'win32/binaural_approx.h').read_text())
if __name__=='__main__': unittest.main()
