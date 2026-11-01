import unittest,tempfile,subprocess,re,os
from pathlib import Path
SRC=(Path(__file__).resolve().parents[1]/'Source/Engine/win32/stream_core.h').read_text()
WINMM=(Path(__file__).resolve().parents[1]/'Source/Engine/win32/stream_winmm.inc').read_text()
class AudioEdge(unittest.TestCase):
 def test_real_c_envelope_cases(self):
  a=SRC.index('static float a3dmix_short_sfx_envelope(')
  b=SRC.index('/* REVIEW NOTE — a3dmix_next:',a)
  frag=SRC[a:b]
  # Compile the verbatim production function with a small C stand-in.
  code=r'''
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#define A3DMIX_RATE 48000u
typedef struct {unsigned short_sfx_declick;} A3DMix;
typedef struct {unsigned looping,rate,channels,bits,bytes;unsigned long played_frames;double cursor;float pitch,doppler_factor;} A3DMixVoice;
/*FN*/
static void need(int condition,const char*why){if(!condition){fprintf(stderr,"FAILED %s\n",why);exit(1);}}
int main(void){
 A3DMix m={1};A3DMixVoice v={0};v.channels=1;v.bits=16;v.rate=48000;v.bytes=4800*2;v.pitch=1;v.doppler_factor=1;
 v.played_frames=1;v.cursor=1;float a=a3dmix_short_sfx_envelope(&m,&v);
 v.played_frames=32;v.cursor=32;float b=a3dmix_short_sfx_envelope(&m,&v);
 v.cursor=4799;float c=a3dmix_short_sfx_envelope(&m,&v);
 need(a>0&&a<0.05f,"soft onset");need(b>0.99f,"full volume after 32 frames");need(c>0&&c<0.05f,"soft ending");
 v.bytes=48000*2;v.played_frames=1;v.cursor=1;need(a3dmix_short_sfx_envelope(&m,&v)==1.0f,"one-second dialogue untouched");
 v.bytes=4800*2;v.looping=1;need(a3dmix_short_sfx_envelope(&m,&v)==1.0f,"loop audio untouched");
 v.looping=0;m.short_sfx_declick=0;need(a3dmix_short_sfx_envelope(&m,&v)==1.0f,"opt-out disables fade");
 v.channels=0;m.short_sfx_declick=1;need(a3dmix_short_sfx_envelope(&m,&v)==1.0f,"invalid PCM untouched");
 puts("7/7 audio edge envelope checks passed");return 0;
}
'''.replace('/*FN*/',frag)
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'a.c';exe=Path(d)/'a';f.write_text(code)
   c=subprocess.run(['clang','-std=c99','-O2','-Wall','-Wextra','-Werror',str(f),'-o',str(exe)],capture_output=True,text=True)
   self.assertEqual(c.returncode,0,c.stderr)
   r=subprocess.run([str(exe)],capture_output=True,text=True)
   self.assertEqual(r.returncode,0,r.stderr)
   self.assertIn('7/7',r.stdout)
 def test_declick_only_on_raw_voice_sample(self):
  self.assertIn('x*=a3dmix_short_sfx_envelope(m,v);',SRC)
  self.assertIn('v->h[v->hist_cursor]=x;',SRC)
  self.assertIn('m->short_sfx_declick=1u',SRC)
  self.assertIn('A3D_SHORT_SFX_DECLICK',WINMM)
  self.assertIn('d->short_sfx_declick=a->short_sfx_declick;',WINMM)
 def test_compatibility_pump_not_lost(self):
  self.assertIn('mix_position_probe=1;',WINMM)
  self.assertIn('mix_position_interval=4u;',WINMM)
  self.assertIn('int valid=mix_sample_playback_position(&ahead);',WINMM)
  self.assertIn('mix_position_consecutive_errors=0;',WINMM)
  self.assertIn('A3D_WAVEOUT_POSITION_PROBE',WINMM)
  self.assertIn('if(mix_adaptive)',WINMM)
 def test_critical_audio_invariants(self):
  self.assertIn('static unsigned mix_subblocks=2u;',WINMM)
  self.assertIn('static unsigned mix_queue_limit=3u;',WINMM)
  self.assertIn('m->master_boost=5.0f;',SRC)
  self.assertIn('a3dmix_render(&mixer,mix_pcm[i]+sub*A3DMIX_BLOCK*4u,A3DMIX_BLOCK);',WINMM)
if __name__=='__main__': unittest.main()
