"""Focused offline v089 tests; live Windows game output still required."""
import hashlib, json, subprocess, shutil, unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
AUDIO={'a3dapi.dll':'1126f87bc55ad9a64ff885ec32dd1794bfb69d713cd93e5591cc2997a9cf0711',
'a3d.dll':'9291fd3e74eb43b129d1ff9713f979b6f9f25723f78300c8f4b2ed8e5bbeccd0'}
class Naming(unittest.TestCase):
 def test_audio_is_frozen(self):
  for n,v in AUDIO.items():self.assertEqual(hashlib.sha256((R/'bin'/n).read_bytes()).hexdigest(),v)
 def test_manifest(self):
  for n,v in json.loads((R/'SHA256_MANIFEST.json').read_text())['files'].items():
   self.assertEqual(hashlib.sha256((R/'bin'/n).read_bytes()).hexdigest(),v)
 def test_proxy_is_pe32(self):
  b=(R/'bin/mss32-namefix-v089.dll').read_bytes();offset=int.from_bytes(b[60:64],'little')
  self.assertEqual(b[:2],b'MZ');self.assertEqual(b[offset:offset+4],b'PE\0\0')
  self.assertEqual(int.from_bytes(b[offset+4:offset+6],'little'),0x14c)
 def test_target_only(self):
  s=(R/'source/miles_selection_v089.c').read_text()
  self.assertIn('A3D_MILES_DISPLAY_CANONICAL',s)
  self.assertIn('provider==__atomic_load_n(&aliased_a3d2_handle',s)
  self.assertIn('r==0 &&',s)
  self.assertIn('same(a3d2_alias,"unknown")',s)
  self.assertIn('scopy(a3d2_alias,canonical_a3d2)',s)
  self.assertIn('static char a3d2_alias[64]',s)
  self.assertIn('static void *translate(void*p){return p;}',s)
  for bad in ('WriteProcessMemory','VirtualProtect','regsvr32','OpenProcess('):self.assertNotIn(bad,s)
 def test_focus_two_runs_same_token(self):
  s=(R/'RUN_AUFAKE3D_V089_AUTOTEST.ps1').read_text()
  self.assertIn('01_A3D2_LEGACY_UNKNOWN_CONTROL',s)
  self.assertIn('02_A3D2_CANONICAL_DISPLAY_FIX',s)
  self.assertIn("$env:A3D_MILES_DISPLAY_CANONICAL=$(if($plan.displayfix){'1'}else{'0'})",s)
  self.assertIn('Aureal A3D 2.0 (TM) provider opened',s)
  self.assertIn('IN-GAME LABEL STILL NOT CANONICAL',s)
  self.assertIn('console_says_unknown',s)
  self.assertIn('CopyStage $gameRoot $stage',s)
  self.assertNotIn('+set developer 1',s)
  self.assertNotIn('+set logfile 2',s)
  self.assertIn('$record.provider.strict_identity_verified',s)
 def test_static_evidence_guards(self):
  s=(R/'RUN_AUFAKE3D_V089_AUTOTEST.ps1').read_text()
  for token in ('ReadVa 0x00467533 11','ReadVa 0x00467546 21','ReadVa 0x004675e4 15','ReadVa 0x004675d5 15','known_original_exe','static_display_buffer_hypothesis_supported'):
   self.assertIn(token,s)
 def test_no_bundled_game(self):
  forbidden={'alice.exe','mss32.dll','mssa3d2.m3d','a3d_mss_real.dll'}
  self.assertFalse({p.name.lower() for p in R.rglob('*') if p.is_file()} & forbidden)
 def test_native_mock(self):
  cc=shutil.which('clang');self.assertIsNotNone(cc)
  import tempfile
  with tempfile.TemporaryDirectory() as tmp:
   output=Path(tmp)/'namecheck'
   proc=subprocess.run([cc,'-std=c11','-O1','-Wno-ignored-attributes',str(R/'tests/mock_v089_namefix_native.c'),'-o',str(output)],capture_output=True,text=True)
   self.assertEqual(proc.returncode,0,proc.stderr)
   proc=subprocess.run([str(output)],capture_output=True,text=True)
   self.assertEqual(proc.returncode,0,proc.stderr)
   self.assertIn('PASS v089',proc.stdout)
if __name__=='__main__':unittest.main()
