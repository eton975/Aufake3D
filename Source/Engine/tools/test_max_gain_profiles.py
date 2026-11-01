"""Offline contract checks for the v0.6.1 max-gain deployment profiles."""
from pathlib import Path
import hashlib
import os
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
PROFILES=['QuakeIII-117','Alice2000','Alice2011-VorpalFix']
class ProfileGains(unittest.TestCase):
    def test_all_six_launchers_default_to_five(self):
        for profile in PROFILES:
            p=ROOT/'profiles'/profile
            w=(p/'RUN_A3D_WINDOWS.cmd').read_text()
            s=(p/'RUN_A3D_WINE.sh').read_text()
            self.assertIn('if not defined A3D_MASTER_GAIN set "A3D_MASTER_GAIN=5.0"', w)
            self.assertNotIn('if not defined A3D_MASTER_GAIN set "A3D_MASTER_GAIN=1.0"', w)
            self.assertIn('export A3D_MASTER_GAIN="${A3D_MASTER_GAIN:-5.0}"', s)
            self.assertNotIn('export A3D_MASTER_GAIN="${A3D_MASTER_GAIN:-1.0}"',s)
    def test_intrinsic_gain_and_peak_limiter(self):
        for name in ['win32/stream_winmm.inc','win32/a3dapi.c']:
            self.assertIn('a3d_tuning_env("A3D_MASTER_GAIN",5.0f,0.1f,5.0f)', (ROOT/name).read_text())
        s=(ROOT/'win32/stream_core.h').read_text()
        self.assertIn('m->master_boost=5.0f;',s)
        self.assertIn('float max_gain=peak>0.95f?0.95f/peak:1.0f;',s)
        self.assertIn('out_l*m->limiter_gain',s)
        self.assertIn('out_r*m->limiter_gain',s)
    def test_wine_launcher_inheritance_and_override(self):
        if not shutil.which('bash'):
            self.skipTest('bash unavailable')
        with tempfile.TemporaryDirectory() as t:
            path=Path(t)
            mock=path/'mock-wine.sh'
            mock.write_text('#!/bin/sh\nprintf "gain=%s queue=%s args=%s\\n" "$A3D_MASTER_GAIN" "$A3D_WAVEOUT_QUEUE_HEADERS" "$*"\n')
            mock.chmod(0o755)
            for profile in PROFILES:
                d=path/profile; d.mkdir()
                shutil.copy2(ROOT/'profiles'/profile/'RUN_A3D_WINE.sh',d/'RUN_A3D_WINE.sh')
                (d/('quake3.exe' if profile=='QuakeIII-117' else 'alice.exe')).write_bytes(b'test')
                (d/('quake3.exe.manifest' if profile=='QuakeIII-117' else 'alice.exe.manifest')).write_text('test')
                if profile=='Alice2011-VorpalFix':
                    for f in ['winmm.dll','VorpalFix.ini','SndDrivers/mss32.dll','SndDrivers/mssa3d2.m3d']:
                        dest=d/f;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b'test')
                for want,env_add in [('5.0',{}),('1.0',{'A3D_MASTER_GAIN':'1.0'})]:
                    env=os.environ.copy();env.pop('A3D_MASTER_GAIN',None)
                    env.update(env_add);env['A3D_WINE_EXECUTABLE']=str(mock)
                    proc=subprocess.run(['bash',str(d/'RUN_A3D_WINE.sh')],cwd=path,env=env,capture_output=True,text=True)
                    self.assertEqual(proc.returncode,0,(profile,proc.stderr))
                    self.assertIn('gain='+want,proc.stdout)
                    self.assertIn('queue='+('8' if profile in ('Alice2000','Alice2011-VorpalFix') else '3'),proc.stdout)
if __name__=='__main__':unittest.main()
