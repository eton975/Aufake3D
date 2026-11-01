#!/usr/bin/env python3
import contextlib, hashlib, importlib.util, io, json, pathlib, shutil, struct, tempfile, unittest
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('aufake3d_manager',ROOT/'Tools/aufake3d.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)

def fake_pe(s):
 p=bytearray(1024);p[:2]=b'MZ';struct.pack_into('<I',p,0x3c,0x80);p[0x80:0x84]=b'PE\0\0';p[0x84:0x86]=b'\x4c\x01';p[0x100:0x100+len(s)]=s
 return bytes(p)
class ReleaseTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.dir=pathlib.Path(self.tmp.name)
 def seed(self,profile):
  exe=self.dir/a.PROFILES[profile];exe.write_bytes(fake_pe(profile.encode()))
  if profile in ('alice2011','alice2000'):
   s=self.dir/'SndDrivers';s.mkdir()
   (s/'mss32.dll').write_bytes(b'miles-owned')
   if profile=='alice2011':
    (s/'mssa3d2.m3d').write_bytes(b'user owned mssa3d2')
    (self.dir/'winmm.dll').write_bytes(b'user VorpalFix')
    (self.dir/'VorpalFix.ini').write_bytes(b'version=4.2.1')
  return exe
 def test_pe32_payloads(self):
  for p in (ROOT/'Game_Kits').rglob('*'):
   if p.suffix.lower() not in ('.exe','.dll'):continue
   b=p.read_bytes();self.assertEqual(b[:2],b'MZ',str(p));off=struct.unpack_from('<I',b,0x3c)[0]
   self.assertEqual(b[off:off+4],b'PE\0\0',str(p))
   self.assertEqual(struct.unpack_from('<H',b,off+4)[0],0x14c,str(p))
 def test_runtime_core_matches_release(self):
  expected={'a3dapi.dll':'2e6f500e8d86b641d702f21cbfa2662f6327e15c794af7c07745c24cba8e8db2','a3d.dll':'9291fd3e74eb43b129d1ff9713f979b6f9f25723f78300c8f4b2ed8e5bbeccd0'}
  for n,h in expected.items():self.assertEqual(a.sha(ROOT/'Universal_Core'/n),h)
  self.assertEqual(a.sha(ROOT/'Game_Kits/Alice_2011_VorpalFix/COPY_TO_GAME_FOLDER/mss32.dll'),'8bc83f25b228849693ef187877388f917d7a5e3475f7db5e0cf9fa9b708426b8')
 def test_wrong_alice2011_rejected(self):
  x=self.seed('alice2011')
  with self.assertRaisesRegex(ValueError,'hash'):a.install('alice2011',x)
  self.assertFalse((self.dir/'a3dapi.dll').exists())
 def test_wrong_miles_rejected_even_if_game_hash_accepted(self):
  x=self.seed('alice2011')
  with patch.object(a,'PINNED_ALICE',a.sha(x)):
   with self.assertRaisesRegex(ValueError,'Miles'):a.install('alice2011',x)
 def test_alice2011_stage_and_rollback(self):
  x=self.seed('alice2011');orig=x.read_bytes();snd=self.dir/'SndDrivers'
  with patch.object(a,'PINNED_ALICE',a.sha(x)),patch.object(a,'PINNED_MILES',a.sha(snd/'mss32.dll')):
   with contextlib.redirect_stdout(io.StringIO()):a.install('alice2011',x)
   self.assertEqual(x.read_bytes(),orig)
   self.assertEqual((snd/'a3d_mss_real.dll').read_bytes(),b'miles-owned')
   self.assertEqual(a.sha(snd/'mss32.dll'),a.sha(ROOT/'Game_Kits/Alice_2011_VorpalFix/COPY_TO_GAME_FOLDER/mss32.dll'))
   self.assertTrue((self.dir/'RUN_AUFAKE3D_WINE.sh').exists())
   with contextlib.redirect_stdout(io.StringIO()):a.rollback(x)
   self.assertEqual((snd/'mss32.dll').read_bytes(),b'miles-owned')
   self.assertFalse((snd/'a3d_mss_real.dll').exists())
   self.assertEqual(x.read_bytes(),orig)
 def test_alice2000_install(self):
  x=self.seed('alice2000');old=x.read_bytes()
  with contextlib.redirect_stdout(io.StringIO()):a.install('alice2000',x)
  self.assertEqual(x.read_bytes(),old);self.assertTrue((self.dir/'alice-a3d-bridge.exe').exists())
  with contextlib.redirect_stdout(io.StringIO()):a.rollback(x)
  self.assertEqual(x.read_bytes(),old)
 def test_quake3_install(self):
  x=self.seed('quake3');old=x.read_bytes()
  with contextlib.redirect_stdout(io.StringIO()):a.install('quake3',x)
  self.assertEqual(x.read_bytes(),old);self.assertTrue((self.dir/'quake3.exe.manifest').exists())
  with contextlib.redirect_stdout(io.StringIO()):a.rollback(x)
  self.assertEqual(x.read_bytes(),old)
 def test_halflife_install(self):
  x=self.seed('halflife');old=x.read_bytes()
  with contextlib.redirect_stdout(io.StringIO()):a.install('halflife',x)
  self.assertEqual(x.read_bytes(),old);self.assertTrue((self.dir/'halflife-a3d-alpha.exe').exists())
  with contextlib.redirect_stdout(io.StringIO()):a.rollback(x)
  self.assertEqual(x.read_bytes(),old)
 def test_no_unwanted_developer_setting(self):
  for p in (ROOT/'Game_Kits').rglob('RUN_AUFAKE3D_*'):
   if p.is_file():self.assertNotIn('developer 1',p.read_text(encoding='utf-8').lower())
 def test_no_proprietary_miles_or_vorpal(self):
  names={p.name.lower() for p in (ROOT/'Game_Kits').rglob('*') if p.is_file()}
  self.assertEqual(sum(1 for p in (ROOT/'Game_Kits').rglob('mss32.dll')),2)
  self.assertNotIn('a3d_mss_real.dll',names);self.assertNotIn('winmm.dll',names);self.assertNotIn('mssa3d2.m3d',names)
 def test_kit_manifest_matches_actual_files(self):
  import json
  m=json.loads((ROOT/'Game_Kits/INSTALL_MAP.json').read_text())
  for profile,meta in m['profiles'].items():
   kit=ROOT/'Game_Kits'/meta['folder']/'COPY_TO_GAME_FOLDER'
   actual={p.relative_to(kit).as_posix() for p in kit.rglob('*') if p.is_file()}
   self.assertEqual(set(meta['files']),actual,profile)
   self.assertNotIn(meta['exe'],actual)
   expected=a.kit_layout(profile)[0]
   self.assertEqual(meta,expected)
 def test_game_kit_universal_core_byte_identical(self):
  m=json.loads((ROOT/'Game_Kits/INSTALL_MAP.json').read_text())
  for profile,meta in m['profiles'].items():
   kit=ROOT/'Game_Kits'/meta['folder']/'COPY_TO_GAME_FOLDER'
   for dll in ('a3d.dll','a3dapi.dll'):
    self.assertEqual(a.sha(kit/dll),a.sha(ROOT/'Universal_Core'/dll))
   if profile=='alice2011':
    for dll in ('a3d.dll','a3dapi.dll'):
     self.assertEqual(a.sha(kit/'SndDrivers'/dll),a.sha(ROOT/'Universal_Core'/dll))
 def test_install_and_manual_copy_exact_same_filenames(self):
  for profile in a.PROFILES:
   with tempfile.TemporaryDirectory() as temp:
    original_dir=self.dir
    self.dir=pathlib.Path(temp)
    try:
     exe=self.seed(profile)
     if profile=='alice2011':
      snd=self.dir/'SndDrivers'
      with patch.object(a,'PINNED_MILES',a.sha(snd/'mss32.dll')):
       actual={p.relative_to(self.dir).as_posix() for p in a.overlay(profile,exe)}
     else: actual={p.relative_to(self.dir).as_posix() for p in a.overlay(profile,exe)}
     m=a.kit_layout(profile)[0]
     extras={'a3d_mss_real.dll','SndDrivers/a3d_mss_real.dll'} if profile=='alice2011' else set()
     self.assertEqual(actual,set(m['files'])|extras)
    finally:self.dir=original_dir
 def test_source_contains_proxy_and_renderer(self):
  for f in ('Source/Engine/win32/a3dapi.c','Source/Alice2011_NameFix_v089/miles_selection_v089.c','Source/SDK_Method_Conformance_v081/sdk_method_probe_v081.c'):
   self.assertTrue((ROOT/f).is_file())
 def test_rollback_refuses_changed_file(self):
  x=self.seed('quake3')
  with contextlib.redirect_stdout(io.StringIO()):a.install('quake3',x)
  (self.dir/'a3d.dll').write_bytes(b'intervening edit')
  with self.assertRaisesRegex(ValueError,'changed'):a.rollback(x)
 def test_dry_run_does_not_mutate(self):
  x=self.seed('quake3')
  with contextlib.redirect_stdout(io.StringIO()):a.install('quake3',x,True)
  self.assertFalse((self.dir/'a3d.dll').exists())
if __name__=='__main__':unittest.main(verbosity=2)
