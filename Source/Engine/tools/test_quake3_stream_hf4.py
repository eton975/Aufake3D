"""Hotfix 4 structural and numeric regressions (not a substitute for Wine)."""
from pathlib import Path
import unittest
R=Path(__file__).resolve().parents[1]
class Quake3Hotfix4(unittest.TestCase):
 def test_event_open_fallback_is_safe_and_optional(self):
  s=(R/'win32/stream_winmm.inc').read_text()
  self.assertIn('A3D_CALLBACK_EVENT 0x00050000UL',s)
  self.assertIn('CreateEventA(0,0,0,0)',s)
  self.assertIn('if(e&&mix_event_mode)',s)
  self.assertIn('if(mix_wave_event)SetEvent(mix_wave_event);',s)
  self.assertIn('if(mix_wave_event){CloseHandle(mix_wave_event);mix_wave_event=0;}',s)
  self.assertIn('A3D_WAVEOUT_EVENT',s)
  self.assertIn('A3D_WAVEOUT_PRIORITY',s)
 def test_qpc_dma_clock_opt_in_and_cursor_bounded(self):
  s=(R/'win32/source_probe.inc').read_text()
  t=(R/'win32/stream_winmm.inc').read_text()
  self.assertIn('A3D_Q3_DMA_CLOCK',t)
  self.assertIn('s->dma_clock_valid=1;',t)
  self.assertIn('if(s->dma_clock_valid&&s->wave_size&&mix_qpc&&mix_qpc_freq>0)',s)
  self.assertIn('*p=(advanced+s->dma_clock_base)%s->wave_size;',s)
  self.assertIn('((DWORD)(s->mix.cursor*s->format.block_align)%s->wave_size)',s)
  self.assertIn('mixer_use_play_cursor()',s)
 def test_mixer_instruments_realtime_cost_without_logging_in_hot_loop(self):
  s=(R/'win32/stream_winmm.inc').read_text()
  self.assertIn('QueryPerformanceFrequency',s)
  self.assertIn('A3D.Mixer.DSP.max_block_us',s)
  self.assertIn('A3D.Mixer.DSP.blocks_over_5333us',s)
  self.assertIn('A3D.Mixer.waveOut.event_wakes',s)
  self.assertIn('A3D.Mixer.waveOut.queue_empty_events',s)
  start=s.index('static DWORD WINAPI mixer_thread_run(')
  end=s.index('static int mixer_start(',start)
  self.assertNotIn('A3D.Mixer.DSP.max_block_us',s[start:end]) # no per-block logging
 def test_quake3_117_disassembly_shape(self):
  # Grounded in the user's original quake3.exe: A3D GetWavePosition (vtable
  # +0x4c) is converted to mono sample units then ring-masked at 0x447d17.
  exe=Path('/mnt/data/files/quake3(2).exe')
  if exe.exists():
   b=exe.read_bytes()
   self.assertIn(bytes.fromhex('ff 51 4c'),b)
   self.assertIn(bytes.fromhex('d3 f8 4a 23 c2'),b)
 def test_byte_ring_cursor_model(self):
  ring=32768
  align=4
  for frames in [0,1,200,8191,8192,8193,100000]:
   self.assertEqual((frames*align)%ring,(frames%(ring//align))*align)
   self.assertLess((frames*align)%ring,ring)
if __name__=='__main__':unittest.main()
