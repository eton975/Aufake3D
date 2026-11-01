"""Tests for alpha infrastructure; synthetic fixtures are not retail-game tests."""
from pathlib import Path
import hashlib,json,os,shutil,struct,subprocess,sys,tempfile,time,unittest,uuid
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools'))
from inspect_game_v070 import inspect_file,inventory
D=R/'deploy-v070-alpha'
P=json.loads((R/'config/game_profiles_v070_alpha.json').read_text())['profiles']
def pe_fixture(machine=0x14c,magic=0x10b):
    b=bytearray(512);b[:2]=b'MZ';struct.pack_into('<I',b,60,64);b[64:68]=b'PE\0\0'
    struct.pack_into('<H',b,68,machine);struct.pack_into('<H',b,84,224);struct.pack_into('<H',b,88,magic)
    return b

class InventoryTests(unittest.TestCase):
    def test_guid_and_pe32(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'Galaxy.dll';p.write_bytes(pe_fixture()+uuid.UUID('e4c40280-ccba-11d2-9dcf-00500411582f').bytes_le)
            before=hashlib.sha256(p.read_bytes()).hexdigest();result=inspect_file(p)
            self.assertTrue(result['pe32_x86']);self.assertEqual(result['guid_evidence']['IID_IA3d4']['file_offset'],512)
            self.assertEqual(result['sha256'],before);self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),before)
    def test_reject_truncated_and_wrong_architecture(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'hl.exe'
            for data in (b'MZ',b'not a PE',pe_fixture(0x8664,0x20b)):
                p.write_bytes(data);self.assertFalse(inspect_file(p)['pe32_x86'])
    def test_system_resolution_missing_and_ambiguous(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);system=root/'System';system.mkdir();(system/'Unreal.exe').write_bytes(pe_fixture())
            result=inventory(root,'unreal');self.assertEqual(result['files'][0]['file'],'Unreal.exe')
            self.assertIn('Galaxy.dll',result['missing_files']);self.assertFalse(result['gameplay_verified'])
    def test_output_cannot_overwrite_existing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'hl.exe';target.write_bytes(pe_fixture());before=target.read_bytes()
            result=subprocess.run([sys.executable,str(R/'tools/inspect_game_v070.py'),'halflife',tmp,'--out',str(target)],capture_output=True)
            self.assertNotEqual(result.returncode,0);self.assertEqual(target.read_bytes(),before)

class ProfileTests(unittest.TestCase):
    def test_shared_engine_and_pe32(self):
        games=('Alice2000','Alice2011-VorpalFix','QuakeIII-117',*P)
        for dll in ('a3dapi.dll','a3d.dll'):
            self.assertEqual(len({hashlib.sha256((D/g/dll).read_bytes()).digest() for g in games}),1)
        for name,p in P.items():self.assertTrue(inspect_file(D/name/p['launcher'])['pe32_x86'])
    def test_candidate_policies(self):
        for name in P:
            cmd=(D/name/'RUN_A3D_WINDOWS.cmd').read_text()
            for setting in ('A3D_LOG=0','A3D_WEAPON_CLARITY=0','A3D_HRTF_TAPS=48','A3D_MASTER_GAIN=5.0','A3D_WAVEOUT_QUEUE_HEADERS=6'):
                self.assertIn(setting,cmd)
            self.assertIn('unverified',cmd)
        self.assertIn('+s_eax 0 +s_a3d 1',(D/'HalfLife-Retail/RUN_A3D_WINDOWS.cmd').read_text())
    def test_all_bash_syntax(self):
        for p in D.rglob('*.sh'):subprocess.run(['bash','-n',str(p)],check=True)
    def test_wine_mock_arguments_and_inheritance(self):
        with tempfile.TemporaryDirectory(prefix='a3d alpha spaces ') as tmp:
            root=Path(tmp);fake=root/'fake-wine'
            fake.write_text('#!/usr/bin/env bash\nprintf "clarity=%s gain=%s log=%s prefix=%s override=%s\\n" "$A3D_WEAPON_CLARITY" "$A3D_MASTER_GAIN" "$A3D_LOG" "$WINEPREFIX" "$WINEDLLOVERRIDES"\nprintf "arg=<%s>\\n" "$@"\n')
            fake.chmod(0o755)
            for name,profile in P.items():
                folder=root/name;shutil.copytree(D/name,folder)
                for required in profile['required']:(folder/required).write_bytes(pe_fixture())
                env={k:v for k,v in os.environ.items() if not k.startswith('A3D_')}
                env.update(A3D_WINE_EXECUTABLE=str(fake),WINEPREFIX='prefix with spaces',WINEDLLOVERRIDES='other=n,b')
                def run(script):return subprocess.check_output(['bash',str(folder/script),'+alpha_probe','two words'],env=env,text=True,stderr=subprocess.DEVNULL)
                normal=run('RUN_A3D_WINE.sh')
                self.assertIn('clarity=0 gain=5.0 log=0',normal);self.assertIn('prefix=prefix with spaces',normal)
                self.assertIn('other=n,b',normal);self.assertIn('arg=<two words>',normal)
                self.assertIn('arg=<./'+profile['launcher']+'>',normal)
                self.assertIn('log=1',run('RUN_A3D_DIAGNOSTIC_WINE.sh'))
                env['A3D_MASTER_GAIN']='2.0';self.assertIn('gain=2.0',run('RUN_A3D_WINE.sh'))

@unittest.skipUnless(os.name=='nt','Native Windows bootstrap test')
class ActivationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(prefix='alpha bootstrap ');cls.root=Path(cls.tmp.name)
        compiler=shutil.which('clang');linker=shutil.which('lld-link')
        if not compiler:raise unittest.SkipTest('Clang required')
        if linker:link=[linker]
        else:link=[shutil.which('ld.lld'),'-flavor','link']
        if not link[0]:raise unittest.SkipTest('LLD required')
        obj=cls.root/'fixture.obj';exe=cls.root/'fixture.exe'
        subprocess.run([compiler,'-target','i686-pc-windows-msvc','-ffreestanding','-fno-stack-protector','-fno-builtin','-O2','-c',str(R/'experimental/activation_fixture.c'),'-o',str(obj)],check=True)
        imports={'CoInitialize':4,'CoUninitialize':0,'CoCreateInstance':20,'ExitProcess':4,'GetStdHandle':4,'WriteFile':20,'GetCommandLineA':0,'GetEnvironmentVariableA':12}
        # The core recipe provides ole32 and a kernel32 import library containing
        # all fixture calls except GetCommandLineA; combine the experimental lib.
        subprocess.run(link+['/subsystem:console','/entry:start@0','/machine:x86','/nodefaultlib','/timestamp:0','/out:'+str(exe),str(obj),str(R/'win32/build/kernel32.lib'),str(R/'win32/build/ole32.lib'),str(R/'experimental/build/kernel32.lib')]+['/alternatename:__imp__'+n+'@'+str(k)+'=__imp__'+n for n,k in imports.items()],check=True)
        cls.fixture=exe
    @classmethod
    def tearDownClass(cls):
        # Windows can briefly retain an executable mapping after process exit.
        # Retry cleanup for at most two seconds; do not swallow persistent errors.
        for attempt in range(21):
            try:cls.tmp.cleanup();return
            except PermissionError:
                if attempt==20:raise
                time.sleep(0.1)
    def setup_profile(self,name):
        folder=self.root/(name+self._testMethodName);shutil.copytree(D/name,folder)
        original=folder/P[name]['game_exe'];shutil.copy2(self.__class__.fixture,original)
        return folder,original
    def run_launcher(self,folder,name,tail=None):
        env=os.environ.copy();env['A3D_ALPHA_FIXTURE_TOKEN']='inherited value'
        return subprocess.run([str(folder/P[name]['launcher']),*(tail or ['+alpha_probe','two words'])],cwd=self.root,env=env,capture_output=True,text=True,timeout=25)
    def test_child_activation_args_exit_and_no_game_edits(self):
        for name in P:
            folder,original=self.setup_profile(name);before=original.read_bytes()
            result=self.run_launcher(folder,name)
            self.assertEqual(result.returncode,37,result.stdout+result.stderr)
            self.assertIn('ALPHA FIXTURE PASS',result.stdout);self.assertEqual(original.read_bytes(),before)
    def test_missing_manifest_fails_before_start(self):
        name='HalfLife-Retail';folder,original=self.setup_profile(name);(folder/(original.name+'.manifest')).unlink()
        self.assertEqual(self.run_launcher(folder,name).returncode,2)
    def test_invalid_manifest_never_falls_back(self):
        name='HalfLife-Retail';folder,original=self.setup_profile(name);(folder/(original.name+'.manifest')).write_text('invalid XML')
        result=self.run_launcher(folder,name)
        # Windows may reject malformed external XML inside CreateProcess,
        # before our bootstrap can return its own activation-failure status.
        self.assertIn(result.returncode&0xffffffff,(3,0xa3d00001))
        self.assertNotIn('ALPHA FIXTURE PASS',result.stdout)
    def test_non_x86_rejected(self):
        name='Unreal-Galaxy';folder,original=self.setup_profile(name);original.write_bytes(pe_fixture(0x8664,0x20b))
        self.assertEqual(self.run_launcher(folder,name).returncode,2)
    def test_long_arguments_rejected_without_truncation(self):
        name='HalfLife-Retail';folder,_=self.setup_profile(name)
        self.assertEqual(self.run_launcher(folder,name,['X'*9000]).returncode,2)
    def test_windows_cmd_launchers_preserve_arguments(self):
        for name in P:
            folder,_=self.setup_profile(name)
            for required in P[name]['required']:
                path=folder/required
                if not path.exists():path.write_bytes(pe_fixture())
            driver=folder/'test-driver.cmd'
            driver.write_text('@echo off\ncall "'+str(folder/'RUN_A3D_WINDOWS.cmd')+'" +alpha_probe "two words"\nexit /b %errorlevel%\n')
            env=os.environ.copy();env['A3D_ALPHA_FIXTURE_TOKEN']='inherited value'
            result=subprocess.run(['cmd','/d','/c',str(driver)],env=env,capture_output=True,text=True,timeout=25)
            self.assertEqual(result.returncode,37,result.stdout+result.stderr)

if __name__=='__main__':unittest.main()
