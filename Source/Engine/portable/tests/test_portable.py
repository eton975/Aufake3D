# v0.5.0 SOURCE COMMENTARY — Regression test / harness
# Exercises the release implementation or checks its ABI/packaging contract. Do not
# treat fixture success as proof of native Wine or retail-game compatibility.
import json
from pathlib import Path
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import a3d_port as port


def fake_pe(signature=b'',x64=False):
    data=bytearray(b'\0'*300)
    data[:2]=b'MZ';data[60:64]=(128).to_bytes(4,'little')
    data[128:132]=b'PE\0\0'
    data[132:134]=(0x8664 if x64 else 0x14c).to_bytes(2,'little')
    data[152:154]=(0x20b if x64 else 0x10b).to_bytes(2,'little')
    return bytes(data)+signature


class PortableTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.bin=self.root/'bin';self.bin.mkdir()
        for name in ('a3d.dll','a3dapi.dll','a3d-legacy-probe.exe','a3d-comtest.exe'):
            (self.bin/name).write_bytes(fake_pe())
        self.exe=self.root/'game.exe';self.exe.write_bytes(fake_pe(b'CoCreateInstance a3dapi.dll'))
        self.digest=port.sha(self.exe.read_bytes())
    def tearDown(self): self.tmp.cleanup()
    def test_generic_both_install_verify_uninstall(self):
        r=port.install(self.exe,self.bin,'both','generic')
        self.assertEqual(r['receipt']['game_sha256'],self.digest)
        self.assertEqual(len(r['installed']),6)
        self.assertEqual(port.verify_or_uninstall(self.exe,False)['verified'],6)
        self.assertTrue((self.root/'a3dapi.dll').is_file())
        self.assertTrue((self.root/'a3d.dll').is_file())
        self.assertEqual(self.digest,port.sha(self.exe.read_bytes()))
        self.assertTrue(port.verify_or_uninstall(self.exe,True)['uninstalled'])
        self.assertEqual(self.digest,port.sha(self.exe.read_bytes()))
        self.assertFalse((self.root/'a3d.dll').exists())
    def test_modes(self):
        port.install(self.exe,self.bin,'legacy','generic')
        self.assertFalse((self.root/'a3dapi.dll').exists())
        port.verify_or_uninstall(self.exe,True)
        port.install(self.exe,self.bin,'com','generic')
        self.assertFalse((self.root/'a3d.dll').exists())
        port.verify_or_uninstall(self.exe,True)
    def test_existing_dll_never_overwritten(self):
        (self.root/'a3d.dll').write_bytes(b'user-data')
        with self.assertRaises(FileExistsError):port.install(self.exe,self.bin,'both','generic')
        self.assertEqual((self.root/'a3d.dll').read_bytes(),b'user-data')
        self.assertFalse((self.root/'a3dapi.dll').exists())
    def test_modified_dll_prevents_partial_uninstall(self):
        port.install(self.exe,self.bin,'both','generic')
        (self.root/'a3d.dll').write_bytes(b'tampered')
        with self.assertRaises(ValueError):port.verify_or_uninstall(self.exe,True)
        self.assertTrue((self.root/'a3dapi.dll').exists())
    def test_game_edit_prevents_uninstall(self):
        port.install(self.exe,self.bin,'both','generic')
        self.exe.write_bytes(self.exe.read_bytes()+b'changed')
        with self.assertRaises(ValueError):port.verify_or_uninstall(self.exe,True)
    def test_quake3_not_alice_renamed(self):
        q3=self.root/'quake3.exe'
        q3.write_bytes(fake_pe(b'Aureal A3D Interactive\0s_milesdriver'))
        with self.assertRaisesRegex(ValueError,'Alice/Miles'):
            port.install(q3,self.bin,'both','quake3')
    def test_quake3_profile_reports_a3d_markers(self):
        q3=self.root/'quake3.exe';q3.write_bytes(fake_pe(b's_enable_a3d\0s_usingA3D'))
        self.assertTrue(port.profile_report(q3,q3.read_bytes(),'quake3')['quake3_a3d_markers'])
        port.install(q3,self.bin,'both','quake3')
        self.assertTrue((self.root/'quake3.exe.manifest').exists())
    def test_x64_refused(self):
        self.exe.write_bytes(fake_pe(x64=True))
        with self.assertRaisesRegex(ValueError,'32-bit'):
            port.install(self.exe,self.bin,'both','generic')
    def test_manifest_class(self):
        b=port.manifest('test game.exe')
        root=ET.fromstring(b)
        self.assertEqual(root.tag,'{%s}assembly'%port.NS)
        child=root.find('.//{%s}comClass'%port.NS)
        self.assertEqual(child.attrib['clsid'],port.GUID)
    def test_no_probes(self):
        r=port.install(self.exe,self.bin,'both','generic',tools=False)
        self.assertEqual(len(r['installed']),3)
    def test_cli_inspect_no_edit(self):
        self.assertEqual(port.main(['inspect',str(self.exe)]),0)
        self.assertEqual(port.sha(self.exe.read_bytes()),self.digest)

if __name__ == '__main__':unittest.main()
