"""Hotfix 7 regression: compile the actual active-Play guard as native C.
The tested function is extracted verbatim from the implementation, avoiding
an independently reimplemented model with different behavior.
"""
import pathlib
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
WINMM = (ROOT / 'win32' / 'stream_winmm.inc').read_text()
SOURCE = (ROOT / 'win32' / 'source_probe.inc').read_text()

class ActivePlayHF7(unittest.TestCase):
    def test_guard_native(self):
        start = WINMM.index('static int sr_play_can_preserve(')
        end = WINMM.index('static HRESULT sr_audio_play(', start)
        code = WINMM[start:end]
        cases = [
            (2, 1, 1, 1, 0, 0, 1), # looping PCM updated: do not lose cursor
            (2, 1, 1, 1, 1, 0, 1), # unchanged looping
            (2, 1, 1, 0, 1, 0, 1), # repeated single, PCM unchanged
            (2, 1, 1, 0, 0, 0, 0), # fresh one-shot data: retrigger
            (1, 1, 1, 0, 1, 0, 0), # conservative policy one-shots retrigger
            (1, 1, 1, 1, 0, 0, 1), # conservative policy looping preserved
            (0, 1, 1, 1, 1, 0, 0), # legacy behavior
            (2, 1, 0, 1, 1, 0, 0), # loop mode transition
            (2, 1, 1, 1, 1, 1, 0), # rewind / explicit seek
            (2, 0, 1, 1, 1, 0, 0), # inactive voice always starts
            (2, 1, 1, 0, 1, 1, 0), # single-shot explicit seek
        ]
        tests = '\n'.join(f'if(sr_play_can_preserve({a},{b},{c},{d},{e},{f})!={expected})return {i};'
                          for i,(a,b,c,d,e,f,expected) in enumerate(cases,1))
        src = f'#include <stdio.h>\n{code}\nint main(void){{{tests}\nputs("HF7 active-Play native regressions PASS");return 0;}}\n'
        if not shutil.which('gcc'):
            self.skipTest('gcc unavailable')
        with tempfile.TemporaryDirectory() as tmp:
            testfile = pathlib.Path(tmp)/'play.c'
            binary = pathlib.Path(tmp)/'play'
            testfile.write_text(src)
            subprocess.run(['gcc','-std=c11','-O2','-Wall','-Wextra','-Werror',str(testfile),'-o',str(binary)],check=True)
            subprocess.run([str(binary)],check=True)

    def test_integration_guards(self):
        self.assertIn('if(s->in_mixer && s->mix.active){', WINMM)
        self.assertIn('if(sr_play_can_preserve(', WINMM)
        self.assertLess(WINMM.index('if(sr_play_can_preserve('), WINMM.index('a3dmix_voice_init(v);'))
        self.assertLess(WINMM.index('if(sr_play_can_preserve('), WINMM.index('sr_copy(s->play_pcm,s->pcm,s->wave_size);'))
        self.assertIn('s->pcm_update_serial++;', SOURCE)
        self.assertIn('s->last_play_pcm_serial=s->pcm_update_serial;', WINMM)
        self.assertIn('s->play_repositioned=1;', SOURCE)
        self.assertIn('A3D.HF7:', WINMM)

if __name__ == '__main__':
    unittest.main()
