"""Source-backed v0.6 offline smoke tests against user's actual remaster EXE.
This is not a substitute for the full-game Wine/Windows playback matrix.
"""
from __future__ import annotations
import hashlib
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'portable'))
import a3d_port as port
ORIGINAL = Path(os.environ.get('A3D_ALICE2011_EXE','/mnt/data/alice(1).exe'))

class Remaster2011Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not ORIGINAL.is_file(): raise unittest.SkipTest('Uploaded remaster not locally available')
        cls.reference = ORIGINAL.read_bytes()
        assert port.sha(cls.reference) == port.ALICE2011_SHA256
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.exe = self.dir/'alice.exe'
        self.exe.write_bytes(self.reference)
        (self.dir/'VorpalFix.ini').write_text('[General]\n')
        (self.dir/'winmm.dll').write_bytes(b'untouched VorpalFix fixture')
        drivers = self.dir/'SndDrivers';drivers.mkdir()
        (drivers/'mss32.dll').write_bytes(b'Miles fixture')
        (drivers/'mssa3d2.m3d').write_bytes(b'Miles A3D2 fixture')
        self.bin=ROOT/'portable/bin'
    def tearDown(self):self.tmp.cleanup()
    def test_exact_profile_detection(self):
        r=port.profile_report(self.exe,self.reference,'alice2011')
        self.assertFalse(r['alice2011_missing'])
        self.assertTrue(r['alice_miles_markers'])
    def test_modified_2011_exe_refused(self):
        with self.assertRaisesRegex(ValueError,'Unknown Alice 2011'):
            port.profile_report(self.exe,self.reference+b'\0','alice2011')
    def test_name_mismatch_refused(self):
        with self.assertRaisesRegex(ValueError,'requires alice.exe'):
            port.profile_report(self.dir/'other.exe',self.reference,'alice2011')
    def test_missing_vorpalfix_refused(self):
        (self.dir/'winmm.dll').unlink()
        with self.assertRaisesRegex(ValueError,'prerequisites missing'):
            port.install(self.exe,self.bin,'com','alice2011',False)
        self.assertFalse((self.dir/'a3dapi.dll').exists())
    def test_legacy_only_refused(self):
        with self.assertRaisesRegex(ValueError,'requires mode com'):
            port.install(self.exe,self.bin,'legacy','alice2011',False)
    def test_exact_exe_and_vorpalfix_untouched(self):
        oldexe=port.sha(self.exe.read_bytes());oldwinmm=port.sha((self.dir/'winmm.dll').read_bytes())
        r=port.install(self.exe,self.bin,'com','alice2011',False)
        self.assertEqual(port.sha(self.exe.read_bytes()),oldexe)
        self.assertEqual(port.sha((self.dir/'winmm.dll').read_bytes()),oldwinmm)
        self.assertTrue((self.dir/'alice-a3d2011-bridge.exe').is_file())
        self.assertTrue((self.dir/'alice.exe.manifest').is_file())
        self.assertTrue((self.dir/'a3dapi.dll').is_file())
        self.assertEqual(port.verify_or_uninstall(self.exe,False)['verified'],3)
        with self.assertRaises(FileExistsError):
            port.install(self.exe,self.bin,'com','alice2011',False)
        self.assertTrue(port.verify_or_uninstall(self.exe,True)['uninstalled'])
        self.assertFalse((self.dir/'alice-a3d2011-bridge.exe').exists())
        self.assertEqual(port.sha(self.exe.read_bytes()),oldexe)
        self.assertEqual(port.sha((self.dir/'winmm.dll').read_bytes()),oldwinmm)
    def test_preexisting_a3dapi_refused(self):
        (self.dir/'a3dapi.dll').write_bytes(b'original data')
        with self.assertRaises(FileExistsError):
            port.install(self.exe,self.bin,'com','alice2011',False)
        self.assertEqual((self.dir/'a3dapi.dll').read_bytes(),b'original data')
        self.assertFalse((self.dir/'alice-a3d2011-bridge.exe').exists())

if __name__=='__main__':unittest.main()
