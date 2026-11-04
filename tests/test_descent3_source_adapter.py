"""Source-only Descent 3 adapter gating; no retail assets are needed."""
import subprocess
import tempfile
import shutil
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
INT=ROOT/'Integrations/Descent3_Source'

class SourceAdapter(unittest.TestCase):
 def test_compiles_against_standalone_abi_shim(self):
  cc=shutil.which('clang++')
  if not cc:self.skipTest('clang++ unavailable')
  with tempfile.TemporaryDirectory() as td:
   subprocess.run([cc,'-target','i686-pc-windows-msvc','-std=c++11',
      '-fno-exceptions','-fno-rtti','-ffreestanding',
      '-fno-stack-protector','-fno-builtin','-Wall','-Wextra','-Werror',
      '-DAUFAKE3D_ADAPTER_STANDALONE','-c',str(INT/'aufake3d_aureal.cpp'),
      '-o',str(Path(td)/'adapter.obj')],check=True,capture_output=True)
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
