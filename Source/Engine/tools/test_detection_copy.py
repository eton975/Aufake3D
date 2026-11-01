# v0.5.0 SOURCE COMMENTARY — Regression test / harness
# Exercises the release implementation or checks its ABI/packaging contract. Do not
# treat fixture success as proof of native Wine or retail-game compatibility.
from pathlib import Path
import importlib.util
import unittest
file=Path(__file__).parent/'alice_detection_copy.py'
spec=importlib.util.spec_from_file_location('alice_detection_copy',file)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
class DetectionCopyTests(unittest.TestCase):
 def test_synthetic_exact(self):
  original=b'MZ'+b'\0'*64+m.ORIGINAL+b'\0'*64
  patched=m.patch(original)
  self.assertEqual(len(original),len(patched))
  self.assertEqual(patched[66:66+len(m.PATCHED)],m.PATCHED)
  self.assertEqual(m.inspect(patched),(0,1))
 def test_reject_mismatched_or_ambiguous_binary(self):
  for data in (b'wrong',m.ORIGINAL*2,m.PATCHED,m.ORIGINAL+m.PATCHED):
   with self.assertRaises(ValueError):m.patch(data)
if __name__=='__main__':unittest.main()
