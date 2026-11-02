#!/usr/bin/env python3
"""One-command Aufake3D Win32 build on native Windows 10/11 or Linux.

Default: check prerequisites, compile the freestanding x86 DLL/EXE recipe,
compile the separate Alice 2000 bridge, build and ABI-check the Miles proxy,
run source tests, optionally run available acoustics tests, and package the
four game kits plus distributable diagnostics/experimental helpers.

This intentionally does NOT install a compiler, modify a game executable,
copy proprietary Miles code, or claim that new binaries have passed gameplay
or antivirus testing. Strict historical hash checking is an explicit option.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.host_toolchain import program, native_mock_ready, windows_complete_msvc_toolset

VERSION = '0.9.0'
DIST = ROOT / 'dist'
ENGINE = ROOT / 'Source' / 'Engine'
TEMPLATES = ROOT / 'packaging' / 'Game_Kits'


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_pe32(path: Path) -> None:
    if not path.is_file():
        raise RuntimeError(f'Expected Windows component was not built: {path}')
    data = path.read_bytes()
    if len(data) < 64 or data[:2] != b'MZ':
        raise RuntimeError(f'Not a Windows executable: {path}')
    offset = int.from_bytes(data[0x3c:0x40], 'little')
    if offset + 6 > len(data) or data[offset:offset + 4] != b'PE\0\0' or int.from_bytes(data[offset + 4:offset + 6], 'little') != 0x14c:
        raise RuntimeError(f'Not 32-bit x86 Windows PE: {path}')


def run(cmd, cwd=ROOT) -> None:
    print('>', ' '.join(str(x) for x in cmd), flush=True)
    subprocess.run([str(x) for x in cmd], cwd=cwd, check=True)


def doctor() -> tuple[str, str]:
    print('Aufake3D build environment:', sys.platform, sys.version.split()[0])
    if sys.version_info < (3, 10):
        raise RuntimeError('Python 3.10 or newer is required')
    clang, ld = program('clang'), program('lld-link')
    for name, location in [('Clang', clang), ('LLD', ld), ('CMake', program('cmake')),
                           ('Ninja', program('ninja'))]:
        print(f'  {name}: {location or "not found (optional for CMake/Ninja)"}')
    if not clang or not ld:
        raise RuntimeError('Required LLVM tools missing. Install Clang and LLD; ensure their bin folder is on PATH. See Docs/ONE_CLICK_BUILD.md')
    ready, reason = native_mock_ready()
    print('  Native Miles mock:', reason if ready else 'SKIP (optional): ' + reason)
    if os.name == 'nt':
        selected = windows_complete_msvc_toolset()
        if selected:
            print(f'  CMake C++ toolset: MSVC {selected.version} ({selected.vs_root}); SDK {selected.sdk_version}')
        else:
            print('  CMake C++ toolset: no complete x64 MSVC/SDK installation (optional acoustics tests unavailable)')
    return clang, ld


def build_alice_bridge(clang: str, ld: str) -> Path:
    """Build the real checked child-process Alice 2000 bridge, not native.exe.

    The main 39-step engine recipe also creates alice-a3d2000-native.exe;
    that is a *different* experimental program and is not the release bridge.
    Reproduce Source/Engine/classic2000/build.sh without requiring Bash on Win10.
    """
    cwd = ENGINE / 'classic2000'
    run([ld, '/lib', '/def:kernel32.def', '/machine:x86', '/out:kernel32.lib'], cwd)
    run([clang, '-target', 'i686-pc-windows-msvc', '-O2', '-fno-stack-protector',
         '-fno-builtin', '-ffreestanding', '-Wall', '-Wextra', '-Werror',
         '-c', 'alice_a3d_bridge.c', '-o', 'alice_a3d_bridge.obj'], cwd)
    names = {'GetModuleFileNameA':12, 'GetCommandLineA':0, 'CreateProcessA':40,
             'ReadProcessMemory':20, 'WriteProcessMemory':20, 'VirtualAllocEx':20,
             'VirtualProtectEx':20, 'FlushInstructionCache':12, 'ResumeThread':4,
             'WaitForSingleObject':8, 'GetExitCodeProcess':8, 'TerminateProcess':8,
             'CloseHandle':4, 'GetStdHandle':4, 'WriteFile':20, 'ExitProcess':4,
             'GetThreadContext':8, 'SetThreadContext':8,
             'CreateActCtxA':4, 'ActivateActCtx':8}
    args = [ld, '/subsystem:console', '/entry:mainCRTStartup', '/nodefaultlib',
            '/machine:x86', 'alice_a3d_bridge.obj', 'kernel32.lib']
    args += [f'/alternatename:__imp__{key}@{size}=__imp__{key}' for key, size in names.items()]
    args.append('/out:alice-a3d-bridge.exe')
    run(args, cwd)
    output = cwd / 'alice-a3d-bridge.exe'
    check_pe32(output)
    return output


def add_file(contents: dict[str, bytes], name: str, path: Path):
    if name in contents:
        raise RuntimeError(f'Duplicate staged release entry: {name}')
    contents[name] = path.read_bytes()


def stage_release(proxy: Path, bridge: Path) -> Path:
    """Assemble all four installer-kit layouts from *source-owned* templates.

    Every required file listed by INSTALL_MAP.json must exist. By looking up
    compiled binaries explicitly we never accidentally ship an old .exe from
    a previous download, internal CRT stub, or the excluded self-test.
    """
    core = DIST / 'core'
    builds = {
        'a3d.dll': core / 'a3d.dll',
        'a3dapi.dll': core / 'a3dapi.dll',
        'mss32.dll': proxy,
        'alice-a3d-bridge.exe': bridge,
        'alice-a3d2011-native.exe': ENGINE/'remaster2011/alice-a3d2011-native.exe',
        'halflife-a3d-alpha.exe': ENGINE/'experimental/build/halflife-a3d-alpha.exe',
        'quake3-a3d-native.exe': ENGINE/'native/quake3-a3d-native.exe',
        'unreal-a3d-alpha.exe': ENGINE/'experimental/build/unreal-a3d-alpha.exe',
        'a3d-launch.exe': ENGINE/'experimental/build/a3d-launch.exe',
        'a3d-comtest.exe': ENGINE/'win32/build/a3d-comtest.exe',
        'a3d-miles-enum.exe': ENGINE/'win32/build/a3d-miles-enum.exe',
        'a3d-miles-open.exe': ENGINE/'win32/build/a3d-miles-open.exe',
    }
    for component in builds.values():
        check_pe32(component)
    contents: dict[str, bytes] = {}
    for p in sorted(TEMPLATES.rglob('*')):
        if p.is_file():
            add_file(contents, 'Game_Kits/'+p.relative_to(TEMPLATES).as_posix(), p)
    install_map = json.loads((TEMPLATES/'INSTALL_MAP.json').read_text())
    for profile in install_map['profiles'].values():
        prefix = 'Game_Kits/' + profile['folder'] + '/COPY_TO_GAME_FOLDER/'
        for relative in profile['files']:
            key = prefix + relative
            if key in contents:
                continue
            basename = Path(relative).name
            if basename not in builds:
                raise RuntimeError(f'Installer map references an unknown component: {key}')
            add_file(contents, key, builds[basename])
        missing = [rel for rel in profile['files'] if prefix+rel not in contents]
        if missing:
            raise RuntimeError(f'Incomplete kit {profile["folder"]}: {missing}')
    # Installer utilities are plain independently authored source scripts.
    # Keep them in packaging/Tools so even a source-only clone can assemble
    # an installer-ready runtime without downloading a previous binary ZIP.
    for source in sorted((ROOT/'packaging/Tools').rglob('*')):
        if source.is_file():
            add_file(contents, 'Tools/'+source.relative_to(ROOT/'packaging/Tools').as_posix(), source)
    add_file(contents, 'Tools/check_game_identity.py', ROOT/'Tools/check_game_identity.py')
    for name in ('a3d.dll','a3dapi.dll'):
        add_file(contents, 'Universal_Core/'+name, builds[name])
    for name in ('a3d-comtest.exe','a3d-miles-enum.exe','a3d-miles-open.exe'):
        add_file(contents, 'Extras/Diagnostics/'+name, builds[name])
    for name in ('a3d-launch.exe','quake3-a3d-native.exe','unreal-a3d-alpha.exe'):
        add_file(contents, 'Extras/Experimental/'+name, builds[name])
    for name in ('LICENSE','LICENSE_SCOPE.md','LICENSE_STATUS.md','THIRD_PARTY_NOTICES.md',
                 'SECURITY_RELEASE_REVIEW.md','README.md'):
        add_file(contents, name, ROOT/name)
    for name in ('MANUAL_INSTALLATION.md','EASY_INSTALL_WINDOWS.md',
                 'Aufake3D_v0.8.18_Quick_Start.pdf','SECURITY_REVIEW_V0814_RC1.md','AU8830_HRTF_PERFORMANCE_MODES.md','GAME_COMPATIBILITY_V090.md'):
        p=ROOT/'Docs'/name
        if p.is_file():add_file(contents, 'Docs/'+name, p)
    add_file(contents, 'START_HERE.txt', ROOT/'START_HERE.txt')
    contents['LOCAL_BUILD_WARNING.txt'] = ('''
Aufake3D locally compiled runtime — NOT a tested official release.
Windows PE32 x86 components compiled from source on this machine.
The Miles DLL requires the original game-owned Miles DLL at runtime.
Do not substitute a locally rebuilt proxy into a working Alice 2011 setup
without separate functionality tests. Process-memory-modifying helpers
remain experimental and need independent antivirus/security review.
Source repository: https://github.com/eton975/Aufake3D
'''.lstrip()).encode('utf-8')
    # Generate checksums for this exact local package, not frozen RC hashes.
    checksums = {path:hashlib.sha256(data).hexdigest() for path,data in sorted(contents.items())}
    contents['LOCAL_BUILD_SHA256.json'] = (json.dumps({'version': VERSION,
        'kind':'unverified-local-runtime', 'sha256':checksums},indent=2,sort_keys=True)+'\n').encode()
    filename = DIST/f'Aufake3D_v{VERSION}_Local_Runtime.zip'
    DIST.mkdir(exist_ok=True)
    with zipfile.ZipFile(filename, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=8) as archive:
        for rel,data in sorted(contents.items()):
            info = zipfile.ZipInfo('Aufake3D-v'+VERSION+'-Local/'+rel, date_time=(2026,1,1,0,0,0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = ((0o755 if rel.endswith('.sh') else 0o644) << 16)
            archive.writestr(info, data)
    with zipfile.ZipFile(filename) as archive:
        bad=archive.testzip()
        if bad:raise RuntimeError('Release archive failed integrity check: '+bad)
    print('Runtime ZIP assembled:', filename)
    print('Entries:',len(contents),'| SHA-256:',digest(filename))
    return filename


def acoustic_tests(require: bool = False) -> None:
    """Build optional acoustics tests using a *complete* matching toolchain.

    On Windows, Visual Studio/CMake otherwise sometimes chooses the oldest
    installed cl.exe (14.31) despite its x64 CRT libraries being missing while
    14.44 is complete. Explicit toolset version and VS instance selection
    prevents `LNK1104: cannot open MSVCRT.lib`/`MSVCRTD.lib`. A per-toolset
    CMake directory prevents stale failed generator cache from poisoning the
    next build. Do not overwrite PATH, LIB or the developer's machine.
    """
    cmake, ninja = program('cmake'), program('ninja')
    if not cmake:
        msg = 'Acoustics C++ tests: SKIPPED (CMake not installed; see Docs/ONE_CLICK_BUILD.md)'
        if require: raise RuntimeError(msg)
        print(msg)
        return
    if os.name == 'nt':
        toolset = windows_complete_msvc_toolset('x64')
        if not toolset:
            msg = ('Acoustics C++ tests: SKIPPED (no complete MSVC x64 compiler, '
                   'matching CRT libraries and Windows SDK; see Docs/ONE_CLICK_BUILD.md)')
            if require: raise RuntimeError(msg)
            print(msg)
            return
        # VS generator supports -T version=<full-toolset-version>; do not use
        # whichever old cl.exe happens to be on the Developer Shell PATH.
        generator = ['-G',toolset.generator,'-A','x64',
                     '-T',f'version={toolset.version},host=x64',
                     '-DCMAKE_GENERATOR_INSTANCE='+str(toolset.vs_root),
                     '-DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreadedDLL',
                     '-DCMAKE_TRY_COMPILE_CONFIGURATION=Release']
        configuration=['--config','Release']
        build_dir = ROOT/'build'/('acoustics-'+toolset.vs_root.parent.name+'-'+toolset.version.replace('.','_'))
        print('Acoustics C++: selected complete MSVC',toolset.version,
              'with SDK',toolset.sdk_version, '(not first cl.exe on PATH)')
    else:
        if not ninja or not (program('c++') or program('clang++')):
            msg = 'Acoustics C++ tests: SKIPPED (install Ninja and C++ compiler to enable)'
            if require: raise RuntimeError(msg)
            print(msg)
            return
        generator=['-G','Ninja']
        configuration=[]
        build_dir=ROOT/'build'/'acoustics'
    run([cmake,'-S',ENGINE/'acoustics','-B',build_dir,*generator])
    run([cmake,'--build',build_dir,*configuration])
    run([program('ctest') or 'ctest','--test-dir',build_dir,*(['-C','Release'] if os.name=='nt' else []),'--output-on-failure'])


def main():
    parser=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--doctor',action='store_true',help='Check tools only; do not compile')
    parser.add_argument('--no-tests',action='store_true',help='Skip Python regression tests')
    parser.add_argument('--no-acoustics',action='store_true',help='Skip optional C++ acoustics tests')
    parser.add_argument('--require-acoustics',action='store_true',help='Fail instead of skipping when CMake/MSVC C++ tests cannot be run')
    parser.add_argument('--no-package',action='store_true',help='Compile components but do not assemble the ZIP')
    parser.add_argument('--strict-frozen-hashes',action='store_true',help='Require exact reference core and proxy bytes (release auditing only)')
    parser.add_argument('--require-native-mock',action='store_true',help='Fail if Windows CRT mock prerequisites are missing instead of skipping')
    args=parser.parse_args()
    try:
        clang,ld=doctor()
        if args.doctor:return 0
        if args.require_native_mock and not native_mock_ready()[0]:
            raise RuntimeError(native_mock_ready()[1])
        run([sys.executable,ROOT/'Tools/generate_vortex2_hrtf.py','--check'])
        print('\n[1/5] Building core and experimental utilities')
        run([sys.executable, ROOT/'scripts/build_engine.py','--clang',clang,'--linker',ld])
        print('\n[2/5] Building original Alice 2000 bridge')
        bridge=build_alice_bridge(clang,ld)
        print('\n[3/5] Building 331-export Miles proxy')
        proxy_dir=DIST/'miles-local'
        cmd=[sys.executable,ROOT/'Source/Alice2011_NameFix_v089/build_proxy_from_export_map.py',
             '--output',proxy_dir]
        if args.strict_frozen_hashes:cmd.append('--strict-frozen-hash')
        run(cmd)
        proxy=proxy_dir/'mss32.dll'
        check_pe32(proxy)
        if args.strict_frozen_hashes:
            run([sys.executable, ROOT/'Tools/check_core_binary_hashes.py'])
        print('\n[4/5] Running regression tests')
        if not args.no_tests:
            run([sys.executable,'-m','unittest','discover','-s','tests','-v'])
        else:print('Python tests explicitly skipped')
        if args.require_acoustics and args.no_acoustics:
            raise RuntimeError('--require-acoustics cannot be combined with --no-acoustics')
        if not args.no_acoustics:acoustic_tests(require=args.require_acoustics)
        print('\n[5/5] Assembling complete game kits')
        if not args.no_package:stage_release(proxy,bridge)
        else:print('Packaging explicitly skipped')
        print('\nBUILD COMPLETED. Outputs under:',DIST)
        print('These are UNVERIFIED local binaries; test with Windows/Wine before deploying or publishing.')
        return 0
    except (RuntimeError,subprocess.CalledProcessError,OSError) as exc:
        print('\nBUILD FAILED:',exc, file=sys.stderr)
        print('See Docs/ONE_CLICK_BUILD.md; try: python scripts/build.py --doctor',file=sys.stderr)
        return 1


if __name__=='__main__':
    sys.exit(main())
