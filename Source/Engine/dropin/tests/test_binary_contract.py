# v0.5.0 SOURCE COMMENTARY — Regression test / harness
# Exercises the release implementation or checks its ABI/packaging contract. Do not
# treat fixture success as proof of native Wine or retail-game compatibility.
"""Binary ABI checks: no Wine runtime required for these tests."""
from pathlib import Path
import subprocess
import shutil
import unittest
import importlib.util

TOP=Path(__file__).resolve().parents[2]
BINS=TOP/'dropin'/'bin'
OBJDUMP=shutil.which('objdump') or shutil.which('llvm-objdump') or 'objdump'
spec=importlib.util.spec_from_file_location('dropin_install',TOP/'dropin'/'install.py')
lib=importlib.util.module_from_spec(spec)
spec.loader.exec_module(lib)

class BinaryContract(unittest.TestCase):
    def test_required_pe32(self):
        for name in ('a3dapi.dll','a3d.dll','a3d-comtest.exe'):
            self.assertTrue(lib.image_is_pe32((BINS/name).read_bytes()),name)
    def test_legacy_exports_are_real_historical_names(self):
        result=subprocess.run([OBJDUMP,'-p',str(BINS/'a3d.dll')],check=True,capture_output=True,text=True)
        for name in ('_A3dCreate@12','DllGetClassObject','DllCanUnloadNow','DllRegisterServer','DllUnregisterServer'):
            self.assertIn(name,result.stdout)
        # A3D's historical 2041 legacy DLL assigned ordinal 6 to A3dCreate.
        # GNU and LLVM print export ordinals in different formats.
        if 'Ordinal base:' in result.stdout:
            self.assertRegex(result.stdout, r'(?m)^\s*6\s+0x[0-9a-fA-F]+\s+_A3dCreate@12\s*$')
        else:
            self.assertIn('+base[   6]',result.stdout)
    def test_a3dapi_exports_com(self):
        result=subprocess.run([OBJDUMP,'-p',str(BINS/'a3dapi.dll')],check=True,capture_output=True,text=True)
        for name in ('DllGetClassObject','DllCanUnloadNow'):
            self.assertIn(name,result.stdout)
    def test_win_scripts_and_fresh_prefix(self):
        setup=(TOP/'dropin'/'install_windows.ps1').read_text()
        for needle in ('CreateNew','PatchAlice','Alice-A3D2.exe','a3dapi.dll'):
            self.assertIn(needle,setup)
        test=(TOP/'dropin'/'test_regfree_wine.sh').read_text()
        self.assertIn('mktemp -d',test)
        self.assertNotIn('wine reg ',test)
        self.assertNotIn('reg32.exe',test)

if __name__=='__main__':unittest.main()
