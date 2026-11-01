# v0.5.0 SOURCE COMMENTARY — Regression test / harness
# Exercises the release implementation or checks its ABI/packaging contract. Do not
# treat fixture success as proof of native Wine or retail-game compatibility.
import pathlib,sys,unittest,struct
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from inspect_alice import pe_imports, fingerprint
root=pathlib.Path(__file__).resolve().parent.parent
class PEChecks(unittest.TestCase):
 def test_win32_dll(self):
  p=root/'win32/build/a3dapi.dll';b=p.read_bytes();self.assertEqual(b[:2],b'MZ')
  off=struct.unpack_from('<I',b,0x3c)[0]
  self.assertEqual(struct.unpack_from('<H',b,off+4)[0],0x14c)
  self.assertEqual(struct.unpack_from('<H',b,off+24)[0],0x10b)
  self.assertEqual(pe_imports(b),['KERNEL32.dll'])
 def test_win32_exe(self):
  self.assertEqual(pe_imports((root/'win32/build/a3d-selftest.exe').read_bytes()),['KERNEL32.dll'])
 def test_original_alice(self):
  p=pathlib.Path('/mnt/data/mssa3d2.m3d')
  if p.exists():
   r=fingerprint(p);self.assertIn('ole32.dll',[x.lower() for x in r['imports']]);self.assertIn('mss32.dll',[x.lower() for x in r['imports']])
if __name__=='__main__':unittest.main()
