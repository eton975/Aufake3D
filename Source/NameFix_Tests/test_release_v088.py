"""Offline v088 provenance and scoped-provider tests; does not invoke Windows games."""
from pathlib import Path
import hashlib,json,subprocess,tempfile,shutil,unittest
R=Path(__file__).resolve().parents[1]
V085={'a3dapi.dll':'1126f87bc55ad9a64ff885ec32dd1794bfb69d713cd93e5591cc2997a9cf0711',
'a3d.dll':'9291fd3e74eb43b129d1ff9713f979b6f9f25723f78300c8f4b2ed8e5bbeccd0'}
class Integrity(unittest.TestCase):
 def test_manifest(self):
  for n,h in json.loads((R/'SHA256_MANIFEST.json').read_text())['files'].items():
   self.assertEqual(hashlib.sha256((R/'bin'/n).read_bytes()).hexdigest(),h,n)
 def test_frozen_audio(self):
  for n,h in V085.items():self.assertEqual(hashlib.sha256((R/'bin'/n).read_bytes()).hexdigest(),h)
 def test_pe32(self):
  for p in (R/'bin').glob('*.dll'):
   d=p.read_bytes();self.assertEqual(d[:2],b'MZ');pe=int.from_bytes(d[60:64],'little')
   self.assertEqual(d[pe:pe+4],b'PE\0\0');self.assertEqual(int.from_bytes(d[pe+4:pe+6],'little'),0x14c)
 def test_no_proprietary_game_or_vendor_dll(self):
  forbidden={'alice.exe','mss32.dll','mssa3d2.m3d','a3d_mss_real.dll'}
  self.assertFalse({p.name.lower() for p in R.rglob('*') if p.is_file()}&forbidden)
 def test_controls_really_original(self):
  s=(R/'RUN_AUFAKE3D_V088_AUTOTEST.ps1').read_text()
  self.assertIn('01_VENDOR_MILES_BASELINE',s)
  self.assertIn('02_A3D2_SCOPED',s)
  self.assertIn('03_PROXY_PASS_SOFTWARE',s)
  self.assertIn('04_A3D2_REPEAT',s)
  self.assertIn('ClearOwnedAudio $bin $drivers',s)
  self.assertIn('Copy-Item -LiteralPath $originalMiles -Destination (Join-Path $folder \'mss32.dll\')',s)
  self.assertIn('if($plan.proxy){ApplyProxy $bin $drivers}',s)
  self.assertIn('CopyStage $gameRoot $stage',s)
 def test_startup_safety_guard(self):
  s=(R/'RUN_AUFAKE3D_V088_AUTOTEST.ps1').read_text()
  self.assertNotIn('+set developer 1',s)
  self.assertNotIn('+set logfile 2',s)
  self.assertIn('function GetSharedAliceConfigPath',s)
  self.assertIn('function GetDeveloperFlag',s)
  self.assertIn('developerConfigEnabledBefore',s)
  self.assertIn('shared_config=',s)
  self.assertIn('main_menu_observation',s)
  self.assertIn('copyright_intro_observation',s)
  self.assertIn('spatial_direction_observation',s)
 def test_miles_proxy_remains_frozen(self):
  s=(R/'RUN_AUFAKE3D_V088_AUTOTEST.ps1').read_text()
  self.assertIn('mss32-scoped-a3d2-v086.dll',s)
  self.assertIn('A3D2 canonical name/handle/activation not all verified',s)
  self.assertIn('strict_identity_verified',s)
 def test_guard_enabled(self):
  s=(R/'RUN_AUFAKE3D_V088_AUTOTEST.ps1').read_text()
  self.assertIn("$env:A3D_MILES_REQUIRE_CLI_A3D2='1'",s)
  self.assertIn("$env:A3D_MASTER_GAIN='5.0'",s)
  self.assertIn("$env:A3D_WAVEOUT_QUEUE_HEADERS='3'",s)
  self.assertIn("$env:A3D_WAVEOUT_SUBBLOCKS='2'",s)
 def test_no_exe_patch_or_registry_write(self):
  s=(R/'RUN_AUFAKE3D_V088_AUTOTEST.ps1').read_text()
  for banned in ('WriteProcessMemory','VirtualProtectEx','regsvr32','Set-ItemProperty','Invoke-WebRequest','VirtualAllocEx'):
   self.assertNotIn(banned,s)
 def test_source_contains_scoped_guard(self):
  s=(R/'source/miles_selection_v086.c').read_text()
  self.assertIn('explicit_a3d2_cli',s)
  self.assertIn('GetCommandLineA',s)
  self.assertIn('A3D_MILES_REQUIRE_CLI_A3D2',s)
 def test_native_mock_sanitized(self):
  cc=shutil.which('clang')
  if not cc:self.skipTest('clang unavailable')
  with tempfile.TemporaryDirectory() as td:
   p=subprocess.run([cc,'-std=gnu11','-O1','-Wno-ignored-attributes','-fsanitize=address,undefined',str(R/'tests/mock_v086_native.c'),'-o',str(Path(td)/'mock')],capture_output=True,text=True)
   self.assertEqual(p.returncode,0,p.stderr)
   p=subprocess.run([str(Path(td)/'mock')],capture_output=True,text=True)
   self.assertEqual(p.returncode,0,p.stdout+p.stderr)
   self.assertIn('real provider handles',p.stdout)
 def test_native_pcm_clock(self):
  cc=shutil.which('clang')
  if not cc:self.skipTest('clang unavailable')
  with tempfile.TemporaryDirectory() as td:
   p=subprocess.run([cc,'-std=gnu11','-O2',str(R/'tests/offline_sources/test_pcm_clock_v085.c'),'-o',str(Path(td)/'clock'),'-lm'],capture_output=True,text=True)
   self.assertEqual(p.returncode,0,p.stderr)
   p=subprocess.run([str(Path(td)/'clock')],capture_output=True,text=True)
   self.assertEqual(p.returncode,0,p.stdout+p.stderr)
   self.assertIn('rate=44100',p.stdout)
 def test_snapshot_parity(self):
  cc=shutil.which('clang')
  if not cc:self.skipTest('clang unavailable')
  with tempfile.TemporaryDirectory() as td:
   p=subprocess.run([cc,'-std=gnu11','-O2',str(R/'tests/offline_sources/test_alice_sync_native.c'),'-o',str(Path(td)/'snapshot'),'-lm'],capture_output=True,text=True)
   self.assertEqual(p.returncode,0,p.stderr)
   p=subprocess.run([str(Path(td)/'snapshot')],capture_output=True,text=True)
   self.assertEqual(p.returncode,0,p.stdout+p.stderr)
   self.assertIn('adaptive_capture_parity_cases=864 failed=0',p.stdout)
class SpatialRegression(unittest.TestCase):
 def test_calibration_json_and_wavs(self):
  root=R/'calibration'
  d=json.loads((root/'spatial_hrtf_reference_v088.json').read_text())
  self.assertEqual(d['sample_rate'],48000)
  self.assertGreater(d['left_ear_advantage_db'],2.0)
  self.assertGreater(d['right_ear_advantage_db'],2.0)
  self.assertGreater(d['near_to_far_energy_ratio'],2.0)
  self.assertNotEqual(d['front_hrir_index'],d['behind_hrir_index'])
  self.assertEqual(d['failures'],0)
  for name in ('left','right','front','behind','far_left'):
   b=(root/(name+'.wav')).read_bytes()
   self.assertEqual(b[:4],b'RIFF')
   self.assertEqual(b[8:12],b'WAVE')
   self.assertEqual(int.from_bytes(b[24:28],'little'),48000)
   self.assertEqual(len(b),44+48000*4)
 def test_spatial_c_against_shared_implementation(self):
  cc=shutil.which('clang')
  if not cc:self.skipTest('clang unavailable')
  with tempfile.TemporaryDirectory() as td:
   out=Path(td)/'spatial'
   p=subprocess.run([cc,'-std=c11','-O2','-I'+str(R/'tests'),str(R/'tests/spatial_hrtf_probe_v088.c'),'-lm','-o',str(out)],capture_output=True,text=True)
   self.assertEqual(p.returncode,0,p.stdout+p.stderr)
   p=subprocess.run([str(out)],capture_output=True,text=True)
   self.assertEqual(p.returncode,0,p.stdout+p.stderr)
   obj=json.loads(p.stdout)
   want=json.loads((R/'calibration/spatial_hrtf_reference_v088.json').read_text())
   self.assertEqual(obj,want)
 def test_strict_game_evidence_and_human_observations(self):
  s=(R/'RUN_AUFAKE3D_V088_AUTOTEST.ps1').read_text()
  for term in ('canonical_provider','enum_canonical','strict_identity_verified',
   'AIL_ENUM_PROVIDER_NAME Aureal A3D 2','AIL_OPEN_LISTENER_RETURN',
   'instrumented_3d_activity','spatial_direction_observation',
   'front_back_observation','distance_observation',
   'A3D.Latency.listener_orientation6_updates','A3D.Mixer.HF9.geometry_trace_calls'):
   self.assertIn(term,s)
  self.assertIn("version='0.8.8'",s)
  self.assertNotIn('version=\'0.8.7\'',s)
  self.assertNotIn('+set developer 1',s)
  self.assertIn('actual_console_label_fixed=$false',s)
 def test_launcher_payload(self):
  s=(R/'source/standalone_launcher_v088.c').read_text()
  self.assertIn("'0','8','8','Z'",s)
  self.assertIn('Two Alice sessions will launch',s)
  self.assertIn('RUN_AUFAKE3D_V088_AUTOTEST.ps1',s)
if __name__=='__main__':unittest.main(verbosity=2)
