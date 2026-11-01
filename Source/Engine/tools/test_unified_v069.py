"""A3D v0.6.9 unified engine, per-title audio, Alice2011 FPS policies, Wine simulation."""
import hashlib,json,os,pathlib,shutil,subprocess,tempfile,unittest
R=pathlib.Path(__file__).resolve().parents[1]
P=json.loads((R/'config/game_profiles_v069.json').read_text())
D=R/'deploy-v0610'

class V069(unittest.TestCase):
 def test_identical_binary_engine(self):
  for filename in ('a3dapi.dll','a3d.dll'):
   digests=[hashlib.sha256((D/game/filename).read_bytes()).hexdigest() for game in P]
   self.assertEqual(len(set(digests)),1)
 def test_safety_audio_defaults_and_profiles(self):
  self.assertEqual((P['Alice2000']['queue_headers'],P['Alice2000']['subblocks'],P['Alice2000']['render_snapshot'],P['Alice2000']['thread_priority']),(6,1,1,0))
  self.assertEqual((P['Alice2011-VorpalFix']['queue_headers'],P['Alice2011-VorpalFix']['subblocks'],P['Alice2011-VorpalFix']['render_snapshot'],P['Alice2011-VorpalFix']['thread_priority']),(6,1,0,0))
  self.assertEqual((P['QuakeIII-117']['queue_headers'],P['QuakeIII-117']['subblocks'],P['QuakeIII-117']['render_snapshot'],P['QuakeIII-117']['thread_priority']),(6,1,1,0))
  for game in P:
   normal=(D/game/'RUN_A3D_WINDOWS.cmd').read_text()
   diagnostic=(D/game/'RUN_A3D_DIAGNOSTIC_WINDOWS.cmd').read_text()
   self.assertIn('A3D_LOG=0',normal)
   self.assertIn('A3D_LOG=1',diagnostic)
   self.assertIn('A3D_MASTER_GAIN=5.0',normal)
   self.assertIn('A3D_HRTF_TAPS=48',normal)
  a=D/'Alice2011-VorpalFix'
  self.assertNotIn('com_maxfps 144',(a/'RUN_A3D_WINDOWS.cmd').read_text())
  self.assertNotIn('com_maxfps 144',(a/'RUN_A3D_WINE.sh').read_text())
  self.assertIn('com_maxfps 144',(a/'RUN_A3D_144FPS_WINDOWS.cmd').read_text())
  self.assertIn('com_maxfps 144',(a/'RUN_A3D_144FPS_WINE.sh').read_text())
  self.assertIn('A3D_WAVEOUT_SUBBLOCKS=2',(a/'RUN_A3D_4x512_FALLBACK_WINDOWS.cmd').read_text())
  self.assertIn('A3D_WAVEOUT_QUEUE_HEADERS=4',(a/'RUN_A3D_4x512_FALLBACK_WINDOWS.cmd').read_text())
  self.assertIn('winmm=n,b',(a/'RUN_A3D_WINE.sh').read_text())
  self.assertIn('+set s_milesdriver a3d2',(a/'RUN_A3D_WINDOWS.cmd').read_text())
  q=D/'QuakeIII-117'
  self.assertTrue((q/'RUN_A3D_32MS_TEST_WINDOWS.cmd').exists())
  self.assertIn('A3D_WAVEOUT_SUBBLOCKS=1',(q/'RUN_A3D_WINDOWS.cmd').read_text())
  self.assertIn('A3D_WAVEOUT_QUEUE_HEADERS=6',(q/'RUN_A3D_WINDOWS.cmd').read_text())
  self.assertIn('A3D_WAVEOUT_SUBBLOCKS=2',(q/'RUN_A3D_3x512_FALLBACK_WINDOWS.cmd').read_text())
  self.assertIn('A3D_WAVEOUT_QUEUE_HEADERS=3',(q/'RUN_A3D_3x512_FALLBACK_WINDOWS.cmd').read_text())
 def test_all_wine_launchers_and_opt_in_144(self):
  with tempfile.TemporaryDirectory() as temporary:
   root=pathlib.Path(temporary)
   fake=root/'fake-wine'
   fake.write_text('#!/usr/bin/env bash\nprintf "gain=%s taps=%s queue=%s sub=%s snapshot=%s priority=%s log=%s args=%s override=%s\\n" "$A3D_MASTER_GAIN" "$A3D_HRTF_TAPS" "$A3D_WAVEOUT_QUEUE_HEADERS" "$A3D_WAVEOUT_SUBBLOCKS" "$A3D_RENDER_SNAPSHOT" "$A3D_WAVEOUT_PRIORITY" "$A3D_LOG" "$*" "$WINEDLLOVERRIDES"\n')
   fake.chmod(0o755)
   for game,c in P.items():
    path=root/game
    shutil.copytree(D/game,path)
    (path/c['game_exe']).write_bytes(b'dummy fixture - never execute')
    for required in c['required']:
     target=path/required;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b'fixture')
    env=os.environ.copy()
    for variable in ('A3D_MASTER_GAIN','A3D_HRTF_TAPS','A3D_WAVEOUT_QUEUE_HEADERS','A3D_WAVEOUT_SUBBLOCKS','A3D_RENDER_SNAPSHOT','A3D_LOG','A3D_WAVEOUT_PRIORITY','WINEDLLOVERRIDES','A3D_WAVEOUT_ADAPTIVE'):
     env.pop(variable,None)
    env['A3D_WINE_EXECUTABLE']=str(fake)
    def launch(script,env=env):
     return subprocess.check_output(['bash',str(path/script)],env=env,text=True,stderr=subprocess.DEVNULL)
    result=launch('RUN_A3D_WINE.sh')
    self.assertIn('gain=5.0',result)
    self.assertIn('taps=48',result)
    self.assertIn(f'queue={c["queue_headers"]}',result)
    self.assertIn(f'sub={c["subblocks"]}',result)
    self.assertIn(f'snapshot={c["render_snapshot"]}',result)
    self.assertIn(f'priority={c["thread_priority"]}',result)
    self.assertIn('log=0',result)
    self.assertIn(f'./{c["bridge_exe"]}',result)
    self.assertIn('a3dapi=n,b;a3d=n,b',result)
    self.assertIn('log=1',launch('RUN_A3D_DIAGNOSTIC_WINE.sh'))
    if game=='Alice2011-VorpalFix':
     self.assertNotIn('com_maxfps',result)
     self.assertIn('winmm=n,b',result)
     self.assertIn('s_milesdriver a3d2',result)
     forced=launch('RUN_A3D_144FPS_WINE.sh')
     self.assertIn('com_maxfps 144',forced)
     self.assertIn('queue=6',forced);self.assertIn('sub=1',forced)
     fallback=launch('RUN_A3D_4x512_FALLBACK_WINE.sh')
     self.assertIn('queue=4',fallback);self.assertIn('sub=2',fallback)
     self.assertNotIn('com_maxfps',fallback)
    if game=='QuakeIII-117':
     exp=launch('RUN_A3D_32MS_TEST_WINE.sh')
     self.assertIn('queue=6',exp);self.assertIn('sub=1',exp)
     fallback=launch('RUN_A3D_3x512_FALLBACK_WINE.sh')
     self.assertIn('queue=3',fallback);self.assertIn('sub=2',fallback)
     self.assertIn('snapshot=1',fallback)
    env['A3D_MASTER_GAIN']='3.0'
    self.assertIn('gain=3.0',launch('RUN_A3D_WINE.sh'))
 def test_debian_read_only_preflight(self):
  s=(R/'DEBIAN13_PREFLIGHT.sh').read_text()
  self.assertNotIn('sudo ',s)
  self.assertIn('dpkg --print-foreign-architectures',s)
  self.assertIn('A3D_WINE_EXECUTABLE',s)

if __name__=='__main__':unittest.main()
