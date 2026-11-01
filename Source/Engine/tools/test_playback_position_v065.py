"""Native C test of the actual 0.6.5 waveOut play-head conversion/validation."""
from pathlib import Path
import shutil, subprocess, tempfile, unittest
from test_latency_governor_v065 import extract, STREAM

class PlaybackCursor(unittest.TestCase):
    def test_real_source(self):
        if not shutil.which('cc'): self.skipTest('No native compiler')
        body=extract(STREAM.read_text(),'static int mix_sample_playback_position(DWORD *ahead_out)')
        src='''#include <stdint.h>
#include <assert.h>
#include <stdio.h>
typedef uint32_t DWORD;
typedef void *HANDLE;
typedef struct {DWORD type,value,reserved;} WaveTime;
#define A3DMIX_BLOCK 256u
#define A3DMIX_RATE 48000u
#define MIX_BUFFERS 12u
#define MIX_SUBBLOCKS_MAX 4u
static int mix_latency_trace=1;
static DWORD mix_pos_unsupported=0,mix_pos_samples=0,mix_playback_ahead_max_frames=0;
static DWORD mix_playback_ahead_min_frames=0xffffffffu;
static unsigned long long mix_playback_ahead_total_frames=0;
static unsigned mix_subblocks=1;
static DWORD mix_headers_submitted=30;
static HANDLE mix_waveout=(HANDLE)1;
static WaveTime fake={2u,0,0};
static DWORD error=0;
static DWORD fake_pos(HANDLE h,WaveTime *t,DWORD cb){(void)h;(void)cb;if(error)return error;*t=fake;return 0;}
static DWORD (*wposition)(HANDLE,WaveTime*,DWORD)=fake_pos;
''' + body + '''
int main(void){
 DWORD ahead=0;
 fake.type=2;fake.value=7580;assert(mix_sample_playback_position(&ahead) && ahead==100);
 fake.type=4;fake.value=7580*4;assert(mix_sample_playback_position(&ahead) && ahead==100);
 fake.type=1;fake.value=150;assert(mix_sample_playback_position(&ahead) && ahead==480);
 fake.type=12;assert(!mix_sample_playback_position(&ahead));
 fake.type=2;fake.value=1000000;assert(!mix_sample_playback_position(&ahead));
 error=1;assert(!mix_sample_playback_position(&ahead));error=0;
 assert(mix_pos_samples==3 && mix_pos_unsupported==3);
 mix_latency_trace=0;
 fake.type=2;fake.value=7600;assert(mix_sample_playback_position(&ahead)&&ahead==80);
 assert(mix_pos_samples==3);
 assert(mix_playback_ahead_total_frames==680);
 puts("PASS v0.6.5 actual playback-position conversions, bounds and fallback");return 0;
}
'''
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'test.c';exe=Path(d)/'test';path.write_text(src)
            subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror',str(path),'-o',str(exe)],check=True,capture_output=True)
            res=subprocess.run([str(exe)],check=True,capture_output=True,text=True)
            self.assertIn('PASS',res.stdout)

if __name__=='__main__':unittest.main()
