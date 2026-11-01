"""Deterministic generic compatibility staging tests: no games are executed.

The test binary is a repository-built Win32 PE fixture, not a commercial game.
"""
import json
import os
import subprocess
import shutil
import struct
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from scan_a3d_clients import scan
from stage_generic_candidate import stage


class GenericV071(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='a3d-v071-generic-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.game = self.root / 'Game'
        self.game.mkdir()
        self.fixture = ROOT / 'win32/build/a3d-selftest.exe'
        self.assertTrue(self.fixture.exists(), 'v0.7.0 PE fixture missing')
        shutil.copy2(self.fixture, self.game / 'Sample.exe')

    def test_stage_no_game_changes_and_survey(self):
        before = sorted((p.name,p.read_bytes()) for p in self.game.iterdir())
        overlay = self.root / 'Overlay'
        result = stage(self.game, 'Sample.exe', overlay)
        self.assertFalse(result['game_directory_modified'])
        self.assertEqual(before, sorted((p.name,p.read_bytes()) for p in self.game.iterdir()))
        for name in ('a3dapi.dll', 'a3d.dll', 'a3d-launch.exe', 'a3d-direct.exe',
                     'a3d-abi-survey.exe','a3d-abi-survey.exe.manifest',
                     'RUN_A3D_DIRECT_WINDOWS.cmd','RUN_A3D_DIRECT_WINE.sh',
                     'RUN_A3D_BRIDGE_WINDOWS.cmd','RUN_A3D_BRIDGE_WINE.sh',
                     'RUN_A3D_ABI_SURVEY_WINDOWS.cmd','RUN_A3D_ABI_SURVEY_WINE.sh'):
            self.assertTrue((overlay/name).is_file(),name)
        for ext in ('.cmd','.sh'):
            self.assertNotIn('A3D_HALFLIFE_SPLASH_FIX=1', '\n'.join(
                p.read_text() for p in overlay.glob('*'+ext)))
        self.assertIn('6', (overlay/'RUN_A3D_WINDOWS.cmd').read_text())
        self.assertIn('a3d-direct.exe', (overlay/'RUN_A3D_WINDOWS.cmd').read_text())
        self.assertIn('a3d-launch.exe', (overlay/'RUN_A3D_BRIDGE_WINDOWS.cmd').read_text())
        self.assertIn('A3D_WEAPON_CLARITY="${A3D_WEAPON_CLARITY:-0}"', (overlay/'RUN_A3D_WINE.sh').read_text())
        self.assertIn('a3d-direct.exe', (overlay/'RUN_A3D_WINDOWS.cmd').read_text())
        self.assertIn('a3d-launch.exe', (overlay/'RUN_A3D_BRIDGE_WINDOWS.cmd').read_text())
        self.assertIn('exec "${A3D_WINE_EXECUTABLE:-wine}" ./"Sample.exe" "$@"',
                      (overlay/'RUN_A3D_DIRECT_WINE.sh').read_text())
        self.assertIn('--game "a3d-abi-survey.exe" --',
                      (overlay/'RUN_A3D_ABI_SURVEY_WINE.sh').read_text())
        self.assertFalse(result['static_a3d_scan']['requires_unimplemented_a3d3'])

    def test_low_invasive_import_contract(self):
        # Static PE imports only. Runtime antivirus or anti-cheat approval is
        # explicitly NOT asserted by this test.
        import shutil
        readobj=shutil.which('objdump')
        if not readobj:self.skipTest('objdump required')
        direct=ROOT/'experimental/build/a3d-direct.exe'
        bridge=ROOT/'experimental/build/a3d-launch.exe'
        a=subprocess.check_output([readobj,'-p',str(direct)],text=True)
        b=subprocess.check_output([readobj,'-p',str(bridge)],text=True)
        for forbidden in ('WriteProcessMemory','VirtualAllocEx','VirtualProtectEx',
                          'GetThreadContext','SetThreadContext','ResumeThread'):
            self.assertNotIn('  '+forbidden+'\n',a)
        self.assertIn('CreateProcessA',a)
        self.assertIn('WriteProcessMemory',b)

    def test_mock_wine_direct_vs_bridge_and_args(self):
        overlay=self.root/'Overlay';stage(self.game,'Sample.exe',overlay)
        fake=self.root/'fake-wine'
        fake.write_text('#!/bin/sh\nprintf "<%s>\\n" "$@"\n')
        fake.chmod(0o755)
        env=os.environ.copy();env['A3D_WINE_EXECUTABLE']=str(fake)
        for script,exe in [('RUN_A3D_WINE.sh','./a3d-direct.exe'),
                           ('RUN_A3D_BRIDGE_WINE.sh','./a3d-launch.exe')]:
            output=subprocess.check_output(['bash',str(overlay/script),'+set','name with spaces'],
                text=True,env=env,cwd=self.root,stderr=subprocess.DEVNULL)
            self.assertIn('<'+exe+'>',output)
            self.assertIn('<name with spaces>',output)
            self.assertIn('<Sample.exe>',output)

    def test_analyse_explicit_a3d3_guid(self):
        binary = (self.game/'Sample.exe').read_bytes()
        # Static analysis only; a trailing GUID is evidence, not proof of code usage.
        (self.game/'Sample.exe').write_bytes(binary + uuid.UUID(
            '9ae07221-8ac4-11d3-b6aa-00600879f3ee').bytes_le)
        info = scan(self.game,0)
        self.assertTrue(info['summary']['requires_unimplemented_a3d3'])
        self.assertIn('A3D3', info['summary']['generations_with_static_evidence'])
        self.assertEqual(info['files'][0]['route'],
                         'a3d3_extension_detected_requires_implementation')
        self.assertFalse(info['gameplay_verified'])

    def test_unknown_target_is_refused(self):
        with self.assertRaises(ValueError):
            stage(self.game,'../Sample.exe',self.root/'nope')
        with self.assertRaises(ValueError):
            stage(self.game,'a3d-launch.exe',self.root/'nope')
        with self.assertRaises(ValueError):
            stage(self.game,'Sample.exe',self.game/'nested')

    def test_executable_is_pe32_and_no_synthetic_game_compatibility_claim(self):
        p=ROOT/'win32/build/a3d-abi-survey.exe'
        data=p.read_bytes()
        off=struct.unpack_from('<I',data,0x3c)[0]
        self.assertEqual(data[off:off+4],b'PE\x00\x00')
        self.assertEqual(struct.unpack_from('<H',data,off+4)[0],0x14c)
        self.assertIn(b'IA3d5 (A3D3)', data)
        self.assertIn(b'not game compatibility proof',data)

if __name__=='__main__':unittest.main()
