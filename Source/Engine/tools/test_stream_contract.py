# v0.5.0 SOURCE COMMENTARY — Regression test / harness
# Exercises the release implementation or checks its ABI/packaging contract. Do not
# treat fixture success as proof of native Wine or retail-game compatibility.
"""New cross-API safety and structure assertions for shared streaming WinMM."""
from pathlib import Path
import unittest
P=Path(__file__).resolve().parents[1]
class StreamContract(unittest.TestCase):
 def test_single_waveout_device_and_backend(self):
  s=(P/'win32/stream_winmm.inc').read_text()
  self.assertEqual(s.count('wopen(&mix_waveout'),2)
  self.assertIn('if(e&&mix_event_mode)',s)
  self.assertIn('CloseHandle(mix_wave_event)',s)
  self.assertIn('CreateThread',s)
  self.assertIn('WaitForSingleObject',s)
  self.assertIn('mixer_shutdown',s)
  self.assertIn('mixer_start',s)
  self.assertIn('A3DMIX_BLOCK',s)
  self.assertIn('#define MIX_BUFFERS 12u',s)
  self.assertIn('A3D_WAVEOUT_SUBBLOCKS',s)
  self.assertIn('h->dwBufferLength=A3DMIX_BLOCK*4u*mix_subblocks',s)
  self.assertIn('mix_pcm[i]+sub*A3DMIX_BLOCK*4u',s)
 def test_thread_race_protection(self):
  s=(P/'win32/source_probe.inc').read_text()
  t=(P/'win32/stream_winmm.inc').read_text()
  self.assertIn('unsigned char *play_pcm',s)
  self.assertIn('if(s->play_pcm)s->play_pcm[off]=byte',s)
  self.assertIn('s->locked=0;s->lock_at=0;s->lock_bytes=0',s)
  self.assertIn('v->pcm=s->play_pcm',t)
  self.assertIn('sr_copy(s->play_pcm,s->pcm,s->wave_size)',t)
  self.assertIn('a3dmix_remove(&mixer,&s->mix)',t)
  self.assertIn('EnterCriticalSection',t)
 def test_realtime_logging_optimized(self):
  src=(P/'win32/source_probe.inc').read_text()
  lis=(P/'win32/listener_trace.inc').read_text()
  api=(P/'win32/a3dapi.c').read_text()
  self.assertIn('A3D_TRACE_DETAIL',api)
  self.assertIn('if(trace_detail())',src)
  self.assertIn('if(trace_detail())',lis)
 def test_geometry_list_abi(self):
  s=(P/'win32/geometry_lists.inc').read_text()
  self.assertIn('list_begin,(void*)list_end,(void*)list_call,(void*)list_bounds',s)
  self.assertIn('x->finished',s)
  self.assertIn('a3d_scene.record_target=0',s)
  self.assertIn('x->frame->count>A3D_SCENE_MAX_TRI',s)
 def test_material_abi(self):
  s=(P/'win32/geom_trace.inc').read_text()
  self.assertIn('mqi,madd,mrel,mload,msave,munserialize',s)
  self.assertIn('mserialize,mduplicate,msetname',s)
  self.assertIn('iid_material',s)
if __name__=='__main__':unittest.main()
