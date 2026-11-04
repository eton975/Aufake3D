"""Opt-in generic 2-channel pan must not change existing release defaults."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]/'Source/Engine/win32'

class SourcePan(unittest.TestCase):
 def test_gated_and_abi_indices_retained(self):
  s=(ROOT/'source_probe.inc').read_text()
  self.assertIn('A3D_ENABLE_PAN_VALUES',s)
  self.assertIn('if(!sr_pan_feature())return E_NOTIMPL',s)
  self.assertIn('sr_setpan /* 57 SetPanValues */',s)
  self.assertIn('sr_getpan /* 58 GetPanValues */',s)
  self.assertIn('if(n!=1u && n!=2u)return E_INVALIDARG',s)
 def test_source_voice_copy_on_play_and_live_updates(self):
  s=(ROOT/'stream_winmm.inc').read_text()
  self.assertGreaterEqual(s.count('s->mix.pan_set=s->pan_set'),1)
  self.assertIn('v->pan_set=s->pan_set;',s)
  self.assertIn('v->pan_values[0]=s->pan_values[0]',s)
 def test_audio_path_only_changes_if_set(self):
  s=(ROOT/'stream_core.h').read_text()
  self.assertIn('if(v->pan_set){l*=v->pan_values[0];r*=v->pan_values[1];}',s)

if __name__=='__main__':unittest.main()
