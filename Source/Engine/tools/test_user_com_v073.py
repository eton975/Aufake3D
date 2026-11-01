"""Non-invasive A3D2 user-COM installer build and packaging tests.

These are OFFLINE structural and safety tests, not Windows/Wine COM execution.
"""
from __future__ import annotations
import sys,unittest,tempfile,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from security_audit_v072 import import_table, RESTRICTED
from stage_safe_candidate_v072 import stage

class PerUserActivation(unittest.TestCase):
    def test_helper_pe32_with_registry_imports_but_no_remote_process_apis(self):
        blob=(ROOT/'win32/build/a3d-com-user.exe').read_bytes()
        arch,imports=import_table(blob)
        self.assertEqual(arch,'x86')
        names={s.split('!')[-1] for s in imports}
        self.assertTrue({'RegOpenKeyExA','RegSetValueExA','RegDeleteValueA','RegDeleteKeyA','RegEnumValueA','RegCloseKey'}<=names)
        self.assertFalse({s for s in names if s.casefold() in RESTRICTED})
        self.assertNotIn('GetProcAddress',names)
    def test_no_silent_registration_overwrite_and_user_scope(self):
        src=(ROOT/'win32/a3d_user_com.c').read_text()
        self.assertIn('#define HKCU',src)
        self.assertNotIn('HKEY_LOCAL_MACHINE',src)
        self.assertIn('REFUSED: a COM registration already exists',src)
        self.assertIn('REFUSED: a per-user A3D CLSID key exists',src)
        self.assertIn('A3DUserRegistrationOwner',src)
        self.assertIn('REFUSED: unknown registry values present',src)
        self.assertIn('RegEnumValueA',src)
        self.assertIn('--remove',src)
        self.assertIn('KEY_WOW64_32KEY',src)
    def test_existing_engine_unchanged(self):
        for n in ['a3d.dll','a3dapi.dll','a3d-direct.exe','a3d-abi-survey.exe']:
            self.assertEqual((ROOT/'runtime-v072'/n).read_bytes(),(ROOT/'runtime-v073'/n).read_bytes())
    def test_existing_generic_staging_unmodified(self):
        with tempfile.TemporaryDirectory() as t:
            t=Path(t);game=t/'game';game.mkdir()
            shutil.copyfile(ROOT/'win32/build/a3d-selftest.exe',game/'Demo.exe')
            original=(game/'Demo.exe').read_bytes()
            ov=t/'overlay';plan=stage(game,'Demo.exe',ov)
            self.assertEqual((game/'Demo.exe').read_bytes(),original)
            self.assertFalse(plan['server_or_anticheat_approved'])
            self.assertNotIn('a3d-com-user.exe',{p.name for p in ov.iterdir()})
            self.assertNotIn('a3d-launch.exe',{p.name for p in ov.iterdir()})
    def test_verify_shell_script_syntax(self):
        for p in (ROOT/'runtime-v073').glob('*.sh'):
            subprocess.run(['bash','-n',str(p)],check=True)

if __name__=='__main__':unittest.main()
