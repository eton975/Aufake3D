import unittest,struct,tempfile,io,zipfile,wave,hashlib,json
from pathlib import Path
import numpy as np
from analyse_weapons_v0611 import read_capture,read_references,prepare_index,rank_sound,normalized_correlation
R=Path(__file__).resolve().parents[1]
D=R/'deploy-v0612'
G=('Alice2000','Alice2011-VorpalFix','QuakeIII-117')
class WeaponForensicsV0611(unittest.TestCase):
 def test_catalog_all_100_no_assets(self):
  catalog=json.loads((R/'tools/weapon_reference_catalog_v0611.json').read_text())
  self.assertEqual(catalog['count'],100)
  self.assertEqual(len({x['name'] for x in catalog['entries']}),100)
  self.assertTrue(all(x['bits']==16 and x['channels']==1 for x in catalog['entries']))
  for p in D.rglob('*'):
   if p.is_file():self.assertFalse(p.suffix.lower() in ('.wav','.flac'),p)
 def test_audio_defaults_not_changed(self):
  profiles=json.loads((R/'config/game_profiles_v069.json').read_text())
  self.assertTrue(all(profiles[x]['queue_headers']==6 and profiles[x]['subblocks']==1 for x in G))
  self.assertEqual([profiles[x]['render_snapshot'] for x in G],[1,0,1])
  for game in G:
   for name in ('RUN_A3D_WINDOWS.cmd','RUN_A3D_WINE.sh'):
    text=(D/game/name).read_text()
    self.assertIn('A3D_LOG',text)
    self.assertNotIn('A3D_WEAPON_CAPTURE=1',text)
  text=(D/'Alice2011-VorpalFix'/'RUN_A3D_WINDOWS.cmd').read_text()
  self.assertNotIn('com_maxfps 144',text)
  self.assertIn('com_maxfps 144',(D/'Alice2011-VorpalFix'/'RUN_A3D_144FPS_WINDOWS.cmd').read_text())
 def test_diagnostic_optin_windows_wine_and_source_capture(self):
  c=(R/'win32/staff_diag.inc').read_text()
  self.assertIn('WEAPON_CAPTURE_SLOTS 256u',c)
  self.assertIn('WEAPON_CAPTURE_BYTES 16384u',c)
  self.assertIn('A3D_WEAPON_CAPTURE',c)
  self.assertIn('weapon_capture_dump();',(R/'win32/stream_winmm.inc').read_text())
  for game in G[:2]:
   cmd=(D/game/'RUN_A3D_WEAPON_DIAGNOSTIC_WINDOWS.cmd').read_text()
   sh=(D/game/'RUN_A3D_WEAPON_DIAGNOSTIC_WINE.sh').read_text()
   self.assertIn('A3D_WEAPON_CAPTURE=1',cmd)
   self.assertIn('A3D_WEAPON_CAPTURE=1',sh)
   self.assertIn('A3D_STAFF_DIAG=1',cmd)
 def test_identical_shared_pe32(self):
  for dll in ('a3dapi.dll','a3d.dll'):
   self.assertEqual(len({hashlib.sha256((D/g/dll).read_bytes()).digest() for g in G}),1)
  dll=(D/G[0]/'a3dapi.dll').read_bytes()
  off=struct.unpack_from('<I',dll,0x3c)[0]
  self.assertEqual(dll[off:off+4],b'PE\0\0')
  self.assertEqual(struct.unpack_from('<H',dll,off+4)[0],0x14c)
 def test_synthetic_source_matches_noisy_quiet_and_shifted(self):
  rate=22050
  t=np.arange(12000)/rate
  a=(np.sin(2*np.pi*(120*t+160*t*t))*np.exp(-0.8*t)*.5).astype(np.float32)
  b=(np.sin(2*np.pi*(350+400*t)*t)*(.3+0.2*np.sin(2*np.pi*8*t))).astype(np.float32)
  refs=[]
  for name,data in [('synthetic_a.wav',a),('synthetic_b.wav',b)]:
   refs.append({'name':name,'rate':rate,'pcm':data})
  index,labels=prepare_index(refs)
  shifted=np.r_[np.zeros(256,dtype=np.float32),a[:7680]*0.23]
  record={'pcm':shifted,'rate':rate}
  name,score,coarse=rank_sound(record,refs,index,labels)
  self.assertEqual(name,'synthetic_a.wav')
  self.assertGreater(score,0.7)
 def test_capture_format_reader_and_bad_magic(self):
  with tempfile.TemporaryDirectory() as temp:
   p=Path(temp)/'test.bin'
   with p.open('wb') as f:
    f.write(struct.pack('<8sII',b'A3DWPC11',1,16384))
    f.write(struct.pack('<10I',123,7,22050,1,16,2048,400,1000,0,4096))
    f.write((b'\1\0')*1024+(b'\0')*(16384-2048))
   capture=list(read_capture(p))
   self.assertEqual(len(capture),1)
   self.assertEqual(capture[0]['id'],7)
   self.assertEqual(len(capture[0]['pcm']),1024)
   p.write_bytes(b'garbage')
   with self.assertRaises(ValueError):list(read_capture(p))
if __name__=='__main__':unittest.main()
