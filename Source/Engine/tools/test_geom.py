# v0.5.0 SOURCE COMMENTARY — Regression test / harness
# Exercises the release implementation or checks its ABI/packaging contract. Do not
# treat fixture success as proof of native Wine or retail-game compatibility.
import unittest,sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from geometry_log_to_obj import read,as_obj
class GeoTest(unittest.TestCase):
 def test_triangle(self):
  log='IA3dGeom.Begin 00000003\nIA3dGeom.Vertex3f 00000000 3f800000 00000000\nIA3dGeom.Vertex3f 3f800000 00000000 00000000\nIA3dGeom.Vertex3f 00000000 00000000 3f800000\nIA3dGeom.End\n'
  tris,skipped=read(log);self.assertEqual(len(tris),1);self.assertEqual(tris[0][0],(0.,1.,0.));self.assertIn('f 1 2 3',as_obj(tris))
 def test_quad(self):
  log='IA3dGeom.Begin 00000004\n'+'IA3dGeom.Vertex3f 00000000 00000000 00000000\n'*4+'IA3dGeom.End\n'
  self.assertEqual(len(read(log)[0]),2)
if __name__=='__main__':unittest.main()
