"""Classic Alice v0.6.0 packaging regression tests.

These are host/offline installation tests. They DO NOT substitute for actual
Alice 2000 gameplay tests under Wine and cannot validate the RAM patch against
an unknown retail executable.
"""
from pathlib import Path
import sys, tempfile, unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import a3d_port as port


def fake_exe():
    v=bytearray(300)
    v[:2]=b'MZ'
    v[60:64]=(128).to_bytes(4,'little')
    v[128:132]=b'PE\x00\x00'
    v[132:134]=(0x14c).to_bytes(2,'little')
    v[152:154]=(0x10b).to_bytes(2,'little')
    return bytes(v)+b's_milesdriver\x00Aureal A3D Interactive\x00'

class ClassicBridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.dir=Path(self.tmp.name)
        self.exe=self.dir/'alice.exe'
        self.exe.write_bytes(fake_exe())
        self.src=Path(__file__).resolve().parents[1]/'bin'
    def tearDown(self):self.tmp.cleanup()
    def test_bridge_is_x86(self):
        self.assertEqual(port.pe_info((self.src/'alice-a3d-bridge.exe').read_bytes())['architecture'],'x86')
    def test_com_install_and_uninstall(self):
        d=port.sha(self.exe.read_bytes())
        r=port.install(self.exe,self.src,'com','alice',False)
        self.assertEqual(r['receipt']['profile'],'alice')
        self.assertEqual(len(r['installed']),4)
        for f in ['alice.exe.manifest','alice-a3d-bridge.exe','alice-a3d-bridge.exe.manifest','a3dapi.dll']:
            self.assertTrue((self.dir/f).is_file(),f)
        self.assertFalse((self.dir/'alice-a3d2011-bridge.exe').exists())
        self.assertEqual(port.sha(self.exe.read_bytes()),d)
        self.assertEqual(port.verify_or_uninstall(self.exe,False)['verified'],4)
        self.assertTrue(port.verify_or_uninstall(self.exe,True)['uninstalled'])
        self.assertEqual(port.sha(self.exe.read_bytes()),d)
        self.assertFalse((self.dir/'alice-a3d-bridge.exe').exists())
    def test_both_installs_legacy_too(self):
        r=port.install(self.exe,self.src,'both','alice',False)
        self.assertEqual(len(r['installed']),5)
        self.assertTrue((self.dir/'a3d.dll').is_file())
    def test_existing_bridge_refused_without_side_effects(self):
        (self.dir/'alice-a3d-bridge.exe').write_bytes(b'USER EXISTING FILE')
        with self.assertRaises(FileExistsError):port.install(self.exe,self.src,'com','alice',False)
        self.assertEqual((self.dir/'alice-a3d-bridge.exe').read_bytes(),b'USER EXISTING FILE')
        self.assertFalse((self.dir/'a3dapi.dll').exists())
        self.assertFalse((self.dir/port.RECORD).exists())

if __name__=='__main__': unittest.main()
