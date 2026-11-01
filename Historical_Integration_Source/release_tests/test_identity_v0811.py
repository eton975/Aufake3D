import importlib.util,io,pathlib,struct,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('audit',ROOT/'Tools/check_game_identity.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
TRACE='''AIL_STARTUP_BEGIN
AIL_ENUM_PROVIDER_NAME Aureal A3D 2.0 (TM)
A3D2_ENUM_SELECTED_CANDIDATE 0x00000004
A3D2_ALIAS_ADVERTISED unknown
AIL_OPEN_BEGIN_PROVIDER 0x00000004
AIL_OPEN_RETURN 0x00000000
A3D2_DISPLAY_NAME_UPGRADED Aureal A3D 2.0 (TM)
AIL_OPEN_LISTENER_RETURN 0x192BF190
A3DAPI_MODULE_PATH C:\\Game\\a3dapi.dll
'''
class Audit(unittest.TestCase):
 def test_match(self):
  v=a.trace_evidence(TRACE);self.assertTrue(v['provider_verified']);self.assertTrue(v['name_upgrade_logged'])
 def test_not_2d_substitute(self):
  self.assertFalse(a.trace_evidence(TRACE.replace('AIL_OPEN_BEGIN_PROVIDER 0x00000004','AIL_OPEN_BEGIN_PROVIDER 0x00000005'))['provider_verified'])
 def test_failed_open(self):
  self.assertFalse(a.trace_evidence(TRACE.replace('AIL_OPEN_RETURN 0x00000000','AIL_OPEN_RETURN 0xFFFFFFFF'))['provider_verified'])
 def test_no_listener(self):
  self.assertFalse(a.trace_evidence(TRACE.replace('AIL_OPEN_LISTENER_RETURN 0x192BF190','AIL_OPEN_LISTENER_RETURN 0x00000000'))['provider_verified'])
 def test_latest_session_not_stale(self):
  self.assertFalse(a.trace_evidence(TRACE+'AIL_STARTUP_BEGIN\nAIL_ENUM_PROVIDER_NAME other\n')['provider_verified'])
 def test_name_upgrade_not_required_to_prove_provider(self):
  z=a.trace_evidence(TRACE.replace('A3D2_DISPLAY_NAME_UPGRADED Aureal A3D 2.0 (TM)',''))
  self.assertTrue(z['provider_verified']);self.assertFalse(z['name_upgrade_logged'])
 def test_console_label_only_is_not_provider_proof(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d);(p/'alice.exe').write_bytes(b'MZAureal A3D 2.0 (TM)');(p/'qconsole.log').write_text('Aureal A3D 2.0 (TM) provider opened.')
   z=a.collect('alice2000',p/'alice.exe',console=p/'qconsole.log')
   self.assertFalse(z['runtime']['provider_verified']);self.assertTrue(z['console_canonical_label_observed'])
 def test_alice2000_static_audit_is_not_certification(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)/'alice.exe';p.write_bytes(b'a3d2 unknown Aureal A3D 2.0')
   z=a.collect('alice2000',p)
   self.assertFalse(z['runtime']['provider_verified']);self.assertGreater(z['static_markers_not_proof']['a3d2']['ascii'],0)
 def test_actual_redacted_windows_v089_trace(self):
  s=(ROOT/'release_tests/fixtures/v089_alice2011_actual_trace_redacted.txt').read_text()
  v=a.trace_evidence(s)
  self.assertTrue(v['provider_verified']);self.assertTrue(v['name_upgrade_logged'])
 def test_shared_dll_identity_across_profiles(self):
  import hashlib
  for n in ('a3d.dll','a3dapi.dll'):
   p=ROOT/'Universal_Core'/n
   self.assertTrue(p.is_file());self.assertGreater(p.stat().st_size,1024)
   self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),{'a3d.dll':'9291fd3e74eb43b129d1ff9713f979b6f9f25723f78300c8f4b2ed8e5bbeccd0','a3dapi.dll':'2e6f500e8d86b641d702f21cbfa2662f6327e15c794af7c07745c24cba8e8db2'}[n])
if __name__=='__main__':unittest.main(verbosity=2)
