"""Security distribution regression tests. Static checks ≠ security certification."""
import json
import os
import sys
import struct
import shutil
import tempfile
import subprocess
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from security_audit_v072 import import_table, audit_runtime, PEError
from stage_safe_candidate_v072 import stage

class SecurityV072(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime=ROOT/'runtime-v072'
        cls.payload={p.name:p.read_bytes() for p in cls.runtime.iterdir() if p.is_file()}
    def test_good_runtime_passes(self):
        report=audit_runtime(self.payload)
        self.assertTrue(report['passed'],report['issues'])
        self.assertEqual({x['file'] for x in report['files']},set(self.payload))
    def test_auditor_detects_invasive_legacy_bridge(self):
        bridge=ROOT/'experimental/build/a3d-launch.exe'
        self.assertTrue(bridge.exists())
        arch,imports=import_table(bridge.read_bytes())
        self.assertEqual(arch,'x86')
        self.assertIn('WriteProcessMemory',{x.split('!')[-1] for x in imports})
        altered=dict(self.payload);altered['a3d-direct.exe']=bridge.read_bytes()
        audit=audit_runtime(altered)
        self.assertFalse(audit['passed'])
        self.assertIn('prohibited imports',' '.join(audit['issues']))
    def test_fail_closed_if_corrupt(self):
        with self.assertRaises(PEError):import_table(b'\0'*512)
        bad=dict(self.payload);bad['a3d.dll']=b'junk'
        self.assertFalse(audit_runtime(bad)['passed'])
    def test_stage_overlay_no_modification_no_bridge(self):
        with tempfile.TemporaryDirectory() as td:
            basedir=Path(td); game=basedir/'game';game.mkdir()
            shutil.copy2(ROOT/'win32/build/a3d-selftest.exe',game/'Sample.exe')
            before={p.name:p.read_bytes() for p in game.iterdir()}
            overlay=basedir/'overlay';plan=stage(game,'Sample.exe',overlay)
            self.assertEqual(before,{p.name:p.read_bytes() for p in game.iterdir()})
            self.assertFalse(plan['server_or_anticheat_approved'])
            self.assertFalse(plan['game_directory_modified'])
            self.assertFalse(any('BRIDGE' in x.name for x in overlay.iterdir()))
            self.assertFalse((overlay/'a3d-launch.exe').exists())
            self.assertIn('a3d-direct.exe',(overlay/'RUN_A3D_WINDOWS.cmd').read_text())
            self.assertTrue((overlay/'a3d-abi-survey.exe.manifest').exists())
            with self.assertRaises(ValueError):stage(game,'Sample.exe',overlay)
            with self.assertRaises(ValueError):stage(game,'../Sample.exe',basedir/'bad')
            with self.assertRaises(ValueError):stage(game,'Sample.exe',game/'nested')
            for script in overlay.glob('*.sh'):
                subprocess.run(['bash','-n',str(script)],check=True)
    def test_mock_wine_launch_args(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td);g=base/'g';g.mkdir()
            shutil.copy2(ROOT/'win32/build/a3d-selftest.exe',g/'Sample.exe')
            overlay=base/'ovl';stage(g,'Sample.exe',overlay)
            fake=base/'wine';fake.write_text('#!/bin/sh\nprintf "[%s]\\n" "$@"\n');fake.chmod(0o755)
            env=dict(os.environ,A3D_WINE_EXECUTABLE=str(fake))
            result=subprocess.check_output(['bash',str(overlay/'RUN_A3D_WINE.sh'),'+set','name with spaces'],env=env,text=True,stderr=subprocess.DEVNULL)
            self.assertIn('[./a3d-direct.exe]',result)
            self.assertIn('[name with spaces]',result)
            self.assertIn('[Sample.exe]',result)
            survey=subprocess.check_output(['bash',str(overlay/'RUN_A3D_ABI_SURVEY_WINE.sh')],env=env,text=True)
            self.assertIn('[./a3d-abi-survey.exe]',survey)
    def test_pe_is_x86_not_recompiled_x64(self):
        for k,v in self.payload.items():
            arch,_=import_table(v)
            self.assertEqual(arch,'x86',k)

if __name__=='__main__':unittest.main()
