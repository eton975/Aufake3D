"""Regression for Quake III 1.17's unusual IA3dSource.Lock call.

The source was reverse-engineered from the user's SHA256-pinned original EXE.
This test statically verifies our source rejects NULL second-region parameters
only when a lock actually wraps. Runtime probe is shipped separately for Wine.
"""
import pathlib, unittest, hashlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
SRC=(ROOT/'win32/source_probe.inc').read_text()
class Quake3LockContract(unittest.TestCase):
 def test_nullable_second_outputs(self):
  self.assertIn('if(!a||!an)return E_POINTER;',SRC)
  self.assertIn('if(b)*b=0;',SRC)
  self.assertIn('if(bn)*bn=0;',SRC)
  self.assertIn('if(bytes>first && (!b||!bn))return E_POINTER;',SRC)
  self.assertNotIn('if(!a||!an||!b||!bn)return E_POINTER;',SRC)
 def test_abi_probe(self):
  probe=(ROOT/'win32/quake3_lock_test.c').read_text()
  self.assertIn('s->vt[11]',probe)
  self.assertIn('88200,&a,&an,0,0,0',probe)
  self.assertIn('s->vt[12]',probe)
  self.assertIn('88196,8,&a,&an,0,0,0',probe)
 def test_compiled_x86(self):
  f=ROOT/'win32/build/a3d-quake3-lock-test.exe'
  self.assertEqual(f.read_bytes()[:2],b'MZ')
  import struct
  d=f.read_bytes();off=struct.unpack_from('<I',d,0x3c)[0]
  self.assertEqual(struct.unpack_from('<H',d,off+4)[0],0x14c)
if __name__=='__main__':unittest.main()
