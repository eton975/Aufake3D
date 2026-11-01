"""Compile the ACTUAL v0.6.4 queue governor with a fake Win32 clock.
This tests recovery, cooldown, floor/ceiling, disabled path; no Wine needed.
"""
from pathlib import Path
import subprocess, tempfile, unittest, shutil
SRC = Path(__file__).resolve().parents[1]/'win32'/'stream_winmm.inc'

def extract_function(text, signature):
    start=text.index(signature)
    open_brace=text.index('{',start)
    depth=0
    for end in range(open_brace,len(text)):
        if text[end]=='{': depth+=1
        if text[end]=='}':
            depth-=1
            if depth==0: return text[start:end+1]
    raise RuntimeError('Unterminated source function')

class AdaptiveNative(unittest.TestCase):
    def test_governor_under_real_C_compiler(self):
        gcc=shutil.which('cc')
        if not gcc: self.skipTest('No host C compiler')
        body=extract_function(SRC.read_text(),'static void mix_update_adaptive(unsigned queued,int just_underran)')
        c='''#include <assert.h>
#include <stdio.h>
typedef unsigned long DWORD;
static int mix_adaptive=0;
static unsigned mix_target_headers=8u,mix_min_headers=6u,mix_queue_limit=8u;
static DWORD mix_last_adjust_ms=0,mix_last_underrun_ms=0;
static DWORD mix_adjust_down=0,mix_adjust_up=0;
static DWORD tick=0;
static DWORD test_tick(void){return tick;}
static DWORD (*mix_tick)(void)=test_tick;
''' +body+'''
int main(void){
  mix_update_adaptive(8,0); assert(mix_target_headers==8); /* opt-in */
  mix_adaptive=1;tick=11000;mix_update_adaptive(8,0);assert(mix_target_headers==8);
  tick=20001;mix_update_adaptive(8,0);assert(mix_target_headers==7);
  tick=35001;mix_update_adaptive(7,0);assert(mix_target_headers==6);
  tick=48000;mix_update_adaptive(6,0);assert(mix_target_headers==6); /* floor */
  tick=48001;mix_update_adaptive(0,1);assert(mix_target_headers==8); /* recover by two */
  tick=59000;mix_update_adaptive(8,0);assert(mix_target_headers==8);
  tick=68002;mix_update_adaptive(8,0);assert(mix_target_headers==7);
  assert(mix_adjust_up==1 && mix_adjust_down==3);
  puts("A3D v0.6.4 C governor: PASS");return 0;
}
'''
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'governor.c'; exe=Path(d)/'governor'
            source.write_text(c)
            subprocess.run([gcc,'-std=c11','-O2','-Wall','-Wextra','-Werror',str(source),'-o',str(exe)],check=True,capture_output=True)
            r=subprocess.run([str(exe)],check=True,capture_output=True,text=True)
            self.assertIn('PASS',r.stdout)
    def test_trace_source(self):
        s=SRC.read_text();l=(SRC.parent/'listener_trace.inc').read_text()
        for marker in ('A3D.Latency.listener_orientation6_updates','A3D.Latency.listener_euler_updates','A3D.Latency.ahead_avg_frames', 'A3D.Latency.adaptive_recoveries', 'A3D_WAVEOUT_ADAPTIVE'):
            self.assertIn(marker,s)
        self.assertIn('InterlockedIncrement(&listener_euler_updates)',l)
        self.assertIn('mixer_update_listener();',l)

if __name__=='__main__':unittest.main()
