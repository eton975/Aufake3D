"""Offline shape/regression tests for experimental Quake III streaming hotfix 2.

These do not claim that Wine's device clock is always reliable or that actual
retail game audio has been tested on Linux.
"""
from pathlib import Path
import unittest
R=Path(__file__).resolve().parents[1]
class StreamHotfix2(unittest.TestCase):
    def test_waveout_grouping_preserves_render_block(self):
        s=(R/'win32/stream_winmm.inc').read_text()
        self.assertIn('for(unsigned sub=0;sub<mix_subblocks;sub++)',s)
        self.assertIn('mix_pcm[i]+sub*A3DMIX_BLOCK*4u,A3DMIX_BLOCK',s)
        self.assertIn('A3D_WAVEOUT_SUBBLOCKS',s)
        self.assertIn('#define MIX_SUBBLOCKS_MAX 4u',s)
        self.assertIn("mix_subblocks=(n==1 && opt[0]=='1')?1u:(n==1 && opt[0]=='4')?4u:2u",s)
        self.assertIn('h->dwBufferLength=A3DMIX_BLOCK*4u*mix_subblocks',s)
        self.assertIn('mix_prepared++;h->dwFlags|=WHDR_DONE;',s)
    def test_device_clock_is_opt_in_and_gracefully_falls_back(self):
        source=(R/'win32/source_probe.inc').read_text()
        backend=(R/'win32/stream_winmm.inc').read_text()
        winmm=(R/'win32/waveout_renderer.inc').read_text()
        self.assertIn('A3D_WAVEOUT_PLAY_CURSOR',backend)
        self.assertIn('waveOutGetPosition',winmm)
        self.assertIn('s->waveout_play_origin=now',backend)
        self.assertIn('if(mixer_use_play_cursor()&&s->waveout_play_valid',source)
        self.assertIn('if(mixer_played_frames(&now))',source)
        self.assertIn('((DWORD)(s->mix.cursor*s->format.block_align)%s->wave_size)',source)
    def test_original_quake3_lock_fix_preserved(self):
        source=(R/'win32/source_probe.inc').read_text()
        self.assertIn('if(!a||!an)return E_POINTER;',source)
        self.assertIn('if(bytes>first && (!b||!bn))return E_POINTER;',source)
        self.assertIn('if(s->play_pcm)s->play_pcm[off]=byte;',source)
    def test_deterministic_configuration_choices(self):
        # 12 prepared output headers x [1,2,4] 256-frame chunks at 48kHz.
        # Separate rendered blocks avoid touching the existing DSP render ABI.
        self.assertEqual([12*256*i for i in (1,2,4)],[3072,6144,12288])
        self.assertEqual([1000*12*256*i/48000 for i in (1,2,4)],[64.,128.,256.])
if __name__=='__main__': unittest.main()
