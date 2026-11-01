"""Source/launcher selection contract for the off-lock render worker."""
from pathlib import Path
import os,shutil,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
PROFILES={'QuakeIII-117':'1','Alice2000':'1','Alice2011-VorpalFix':'0'}
class SnapshotProfiles(unittest.TestCase):
 def test_win_and_wine_modes(self):
  for profile,mode in PROFILES.items():
   p=ROOT/'profiles'/profile
   w=(p/'RUN_A3D_WINDOWS.cmd').read_text()
   s=(p/'RUN_A3D_WINE.sh').read_text()
   self.assertIn('A3D_RENDER_SNAPSHOT='+mode,w)
   self.assertIn('A3D_RENDER_SNAPSHOT="${A3D_RENDER_SNAPSHOT:-'+mode+'}"',s)
   self.assertIn('A3D_MASTER_GAIN=5.0',w)
   self.assertIn('A3D_MASTER_GAIN="${A3D_MASTER_GAIN:-5.0}"',s)
 def test_wine_override_and_default(self):
  with tempfile.TemporaryDirectory() as t:
   d=Path(t);mock=d/'fake-wine'
   mock.write_text('#!/bin/sh\nprintf "snapshot=%s gain=%s queue=%s\n" "$A3D_RENDER_SNAPSHOT" "$A3D_MASTER_GAIN" "$A3D_WAVEOUT_QUEUE_HEADERS"\n')
   mock.chmod(0o755)
   for profile,default in PROFILES.items():
    game=d/profile;game.mkdir()
    sh=game/'RUN_A3D_WINE.sh';sh.write_bytes((ROOT/'profiles'/profile/'RUN_A3D_WINE.sh').read_bytes());sh.chmod(0o755)
    gameexe='quake3.exe' if profile=='QuakeIII-117' else 'alice.exe'
    (game/gameexe).write_bytes(b'x');(game/(gameexe+'.manifest')).write_bytes(b'x')
    if profile=='Alice2011-VorpalFix':
     for name in ('winmm.dll','VorpalFix.ini','SndDrivers/mss32.dll','SndDrivers/mssa3d2.m3d'):
      q=game/name;q.parent.mkdir(exist_ok=True,parents=True);q.write_bytes(b'x')
    for mode,override in ((default,{}),('0' if default=='1' else '1',{'A3D_RENDER_SNAPSHOT':'0' if default=='1' else '1'})):
     env=os.environ.copy();env.pop('A3D_RENDER_SNAPSHOT',None);env.pop('A3D_MASTER_GAIN',None)
     env.update(override);env['A3D_WINE_EXECUTABLE']=str(mock)
     result=subprocess.run(['bash',str(sh)],cwd=game,env=env,capture_output=True,text=True)
     self.assertEqual(result.returncode,0,result.stderr)
     self.assertIn('snapshot='+mode,result.stdout)
     self.assertIn('gain=5.0',result.stdout)
     self.assertIn('queue='+('8' if profile in ('Alice2000','Alice2011-VorpalFix') else '3'),result.stdout)
if __name__=='__main__':unittest.main()
