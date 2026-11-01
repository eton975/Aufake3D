"""Focused regression checks for promoted Quake III 6x256 Windows/Wine defaults."""
from pathlib import Path
import json,unittest
R=Path(__file__).resolve().parents[1]
D=R/'deploy-v0610'/'QuakeIII-117'
P=json.loads((R/'config/game_profiles_v069.json').read_text())
class QuakePromotedDefault(unittest.TestCase):
 def test_win32_default_matches_successful_32ms_legacy_test(self):
  q=P['QuakeIII-117']
  self.assertEqual((q['queue_headers'],q['subblocks'],q['render_snapshot'],q['thread_priority']),(6,1,1,0))
  default=(D/'RUN_A3D_WINDOWS.cmd').read_text()
  successful=(D/'RUN_A3D_32MS_TEST_WINDOWS.cmd').read_text()
  for token in ('A3D_WAVEOUT_QUEUE_HEADERS=6','A3D_WAVEOUT_SUBBLOCKS=1','A3D_WAVEOUT_ADAPTIVE=0'):
   self.assertIn(token,default)
  for token in ('A3D_WAVEOUT_QUEUE_HEADERS=6','A3D_WAVEOUT_SUBBLOCKS=1'):
   self.assertIn(token,successful)
  self.assertIn('+set s_enable_a3d 1 +set s_mixahead 0.35 +set s_mixPreStep 0.05',default)
  self.assertIn('A3D_LOG=0',default)
 def test_fallback_provided_on_both_os(self):
  fallback=(D/'RUN_A3D_3x512_FALLBACK_WINDOWS.cmd').read_text()
  wine=(D/'RUN_A3D_3x512_FALLBACK_WINE.sh').read_text()
  for token in ('A3D_WAVEOUT_SUBBLOCKS=2','A3D_WAVEOUT_QUEUE_HEADERS=3','A3D_WAVEOUT_ADAPTIVE=0'):
   self.assertIn(token,fallback)
   self.assertIn(token,wine)
  self.assertIn('A3D_WAVEOUT_SUBBLOCKS', (D/'RUN_A3D_WINE.sh').read_text())
if __name__=='__main__':unittest.main()
