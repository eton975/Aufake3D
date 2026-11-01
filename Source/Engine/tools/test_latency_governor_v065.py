"""Compile and exercise the REAL v0.6.5 adaptive governor under native C.
Offline test of header target, conservative throttling, and early recovery;
not an audio-device timing or game-compatibility test.
"""
import shutil, subprocess, tempfile, unittest
from pathlib import Path
STREAM = Path(__file__).resolve().parents[1] / 'win32' / 'stream_winmm.inc'

def extract(source, signature):
    i=source.index(signature); op=source.index('{',i); depth=0
    for n in range(op,len(source)):
        if source[n]=='{': depth+=1
        elif source[n]=='}':
            depth-=1
            if depth==0: return source[i:n+1]
    raise RuntimeError(signature)

class Governor(unittest.TestCase):
    def test_real_c_controller(self):
        if not shutil.which('cc'): self.skipTest('native C compiler unavailable')
        source = STREAM.read_text()
        controller=extract(source,'static void mix_update_adaptive(unsigned queued,int just_underran)')
        monitor=extract(source,'static void mix_watch_headroom(unsigned queued,int valid,DWORD ahead)')
        code='''#include <assert.h>
#include <stdio.h>
#include <stdint.h>
typedef uint32_t DWORD;
#define A3DMIX_BLOCK 256u
static unsigned mix_subblocks=1u, mix_queue_limit=8u;
static unsigned mix_target_headers=4u, mix_min_headers=3u, mix_start_headers=4u;
static int mix_adaptive=1;
static DWORD mix_last_adjust_ms=0,mix_last_underrun_ms=0,mix_last_early_recovery_ms=0;
static DWORD mix_adjust_down=0,mix_adjust_up=0,mix_early_recoveries=0,mix_low_headroom_samples=0;
static unsigned mix_low_headroom_streak=0;
static DWORD mix_headers_submitted=30;
static DWORD tick=0;
static DWORD gettick(void){return tick;}
static DWORD (*mix_tick)(void)=gettick;
''' + controller + '\n' + monitor + '''
int main(void){
  // four 256-frame headers, with three minimum and eight ceiling
  assert(mix_subblocks==1 && mix_target_headers==4);
  tick=12001;mix_update_adaptive(3,0);assert(mix_target_headers==4);
  tick=20001;mix_update_adaptive(3,0);assert(mix_target_headers==3);
  tick=55000;mix_update_adaptive(3,0);assert(mix_target_headers==3);
  // one suspicious playback cursor reading cannot change the queue
  mix_watch_headroom(1,1,90);assert(mix_target_headers==3);
  // invalid reading resets consecutive count
  mix_watch_headroom(1,0,0);assert(mix_target_headers==3);
  tick=56000;mix_watch_headroom(1,1,80);mix_watch_headroom(1,1,70);
  assert(mix_target_headers==4 && mix_early_recoveries==1);
  // warning cooldown avoids rapid oscillation
  tick=56001;mix_watch_headroom(1,1,50);mix_watch_headroom(1,1,40);
  assert(mix_target_headers==4);
  // no reductions while within 20s of low-headroom warning
  tick=70000;mix_update_adaptive(4,0);assert(mix_target_headers==4);
  tick=77000;mix_update_adaptive(4,0);assert(mix_target_headers==3);
  // actual queue starvation immediately recovers by two
  tick=80000;mix_update_adaptive(0,1);assert(mix_target_headers==5);
  tick=81000;mix_update_adaptive(0,1);assert(mix_target_headers==7);
  tick=82000;mix_update_adaptive(0,1);assert(mix_target_headers==8);
  tick=83000;mix_update_adaptive(0,1);assert(mix_target_headers==8);
  mix_adaptive=0;tick=100000;mix_update_adaptive(0,1);
  mix_watch_headroom(1,1,0);assert(mix_target_headers==8);
  assert(mix_low_headroom_samples>0 && mix_adjust_up>=4);
  assert(mix_adjust_down>0);
  puts("PASS v0.6.5 low-latency queue governor + early warning C test");return 0;
}
'''
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/'test.c'; exe=Path(d)/'test';src.write_text(code)
            subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror',str(src),'-o',str(exe)],check=True)
            out=subprocess.check_output([str(exe)],text=True)
            self.assertIn('PASS',out)
    def test_contract(self):
        s=STREAM.read_text()
        for term in ['A3D_WAVEOUT_START_HEADERS','A3D.Latency.early_headroom_recoveries','mix_watch_headroom','A3D_WAVEOUT_MIN_HEADERS','A3D_WAVEOUT_QUEUE_HEADERS']:
            self.assertIn(term,s)

if __name__ == '__main__': unittest.main()
