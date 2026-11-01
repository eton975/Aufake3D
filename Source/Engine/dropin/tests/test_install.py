# v0.5.0 SOURCE COMMENTARY — Regression test / harness
# Exercises the release implementation or checks its ABI/packaging contract. Do not
# treat fixture success as proof of native Wine or retail-game compatibility.
"""Tests for the drop-in payload, COM manifests and safe install/uninstall."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

MODULE=Path(__file__).resolve().parents[1]/'install.py'
spec=importlib.util.spec_from_file_location('dropin_install',MODULE)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def fakepe():
    header=bytearray(512)
    header[:2]=b'MZ'
    header[0x3c:0x40]=(0x80).to_bytes(4,'little')
    header[0x80:0x84]=b'PE\0\0'
    header[0x84:0x86]=(0x14c).to_bytes(2,'little')
    header[0x98:0x9a]=(0x10b).to_bytes(2,'little')
    return bytes(header)


class InstallTests(unittest.TestCase):
    def test_manifest_structure(self):
        ns={'a':'urn:schemas-microsoft-com:asm.v1'}
        for exe in ['Alice.exe','Alice-A3D2.exe','quake3.exe']:
            root=ET.fromstring(mod.make_manifest(exe))
            self.assertEqual(root.tag,'{%s}assembly'%ns['a'])
            c=root.find('a:file/a:comClass',ns)
            self.assertEqual(c.attrib['clsid'],mod.A3D_CLSID)
            self.assertEqual(c.attrib['threadingModel'],'Both')
            self.assertEqual(root.find('a:file',ns).attrib['name'],'a3dapi.dll')
    def test_detection(self):
        self.assertTrue(mod.image_is_pe32(fakepe()))
        self.assertFalse(mod.image_is_pe32(b'not PE'))
        before=fakepe()+mod.ORIGINAL
        after=mod.patch_alice(before)
        self.assertEqual(after.count(mod.ORIGINAL),0)
        self.assertEqual(after.count(mod.PATCHED),1)
        self.assertEqual(mod.patch_alice(after),after)
        with self.assertRaises(ValueError): mod.patch_alice(fakepe())
    def test_installer_safety_and_uninstall(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            payload=root/'bin';payload.mkdir()
            for binary in ['a3d.dll','a3dapi.dll','a3d-comtest.exe']:
                (payload/binary).write_bytes(fakepe())
            exe=root/'Alice.exe';exe.write_bytes(fakepe()+mod.ORIGINAL)
            original_hash=mod.sha256(exe.read_bytes())
            paths=mod.install(exe,payload,'alice',True)
            self.assertIn(root/'Alice-A3D2.exe',paths)
            self.assertTrue((root/'Alice-A3D2.exe.manifest').exists())
            self.assertEqual(mod.sha256(exe.read_bytes()),original_hash)
            with self.assertRaises(FileExistsError):mod.install(exe,payload,'alice',True)
            (root/'a3dapi.dll').write_bytes(b'user modified')
            with self.assertRaises(ValueError):mod.uninstall(exe)
            self.assertTrue((root/'Alice-A3D2.exe').exists())
            (root/'a3dapi.dll').write_bytes(fakepe())
            removed=mod.uninstall(exe)
            self.assertIn('a3dapi.dll',removed)
            self.assertFalse((root/'Alice-A3D2.exe').exists())
            self.assertEqual(mod.sha256(exe.read_bytes()),original_hash)
    def test_quake3_gets_legacy_dll(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'bin').mkdir()
            for f in ['a3d.dll','a3dapi.dll']:
                (root/'bin'/f).write_bytes(fakepe())
            exe=root/'quake3.exe';exe.write_bytes(fakepe())
            files=mod.install(exe,root/'bin','quake3',False,False)
            self.assertIn(root/'a3d.dll',files)
            self.assertIn(root/'quake3.exe.manifest',files)
            self.assertEqual(mod.uninstall(exe),sorted([p.name for p in files]))
    def test_existing_file_not_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'bin').mkdir()
            (root/'bin'/'a3dapi.dll').write_bytes(fakepe())
            (root/'Alice.exe').write_bytes(fakepe())
            (root/'a3dapi.dll').write_bytes(b'valuable original')
            with self.assertRaises(FileExistsError):mod.install(root/'Alice.exe',root/'bin','alice',False,False)
            self.assertEqual((root/'a3dapi.dll').read_bytes(),b'valuable original')
            self.assertFalse((root/'Alice.exe.manifest').exists())

if __name__=='__main__':unittest.main()
