"""Tests that do not require a retail game, vendor Miles DLL or frozen runtime ZIP."""
import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from scripts.host_toolchain import native_mock_ready, compile_native_mock
import unittest

ROOT=Path(__file__).resolve().parents[1]

class SourceSmoke(unittest.TestCase):
    def test_source_snapshot_present(self):
        for p in ['Source/Engine/win32/a3dapi.c','Source/Engine/win32/a3d_legacy_bridge.c',
                  'Source/Alice2011_NameFix_v089/miles_selection_v089.c',
                  'Source/Engine/acoustics/src/acoustics.cpp']:
            self.assertTrue((ROOT/p).is_file(),p)

    def test_no_proprietary_vendor_dlls_shipped(self):
        # This is the unified runtime+source distribution, so release binaries are expected.
        forbidden={'a3d_mss_real.dll','mssa3d2.m3d','winmm.dll','mss32-original.dll'}
        names={p.name.lower() for p in ROOT.rglob('*') if p.is_file() and not ({'build','dist'} & set(p.relative_to(ROOT).parts))}
        self.assertFalse(names & forbidden, sorted(names & forbidden))

    def test_miles_builder_starts(self):
        r=subprocess.run([sys.executable,str(ROOT/'Source/Alice2011_NameFix_v089/build_scoped_proxy_v089.py'),'--help'],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertIn('--original',r.stdout)

    def test_actual_trace_parser(self):
        p=ROOT/'Tools/check_game_identity.py'
        spec=importlib.util.spec_from_file_location('audit',p)
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        trace=(ROOT/'release_tests/fixtures/v089_alice2011_actual_trace_redacted.txt').read_text()
        r=mod.trace_evidence(trace)
        self.assertTrue(r['provider_verified'])
        self.assertTrue(r['name_upgrade_logged'])
        self.assertFalse(mod.trace_evidence(trace.replace('AIL_OPEN_BEGIN_PROVIDER 0x00000004','AIL_OPEN_BEGIN_PROVIDER 0x00000009'))['provider_verified'])

    def test_original_proxy_source_native_mock(self):
        """Exercise the real C provider-selection implementation on the host.

        Unlike the freestanding Win32 A3D DLL build, this test uses stdio and
        the host C runtime. On Windows, discover MSVC/SDK libraries explicitly
        so users need not launch a specially configured Developer PowerShell.
        """
        ready, explanation = native_mock_ready()
        if not ready:
            self.skipTest('Optional native mock: ' + explanation)
        source = ROOT/'Source/NameFix_Tests/mock_v089_namefix_native.c'
        with tempfile.TemporaryDirectory() as tmp:
            exe = Path(tmp)/('namefix_mock.exe' if sys.platform == 'win32' else 'namefix_mock')
            build = compile_native_mock(source, exe)
            self.assertEqual(
                build.returncode, 0,
                'Native mock compile/link failed (exit {}):\n'
                'Command: {}\n'
                '--- Compiler/linker stdout ---\n{}\n'
                '--- Compiler/linker stderr ---\n{}\n'
                'See Docs/ONE_CLICK_BUILD.md for compiler prerequisites.'.format(
                    build.returncode,
                    ' '.join(map(str, build.args)),
                    build.stdout or '<empty>',
                    build.stderr or '<empty>'))
            r = subprocess.run([str(exe)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn('PASS v089', r.stdout)
if __name__=='__main__':unittest.main()
