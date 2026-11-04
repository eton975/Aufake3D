"""Source-only Descent 3 adapter gating; no retail assets are needed."""
import os
import subprocess
import tempfile
import shutil
from pathlib import Path
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
INT=ROOT/'Integrations/Descent3_Source'

def adapter_clang():
 """Prefer the exact pinned compiler; never silently fall back on a bad pin."""
 pinned=os.environ.get('A3D_PINNED_CLANG')
 if pinned:
  if not Path(pinned).is_file():
   raise RuntimeError('Pinned Clang does not exist: '+pinned)
  return pinned
 # Outside pinned builds, use clang itself to compile the C++ translation
 # unit; selecting clang++ can pick an unrelated /usr/bin compiler.
 return shutil.which('clang')

class SourceAdapter(unittest.TestCase):
 def test_compiles_against_standalone_abi_shim(self):
  cc=adapter_clang()
  if not cc:self.skipTest('clang unavailable outside pinned build')
  with tempfile.TemporaryDirectory() as td:
   cmd=[cc,'-x','c++','-target','i686-pc-windows-msvc','-std=c++11',
      '-fno-exceptions','-fno-rtti','-ffreestanding',
      '-fno-stack-protector','-fno-builtin','-Wall','-Wextra','-Werror',
      '-DAUFAKE3D_ADAPTER_STANDALONE','-c',str(INT/'aufake3d_aureal.cpp'),
      '-o',str(Path(td)/'adapter.obj')]
   completed=subprocess.run(cmd,check=False,capture_output=True,text=True)
   self.assertEqual(completed.returncode,0,
                    f'Clang adapter compile failed with {cc}:\n'
                    f'{completed.stderr}\n{completed.stdout}')
 def test_adapter_compile_uses_explicit_pinned_clang_not_system_clangpp(self):
  with tempfile.TemporaryDirectory() as td:
   pinned=Path(td)/'verified-clang'
   pinned.write_bytes(b'fixture only')
   with patch.dict(os.environ,{'A3D_PINNED_CLANG':str(pinned)}), \
        patch('subprocess.run',return_value=subprocess.CompletedProcess([],0,'','')) as run:
    self.test_compiles_against_standalone_abi_shim()
   argv=run.call_args.args[0]
   self.assertEqual(argv[0],str(pinned))
   self.assertEqual(argv[argv.index('-x')+1],'c++')
   self.assertNotIn('clang++',argv[0])
 def test_missing_pinned_clang_fails_instead_of_using_system_compiler(self):
  with tempfile.TemporaryDirectory() as td:
   missing=str(Path(td)/'missing-clang')
   with patch.dict(os.environ,{'A3D_PINNED_CLANG':missing}), \
        patch('subprocess.run') as run:
    with self.assertRaisesRegex(RuntimeError,'Pinned Clang does not exist'):
     self.test_compiles_against_standalone_abi_shim()
    run.assert_not_called()
 def test_installer_refuses_unrecognised_and_is_dry_run_first(self):
  spec=__import__('importlib.util',fromlist=['spec_from_file_location'])
  sp=spec.spec_from_file_location('adapter_installer',INT/'install_into_checkout.py')
  m=spec.module_from_spec(sp);sp.loader.exec_module(m)
  with tempfile.TemporaryDirectory() as td:
   t=Path(td);p=t/'dd_sndlib';p.mkdir()
   with self.assertRaises(ValueError):m.plan(t)
   (p/'geometry.cpp').write_text('// historical geometry')
   (p/'auddev.h').write_text('header\n// #define SUPPORT_AUREAL\n')
   (p/'CMakeLists.txt').write_text('set(CPPS\n  Ds3dlib.cpp\n  ssl_lib.cpp)\n')
   paths=m.plan(t)
   self.assertEqual(len(paths),5)
   self.assertIn('#define SUPPORT_AUREAL',paths[3])
   self.assertIn('  aufake3d_aureal.cpp)',paths[4])
   self.assertNotIn('aufake3d_aureal.cpp', (p/'CMakeLists.txt').read_text())
   self.assertFalse((p/'aufake3d_aureal.cpp').exists())
 def test_adapter_does_not_declare_fake_provider_names(self):
  s=(INT/'aufake3d_aureal.cpp').read_text()
  self.assertIn('DllGetClassObject',s)
  self.assertIn('IA3d4',s)
  self.assertNotIn('WriteProcessMemory',s)
  self.assertNotIn('CreateRemoteThread',s)
  self.assertNotIn('RegSetValue',s)
if __name__=='__main__':unittest.main()
