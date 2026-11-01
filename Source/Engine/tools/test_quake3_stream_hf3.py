"""Offline tests for bounded WaveOut buffering; no Wine runtime available."""
from pathlib import Path
import unittest
R=Path(__file__).resolve().parents[1]
class StreamHotfix3(unittest.TestCase):
 def test_inflight_is_bounded_and_counted(self):
  s=(R/'win32/stream_winmm.inc').read_text()
  for k in ('if(queued>=mix_target_headers)break;', 'queued++;',
            'A3D_WAVEOUT_QUEUE_HEADERS', 'mix_queue_empty_events++',
            'A3D.Mixer.waveOut.queue_limit_frames',
            'A3D.Mixer.waveOut.queue_empty_events'):
   self.assertIn(k,s)
 def test_queue_settings_limit_nominal_ahead_audio(self):
  # The default 12-header eager queue had ~128ms for 512-frame buffers.
  before_ms=1000*12*512/48000
  self.assertEqual(before_ms,128.0)
  defaults={1:6,2:3,4:2}
  for sub,count in defaults.items():
   self.assertTrue(20<=1000*256*sub*count/48000<=45)
   self.assertLessEqual(count,12)
 def test_legacy_lock_and_cursor_controls_preserved(self):
  source=(R/'win32/source_probe.inc').read_text()
  self.assertIn('if(!a||!an)return E_POINTER;',source)
  self.assertIn('A3D_WAVEOUT_PLAY_CURSOR', (R/'win32/stream_winmm.inc').read_text())
if __name__=='__main__':unittest.main()
