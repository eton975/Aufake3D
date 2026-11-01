"""Hotfix 5 contracts; native C test validates voice-pool behaviour."""
from pathlib import Path
import re
import unittest
ROOT=Path(__file__).resolve().parents[1]
class Voice128Hotfix5(unittest.TestCase):
 def test_voice_capacity_and_configurable_limit(self):
  core=(ROOT/'win32/stream_core.h').read_text()
  audio=(ROOT/'win32/stream_winmm.inc').read_text()
  self.assertRegex(core,r'#define\s+A3DMIX_VOICES\s+128u')
  self.assertIn('voice_limit,voice_peak,voice_rejections,voice_additions',core)
  self.assertIn('m->voice_limit=A3DMIX_VOICES',core)
  self.assertIn('A3D_VOICE_LIMIT',audio)
  self.assertIn('A3D.Mixer.voice_rejections',audio)
  self.assertIn('A3D.Mixer.voice_peak',audio)
 def test_stop_and_play_logging_are_opt_in(self):
  audio=(ROOT/'win32/stream_winmm.inc').read_text()
  src=(ROOT/'win32/source_probe.inc').read_text()
  self.assertIn('if(trace_detail())logline("IA3dSource.Stop");',src)
  self.assertIn('InterlockedIncrement(&sr_stop_calls)',src)
  self.assertIn('if(trace_detail()){\n  sr_logu("IA3dSource.Play source_id"',audio)
  self.assertIn('if(trace_detail())logline("A3D.Mixer rejected source:',audio)
 def test_compatibility_lock_fix_retained(self):
  src=(ROOT/'win32/source_probe.inc').read_text()
  self.assertIn('if(!a||!an)return E_POINTER;',src)
  self.assertIn('if(bytes>first && (!b||!bn))return E_POINTER;',src)
if __name__=='__main__':unittest.main()
