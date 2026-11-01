"""Offline package and implementation integrity tests (no game, registry or audio device)."""
from pathlib import Path
import hashlib, json, re, shutil, subprocess, tempfile, unittest
R=Path(__file__).resolve().parents[1]
EXPECTED_DLL={
 'a3d.dll':'9291fd3e74eb43b129d1ff9713f979b6f9f25723f78300c8f4b2ed8e5bbeccd0',
 'a3dapi.dll':'1126f87bc55ad9a64ff885ec32dd1794bfb69d713cd93e5591cc2997a9cf0711',
 'mss32-unknown-alias.dll':'ced69a6eb2eb7ac1501d5bfeed2556d85aee61124110aa3cb0ae1e4db93a1eeb',
}
class Integrity(unittest.TestCase):
 def test_integrity_manifest(self):
  hashes=json.loads((R/'SHA256_MANIFEST.json').read_text())['files']
  self.assertGreaterEqual(len(hashes),6)
  for n,h in hashes.items():self.assertEqual(hashlib.sha256((R/'bin'/n).read_bytes()).hexdigest(),h)
 def test_frozen_render_and_proxy(self):
  for n,h in EXPECTED_DLL.items():self.assertEqual(hashlib.sha256((R/'bin'/n).read_bytes()).hexdigest(),h)
 def test_prebuilt_pe32(self):
  for p in (R/'bin').glob('*.dll'):
   b=p.read_bytes();self.assertEqual(b[:2],b'MZ')
   pe=int.from_bytes(b[0x3c:0x40],'little')
   self.assertEqual(b[pe:pe+4],b'PE\0\0')
   self.assertEqual(int.from_bytes(b[pe+4:pe+6],'little'),0x14c)
 def test_no_vendor_game_binary_bundled(self):
  forbidden={'alice.exe','mss32.dll','mssa3d2.m3d','a3d_mss_real.dll'}
  self.assertFalse(forbidden.intersection(x.name.lower() for x in R.rglob('*') if x.is_file()))
 def test_24_sdk_cases_remain_standalone(self):
  s=(R/'tools/Run-AutoDiag-v081.ps1').read_text(encoding='utf-8-sig')
  self.assertIn('prior_v080_suite',s)
  self.assertIn('NOT_RUN_NOT_REQUIRED',s)
  self.assertIn('method_failed_or_error',s)
  self.assertIn('WaitForExit(12000)',s)
 def test_no_original_game_mutation_api(self):
  script=(R/'RUN_A3D_V085_AUTOTEST.ps1').read_text()
  for banned in ('WriteProcessMemory','VirtualProtectEx','regsvr32','Set-ItemProperty','Invoke-WebRequest','Invoke-RestMethod','VirtualAllocEx'):
   self.assertNotIn(banned,script)
  for necessary in ('SHA256_MANIFEST.json','robocopy.exe','A3D_MILES_ALIAS_UNKNOWN','s_milesdriver','A3D_RENDER_SNAPSHOT','A3D_LATENCY_TRACE','A3D_MASTER_GAIN','a3d2','software'):
   self.assertIn(necessary,script)
 def test_hex_metrics_supported(self):
  s=(R/'RUN_A3D_V085_AUTOTEST.ps1').read_text()
  self.assertIn('[convert]::ToInt64',s)
  self.assertIn('queue_empty_events',s)
  self.assertIn('blocks_over_5333us',s)
 def test_native_provider_mock(self):
  cc=shutil.which('clang')
  if not cc:self.skipTest('clang unavailable')
  with tempfile.TemporaryDirectory() as tmp:
   bin=Path(tmp)/'mock'
   proc=subprocess.run([cc,'-std=gnu11','-O1','-Wno-ignored-attributes',str(R/'tests/mock_v083_native.c'),'-o',str(bin)],capture_output=True,text=True)
   self.assertEqual(proc.returncode,0,proc.stderr)
   p=subprocess.run([str(bin)],capture_output=True,text=True)
   self.assertEqual(p.returncode,0,p.stdout+'\n'+p.stderr)
   self.assertIn('alias-only, real provider handles',p.stdout)
 def test_native_pcm_clock(self):
  cc=shutil.which('clang')
  if not cc:self.skipTest('clang unavailable')
  with tempfile.TemporaryDirectory() as tmp:
   bin=Path(tmp)/'clock'
   p=subprocess.run([cc,'-std=gnu11','-O2',str(R/'tests/offline_sources/test_pcm_clock_v085.c'),'-o',str(bin),'-lm'],capture_output=True,text=True)
   self.assertEqual(p.returncode,0,p.stderr)
   p=subprocess.run([str(bin)],capture_output=True,text=True)
   self.assertEqual(p.returncode,0,p.stdout+'\n'+p.stderr)
   self.assertIn('rate=44100',p.stdout)
 def test_native_pcm_snapshot_parity(self):
  cc=shutil.which('clang')
  if not cc:self.skipTest('clang unavailable')
  with tempfile.TemporaryDirectory() as tmp:
   bin=Path(tmp)/'sync'
   p=subprocess.run([cc,'-std=gnu11','-O2',str(R/'tests/offline_sources/test_alice_sync_native.c'),'-o',str(bin),'-lm'],capture_output=True,text=True)
   self.assertEqual(p.returncode,0,p.stderr)
   p=subprocess.run([str(bin)],capture_output=True,text=True)
   self.assertEqual(p.returncode,0,p.stdout+'\n'+p.stderr)
   self.assertIn('adaptive_capture_parity_cases=864 failed=0',p.stdout)
if __name__=='__main__':unittest.main(verbosity=2)
