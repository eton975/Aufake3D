"""v0.7.4 non-invasive Miles adapter structural tests; no Windows execution."""
from pathlib import Path
import tempfile,shutil,subprocess,sys,unittest,struct
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from build_miles_adapter_v074 import exports,spec_def,PEError,build
from security_audit_v072 import import_table,RESTRICTED
class MilesAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.tmp=Path(cls.temp.name);cls.fake=cls.tmp/'mss32.dll'
        clang=shutil.which('clang');link=shutil.which('lld-link')
        if not clang or not link:raise unittest.SkipTest('clang + lld-link required')
        cpp=ROOT/'v074/fixture/fake_mss.c';defs=ROOT/'v074/fixture/fake_mss.def'
        subprocess.run([clang,'-target','i686-pc-windows-msvc','-ffreestanding','-c',str(cpp),'-o',str(cls.tmp/'test.obj')],check=True)
        subprocess.run([link,'/dll','/noentry','/machine:x86','/timestamp:0','/def:'+str(defs),'/out:'+str(cls.fake),str(cls.tmp/'test.obj')],check=True)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def test_exports_parse_ordinals(self):
        self.assertEqual(exports(self.fake),[('_AIL_open_3D_provider@4',1),('_AIL_enumerate_3D_providers@12',2),('_AIL_shutdown@0',3)])
    def test_no_original_overwrite_and_all_exports_kept(self):
        dest=self.tmp/'adapt_forward'
        source=self.fake.read_bytes()
        build(self.fake,ROOT/'runtime-v073/a3dapi.dll',dest)
        self.assertEqual(source,self.fake.read_bytes())
        self.assertEqual(source,(dest/'a3d_mss_real.dll').read_bytes())
        self.assertEqual(exports(dest/'mss32.dll',allow_forwarders=True),exports(self.fake))
        self.assertEqual((dest/'a3dapi.dll').read_bytes(),(ROOT/'runtime-v073/a3dapi.dll').read_bytes())
        with self.assertRaises(PEError):build(self.fake,ROOT/'runtime-v073/a3dapi.dll',dest)
    def test_adapter_no_remote_process_apis_or_registry(self):
        p=self.tmp/'adapt_audit/mss32.dll'
        if not p.is_file():build(self.fake,ROOT/'runtime-v073/a3dapi.dll',self.tmp/'adapt_audit')
        arch,imports=import_table(p.read_bytes());self.assertEqual(arch,'x86')
        names={x.split('!')[-1].lower() for x in imports}
        self.assertFalse(names & RESTRICTED)
        self.assertFalse(any(n.startswith('reg') for n in names))
        self.assertTrue({'createactctxa','activateactctx','deactivateactctx','getprocaddress'}<=names)
    def test_manifest_valid_and_regfree_class(self):
        root=ET.parse(ROOT/'v074/a3d-miles-local.manifest').getroot()
        xml=ET.tostring(root,encoding='unicode')
        self.assertIn('{92FA2C24-253C-11D2-90FB-006008A1F441}',xml)
        self.assertIn('a3dapi.dll',xml)
    def test_unrelated_export_forwarded(self):
        spec=spec_def(exports(self.fake))
        self.assertIn('_AIL_shutdown@0=a3d_mss_real._AIL_shutdown@0 @3',spec)
        self.assertIn('_AIL_open_3D_provider@4=_a3d_intercept_open@4 @1',spec)
    def test_not_a_malware_bypass_or_self_patching(self):
        text=(ROOT/'v074/miles_com_adapter.c').read_text()
        self.assertNotIn('WriteProcessMemory(',text)
        self.assertNotIn('SetThreadContext(',text)
        self.assertIn('CreateActCtxA(',text)
        self.assertIn('DeactivateActCtx(',text)
        self.assertIn('FILE_APPEND_DATA',text)
if __name__=='__main__':unittest.main()
