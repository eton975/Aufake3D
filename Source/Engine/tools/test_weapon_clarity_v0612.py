import hashlib,json,subprocess,tempfile,unittest,shutil,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'deploy-v0612'
G=('Alice2000','Alice2011-VorpalFix','QuakeIII-117')
class ClarityTests(unittest.TestCase):
 def test_conservative_fingerprints_no_audio(self):
  t=(ROOT/'win32/weapon_signatures_v0612.inc').read_text()
  self.assertEqual(t.count('1u},'),15)
  self.assertIn('0xb1cff040u',t)
  self.assertIn('0xc428d666u',t)
  self.assertNotIn('static const signed short',t)
  self.assertTrue(all(not x.suffix.lower() in ('.wav','.flac','.bin') for x in D.rglob('*') if x.is_file()))
 def test_core_snapshot_and_optin(self):
  c=(ROOT/'win32/stream_core.h').read_text()
  w=(ROOT/'win32/stream_winmm.inc').read_text()
  self.assertIn('m->weapon_clarity && v->weapon_protected',c)
  self.assertIn('m->limiter_gain+=(m->weapon_clarity?0.00020f:0.00010f)',c)
  self.assertIn('d->weapon_protected=a->weapon_protected;',w)
  self.assertIn('d->master_boost=a->master_boost;d->weapon_clarity=a->weapon_clarity;',w)
  self.assertIn('a3d_weapon_is_known(s->staff_pcm_sig)',w)
 def test_3_shared_pe32_and_settings(self):
  p=json.loads((ROOT/'config/game_profiles_v069.json').read_text())
  for game in G:
   self.assertEqual(p[game]['queue_headers'],6)
   self.assertEqual(p[game]['subblocks'],1)
   cmd=(D/game/'RUN_A3D_WINDOWS.cmd').read_text()
   sh=(D/game/'RUN_A3D_WINE.sh').read_text()
   expected='1' if game.startswith('Alice') else '0'
   self.assertIn('A3D_WEAPON_CLARITY='+expected,cmd)
   self.assertIn('A3D_WEAPON_CLARITY="${A3D_WEAPON_CLARITY:-'+expected+'}"',sh)
   self.assertIn('A3D_MASTER_GAIN=5.0',cmd)
   self.assertIn('A3D_HRTF_TAPS=48',cmd)
   self.assertIn('A3D_WAVEOUT_QUEUE_HEADERS=6',cmd)
   self.assertIn('A3D_WAVEOUT_SUBBLOCKS=1',cmd)
   self.assertIn('A3D_LOG=0',cmd)
  for name in ('a3dapi.dll','a3d.dll'):
   self.assertEqual(len({hashlib.sha256((D/g/name).read_bytes()).digest() for g in G}),1)
  self.assertNotIn('com_maxfps 144',(D/G[1]/'RUN_A3D_WINDOWS.cmd').read_text())
  self.assertIn('com_maxfps 144',(D/G[1]/'RUN_A3D_144FPS_WINDOWS.cmd').read_text())
 def test_fallback_and_wine_mock(self):
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp);fake=path/'fake-wine'
   fake.write_text('#!/bin/sh\necho clarity=$A3D_WEAPON_CLARITY queue=$A3D_WAVEOUT_QUEUE_HEADERS snapshot=$A3D_RENDER_SNAPSHOT\n')
   fake.chmod(0o755)
   for game in G:
    install=path/game;shutil.copytree(D/game,install)
    original='quake3.exe' if game==G[2] else 'alice.exe'
    (install/original).write_bytes(b'placeholder')
    if game==G[1]:
     for r in ('winmm.dll','SndDrivers/mssa3d2.m3d'):
      p=install/r;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'fixture')
    env=os.environ.copy();env.pop('A3D_WEAPON_CLARITY',None);env['A3D_WINE_EXECUTABLE']=str(fake)
    def call(name,env=env):return subprocess.check_output(['bash',str(install/name)],env=env,text=True,stderr=subprocess.DEVNULL)
    self.assertIn('clarity='+('1' if game!=G[2] else '0'),call('RUN_A3D_WINE.sh'))
    if game!=G[2]:
     self.assertIn('clarity=0',call('RUN_A3D_ORIGINAL_MIX_WINE.sh'))
     env['A3D_WEAPON_CLARITY']='0'
     self.assertIn('clarity=0',call('RUN_A3D_WINE.sh'))
 def test_native_mixer(self):
  if not shutil.which('gcc'):self.skipTest('Native compiler unavailable')
  with tempfile.TemporaryDirectory() as t:
   binary=Path(t)/'clarity-test'
   subprocess.run(['gcc','-std=c11','-O2',str(ROOT/'win32/test_clarity_v0612_native.c'),'-o',str(binary)],check=True)
   result=subprocess.run([str(binary)],capture_output=True,text=True,check=True)
   self.assertIn('PASS:',result.stdout)
if __name__=='__main__':unittest.main()
