# v0.5.0 SOURCE COMMENTARY — Regression test / harness
# Exercises the release implementation or checks its ABI/packaging contract. Do not
# treat fixture success as proof of native Wine or retail-game compatibility.
"""Contract test for independent IA3dSource COM object."""
from pathlib import Path
import re,unittest
R=Path(__file__).resolve().parents[1]
class SourceContract(unittest.TestCase):
 def test_abi_order(self):
  s=(R/'win32/source_probe.inc').read_text()
  items=re.findall(r'\(void\*\)(sr_\w+) /\* (\d+) (\w+) \*/',s)
  self.assertEqual(len(items),67)
  self.assertEqual([int(i) for _,i,_ in items],list(range(67)))
  for index,name in {0:'QueryInterface',3:'LoadWaveFile',11:'Lock',13:'Play',20:'SetPosition3f',21:'GetPosition3f',38:'SetMinMaxDistance',40:'SetGain',54:'GetAudibility',66:'GetReflectionGainScale'}.items():
   self.assertEqual(items[index][2],name)
 def test_waveout_playback_is_explicit_and_fails_on_backend_error(self):
  s=(R/'win32/source_probe.inc').read_text()
  self.assertIn('return sr_audio_play(s,repeat);',s)
  a=(R/'win32/waveout_renderer.inc').read_text()
  self.assertIn('waveOutOpen',a)
  b=(R/'win32/stream_winmm.inc').read_text()
  self.assertIn('if(!load_winmm())return 0;',b)
  self.assertIn('if(!mixer_start()){mix_leave();return E_FAIL;}',b)
  self.assertIn('wwrite(mix_waveout,h',b)
 def test_miles_probe_no_pcm_calls(self):
  m=(R/'win32/miles_open.c').read_text()
  self.assertIn('_AIL_allocate_3D_sample_handle@4',m)
  self.assertIn('_AIL_release_3D_sample_handle@4',m)
  self.assertNotIn('_AIL_set_3D_sample_file@',m)
if __name__=='__main__':unittest.main()
