"""Compile and exercise the production Stop function with mocked host mutex."""
import pathlib
import shutil
import subprocess
import tempfile
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
SRC=ROOT/'win32/stream_winmm.inc'
class IdleStopHF6(unittest.TestCase):
    def test_actual_function_skips_global_lock(self):
        src=SRC.read_text()
        start=src.index('static void sr_audio_stop(Source*s){')
        opening=src.index('{',start)
        depth=0
        end=None
        for i in range(opening,len(src)):
            depth+=(src[i]=='{')-(src[i]=='}')
            if depth==0:
                end=i+1
                break
        self.assertIsNotNone(end)
        func=src[start:end]
        cc=shutil.which('cc') or shutil.which('gcc')
        if not cc:self.skipTest('No host compiler')
        mock='''#include <stdio.h>
        typedef struct {int active;} MockVoice;
        typedef struct {volatile long in_mixer; MockVoice mix;} Source;
        static volatile long sr_stop_noop_calls=0;
        static volatile long sr_stop_active_calls=0;
        static volatile long sr_stop_inactive_registered_calls=0;
        static int locks=0, removals=0, mixer=0;
        static void mix_enter(void){locks++;}
        static void mix_leave(void){}
        static void a3dmix_remove(int*m,MockVoice*v){(void)m;(void)v;removals++;}
        static long InterlockedIncrement(volatile long *p){return ++*p;}
        static long InterlockedExchange(volatile long *p,long n){long o=*p;*p=n;return o;}
        '''
        checks='''int main(void){
          Source s={0};
          for(int i=0;i<100000;i++)sr_audio_stop(&s);
          if(locks!=0||sr_stop_noop_calls!=100000||removals!=0)return 1;
          s.in_mixer=1;s.mix.active=1;sr_audio_stop(&s);
          if(locks!=1||sr_stop_active_calls!=1||s.in_mixer!=0||removals!=1)return 2;
          for(int i=0;i<1000;i++)sr_audio_stop(&s);
          if(locks!=1||sr_stop_noop_calls!=101000)return 3;
          s.in_mixer=1;s.mix.active=0;sr_audio_stop(&s);
          if(locks!=2||sr_stop_inactive_registered_calls!=1||removals!=2)return 4;
          puts("PASS: real Stop fast-exits idle calls and preserves active removal");
          return 0;
        }'''
        with tempfile.TemporaryDirectory() as d:
            binary=pathlib.Path(d)/'test'
            result=subprocess.run([cc,'-std=c11','-Wall','-Wextra','-x','c','-','-o',str(binary)],input=mock+func+checks,text=True,capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr)
            run=subprocess.run([str(binary)],capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
    def test_counters_and_marker(self):
        s=SRC.read_text()
        for name in ('source_stop_noops','source_stop_active','source_stop_ended','source_play_active_restarts'):
            self.assertIn('A3D.Mixer.'+name,s)
        self.assertIn('A3D.HF7: preserve active Play cursor',s)
if __name__=='__main__':unittest.main()
