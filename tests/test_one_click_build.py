"""Contract checks: build orchestration and source-owned packaging assets.

These intentionally avoid building the entire engine again inside unittest.
The main one-click driver and CI invoke compilation separately.
"""
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

class OneClickBuild(unittest.TestCase):
    def test_active_v0816_release_labels(self):
        # A release bump must reach the actual packaged runtime and installer.
        self.assertIn("VERSION = '0.8.16'", (ROOT/'scripts/build.py').read_text())
        self.assertEqual(json.loads((ROOT/'packaging/Game_Kits/INSTALL_MAP.json').read_text())['version'], '0.8.16')
        self.assertIn("0.8.16", (ROOT/'packaging/Tools/aufake3d.py').read_text())
        self.assertIn("Aufake3D_v0.8.16_Local_Runtime.zip", (ROOT/'.github/workflows/source-ci.yml').read_text())
        self.assertTrue((ROOT/'Docs/GITHUB_SOURCE_INTEGRATION_V0815.md').is_file())

    def test_entrypoints_exist(self):
        for rel in ('BUILD_WINDOWS.cmd','BUILD_LINUX.sh','scripts/build.py',
                    'scripts/host_toolchain.py','Docs/ONE_CLICK_BUILD.md'):
            self.assertTrue((ROOT/rel).is_file(),rel)
    def test_game_kit_templates_are_complete_without_binaries(self):
        base=ROOT/'packaging/Game_Kits'
        j=json.loads((base/'INSTALL_MAP.json').read_text())
        self.assertEqual(set(j['profiles']),{'alice2000','alice2011','quake3','halflife'})
        for profile in j['profiles'].values():
            for filename in profile['files']:
                if filename.lower().endswith(('.dll','.exe')):
                    continue  # must be supplied by newly compiled binary
                self.assertTrue((base/profile['folder']/'COPY_TO_GAME_FOLDER'/filename).is_file(),filename)
        self.assertFalse(any(p.suffix.lower() in {'.exe','.dll'} for p in base.rglob('*') if p.is_file()))
    def test_installers_are_source_owned(self):
        for filename in ('aufake3d.py','Install-Windows.ps1'):
            self.assertTrue((ROOT/'packaging/Tools'/filename).is_file())
        self.assertTrue((ROOT/'Docs/MANUAL_INSTALLATION.md').is_file())
    def test_no_case_colliding_paths(self):
        seen={}
        for p in ROOT.rglob('*'):
            if not p.is_file():continue
            rel=p.relative_to(ROOT).as_posix()
            if 'build/' in rel or rel.startswith('dist/') or '__pycache__' in rel:
                continue
            self.assertNotIn(rel.casefold(), seen, f'Windows checkout collision: {rel} vs {seen.get(rel.casefold())}')
            seen[rel.casefold()]=rel
    def test_frozen_verification_is_opt_in(self):
        script=(ROOT/'scripts/build.py').read_text()
        self.assertIn('--strict-frozen-hashes',script)
        self.assertIn('--require-native-mock',script)
        self.assertIn('331-export',script)
    def test_windows_crt_autodiscovery_with_fixture(self):
        """Exercise Windows header and library discovery even on Linux CI.

        Create a miniature BuildTools/Windows Kits layout and simulate the
        Windows environment. This guards against the exact missing stdio.h,
        msvcrt.lib and oldnames.lib failures encountered on Windows 10.
        """
        import tempfile
        from types import SimpleNamespace
        from unittest.mock import patch
        from scripts import host_toolchain

        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            version = base/'Microsoft Visual Studio'/'2022'/'BuildTools'/'VC'/'Tools'/'MSVC'/'14.44.35000'
            lib = version/'lib'/'x64'
            inc = version/'include'
            sdk = base/'Windows Kits'/'10'
            ucrt_lib = sdk/'Lib'/'10.0.26100.0'/'ucrt'/'x64'
            win_lib = sdk/'Lib'/'10.0.26100.0'/'um'/'x64'
            sdk_inc = sdk/'Include'/'10.0.26100.0'/'ucrt'
            for folder, names in ((lib, ('msvcrt.lib','oldnames.lib')),
                                  (inc, ('vcruntime.h',)),
                                  (ucrt_lib, ('ucrt.lib',)),
                                  (win_lib, ('kernel32.lib',)),
                                  (sdk_inc, ('stdio.h',))):
                folder.mkdir(parents=True, exist_ok=True)
                for name in names:
                    (folder/name).write_bytes(b'fixture only')
            mock_os = SimpleNamespace(name='nt', pathsep=';',
                                      environ={'ProgramFiles(x86)':str(base)})
            with patch.object(host_toolchain, 'os', mock_os):
                library_dirs = host_toolchain.windows_crt_library_dirs('x64')
                header_dirs = host_toolchain.windows_crt_include_dirs()
            self.assertEqual(len(library_dirs), 3)
            self.assertIn(lib, library_dirs)
            self.assertIn(ucrt_lib, library_dirs)
            self.assertIn(win_lib, library_dirs)
            self.assertIn(inc, header_dirs)
            self.assertIn(sdk_inc, header_dirs)

    def test_windows_selects_complete_matching_msvc_not_first_cl(self):
        """Regression for 14.31 x64 compiler + ARM-only CRT vs complete 14.44.

        Run fixture on Linux too: no actual Visual Studio installation needed.
        The native Windows failure was MSVCRT.lib missing while cl.exe worked.
        """
        import tempfile
        from types import SimpleNamespace
        from unittest.mock import patch
        from scripts import host_toolchain as host
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            root=base/'Microsoft Visual Studio'/'2022'/'BuildTools'
            old=root/'VC'/'Tools'/'MSVC'/'14.31.31103'
            new=root/'VC'/'Tools'/'MSVC'/'14.44.35207'
            for ver in (old,new):
                for path in (ver/'bin'/'Hostx64'/'x64'/'cl.exe',
                             ver/'bin'/'Hostx64'/'x64'/'link.exe',
                             ver/'include'/'vcruntime.h'):
                    path.parent.mkdir(parents=True,exist_ok=True)
                    path.write_bytes(b'fixture')
            # The older toolset has ARM libraries only; no x64 CRT.
            old_arm=old/'lib'/'arm'
            old_arm.mkdir(parents=True)
            (old_arm/'msvcrt.lib').write_bytes(b'fixture')
            good_lib=new/'lib'/'x64'
            good_lib.mkdir(parents=True)
            for name in ('msvcrt.lib','oldnames.lib','vcruntime.lib'):
                (good_lib/name).write_bytes(b'fixture')
            sdk=base/'Windows Kits'/'10'
            for name in ('Lib/10.0.26100.0/ucrt/x64/ucrt.lib',
                         'Lib/10.0.26100.0/um/x64/kernel32.lib',
                         'Include/10.0.26100.0/ucrt/stdio.h'):
                dest=sdk/name
                dest.parent.mkdir(parents=True,exist_ok=True)
                dest.write_bytes(b'fixture')
            env={'ProgramFiles(x86)':str(base)}
            fake_os=SimpleNamespace(name='nt',pathsep=';',environ=env)
            with patch.object(host,'os',fake_os):
                chosen=host.windows_complete_msvc_toolset()
                self.assertIsNotNone(chosen)
                self.assertEqual(chosen.version,'14.44.35207')
                self.assertEqual(chosen.vs_root,root)
                self.assertEqual(chosen.library_dir,good_lib)
                self.assertEqual(chosen.generator,'Visual Studio 17 2022')
                self.assertEqual(host.windows_crt_library_dirs()[0],good_lib)
                self.assertEqual(host.windows_crt_include_dirs()[0],new/'include')

    def test_acoustics_pins_exact_msvc_toolset_and_instance(self):
        """Ensure the selected toolset, not an old PATH cl.exe, reaches CMake."""
        from types import SimpleNamespace
        from unittest.mock import patch
        from scripts import build,host_toolchain
        toolset=host_toolchain.WindowsCxxToolset(
            Path('C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools'),
            '14.44.35207',Path('C:/mock/cl.exe'),Path('C:/mock/lib'),
            Path('C:/mock/sdk'),'10.0.26100.0')
        calls=[]
        fake_os=SimpleNamespace(name='nt')
        with patch.object(build,'os',fake_os), \
             patch.object(build,'program',side_effect=lambda name: name), \
             patch.object(build,'windows_complete_msvc_toolset',return_value=toolset), \
             patch.object(build,'run',side_effect=lambda args,*other:calls.append([str(x) for x in args])):
            build.acoustic_tests(require=True)
        self.assertEqual(len(calls),3)
        configure=calls[0]
        self.assertIn('version=14.44.35207,host=x64',configure)
        self.assertIn('Visual Studio 17 2022',configure)
        self.assertTrue(any('CMAKE_GENERATOR_INSTANCE=' in arg for arg in configure))
        self.assertIn('-DCMAKE_TRY_COMPILE_CONFIGURATION=Release',configure)
        self.assertIn('acoustics-2022-14_44_35207',' '.join(configure))
        self.assertIn('--output-on-failure',calls[2])

    def test_acoustics_required_mode_fails_helpfully_when_incomplete(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from scripts import build
        with patch.object(build,'os',SimpleNamespace(name='nt')), \
             patch.object(build,'program',side_effect=lambda name: name), \
             patch.object(build,'windows_complete_msvc_toolset',return_value=None):
            with self.assertRaisesRegex(RuntimeError,'complete MSVC x64 compiler'):
                build.acoustic_tests(require=True)

    def test_native_mock_autodiscovery_documented(self):
        script=(ROOT/'scripts/host_toolchain.py').read_text()
        self.assertIn('vswhere',script)
        self.assertIn('oldnames.lib',script)
        self.assertIn('windows_crt_include_dirs',script)
        self.assertIn('stdio.h',script)
        self.assertIn('-isystem',script)
        self.assertIn('/LIBPATH:',script)

if __name__=='__main__':unittest.main()
