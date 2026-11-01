"""Host-toolchain discovery shared by the one-click build and native mock test.

The A3D engine itself is freestanding PE32 and needs only Clang/LLD.
The *host-native* Miles mock uses stdio.h and the Microsoft CRT on Windows.
A Developer PowerShell may supply LIB, but a fresh terminal often does not;
resolve the actual library directories rather than depending on shell state.
This module never changes the user's system PATH or installs software.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
import sys


def program(name: str) -> str | None:
    return shutil.which(name) or (shutil.which(name + '.exe') if os.name == 'nt' else None)


def _version_key(path: Path):
    try:
        return tuple(int(part) for part in path.name.split('.'))
    except ValueError:
        return (0,)


def _existing_dirs(paths):
    return [p for p in paths if p.is_dir()]


def _windows_install_roots() -> tuple[list[Path], list[Path]]:
    """Find VS and SDK installations without assuming a Developer PowerShell.

    VS 2022 can live under Program Files (x86), Program Files, or a custom
    location returned by Microsoft's vswhere utility. Never hard-code an
    MSVC version or assume that LLVM's directory is the MSVC directory.
    """
    vsroots = [Path(os.environ['VSINSTALLDIR'])] if os.environ.get('VSINSTALLDIR') else []
    bases = [Path(os.environ[k]) for k in ('ProgramFiles(x86)', 'ProgramFiles')
             if os.environ.get(k)]
    for base in bases:
        for year in ('2026', '2022'):
            vsroots.extend(base / 'Microsoft Visual Studio' / year / edition
                           for edition in ('BuildTools', 'Community', 'Professional', 'Enterprise'))
    for base in bases:
        vswhere = base / 'Microsoft Visual Studio' / 'Installer' / 'vswhere.exe'
        if not vswhere.is_file():
            continue
        try:
            result = subprocess.run([str(vswhere), '-products', '*',
                                     '-property', 'installationPath'],
                                    capture_output=True, text=True, timeout=10)
            vsroots.extend(Path(x.strip()) for x in result.stdout.splitlines() if x.strip())
        except (OSError, subprocess.TimeoutExpired):
            continue
    sdkroots = [Path(os.environ['WindowsSdkDir'])] if os.environ.get('WindowsSdkDir') else []
    sdkroots.extend(base / 'Windows Kits' / '10' for base in bases)
    return list(dict.fromkeys(vsroots)), list(dict.fromkeys(sdkroots))



@dataclass(frozen=True)
class WindowsCxxToolset:
    """One *complete* MSVC installation for native C++/CMake tests.

    VS installations may contain multiple minor MSVC releases. The first
    ``cl.exe`` on PATH is not sufficient: e.g. 14.31 may have an x64 compiler
    but only ARM libraries while 14.44 has matching x64 CRT libraries.
    Never combine a compiler from one minor toolset with another's CRT libs.
    """
    vs_root: Path
    version: str
    compiler: Path
    library_dir: Path
    sdk_root: Path
    sdk_version: str

    @property
    def generator(self) -> str:
        year = self.vs_root.parent.name
        if year == '2022':
            return 'Visual Studio 17 2022'
        if year == '2026':
            return 'Visual Studio 18 2026'
        raise ValueError(f'Unsupported Visual Studio CMake generator for {self.vs_root}')


def windows_complete_msvc_toolset(arch: str = 'x64') -> WindowsCxxToolset | None:
    """Select newest compiler+matching CRT+SDK with the requested target arch.

    Unlike simply calling `where cl`, this refuses incomplete side-by-side
    MSVC versions. Both the C++ compiler/linker and their own runtime import
    libraries must belong to the same version directory. SDK UCRT, Windows
    API import libraries and headers must be available for the same target.
    Detection is side-effect-free; it never edits PATH, LIB or the registry.
    """
    if os.name != 'nt':
        return None
    vsroots, sdkroots = _windows_install_roots()
    valid_sdks = []
    for sdk_root in sdkroots:
        lib_root = sdk_root / 'Lib'
        if not lib_root.is_dir():
            continue
        for version_dir in sorted(lib_root.iterdir(), key=_version_key, reverse=True):
            if not version_dir.is_dir():
                continue
            version = version_dir.name
            if all((path).is_file() for path in (
                version_dir/'ucrt'/arch/'ucrt.lib',
                version_dir/'um'/arch/'kernel32.lib',
                sdk_root/'Include'/version/'ucrt'/'stdio.h',
            )):
                valid_sdks.append((version, sdk_root))
    if not valid_sdks:
        return None
    valid_sdks.sort(key=lambda item: _version_key(Path(item[0])), reverse=True)
    sdversion, sdkroot = valid_sdks[0]
    found = []
    for root in vsroots:
        year = root.parent.name
        if year not in ('2022', '2026'):
            continue
        toolsets = root/'VC'/'Tools'/'MSVC'
        if not toolsets.is_dir():
            continue
        for version in toolsets.iterdir():
            if not version.is_dir():
                continue
            lib = version/'lib'/arch
            # Prefer 64-bit host tooling even for 32-bit x86 targets.
            compiler = version/'bin'/'Hostx64'/arch/'cl.exe'
            linker = version/'bin'/'Hostx64'/arch/'link.exe'
            if not compiler.is_file() or not linker.is_file():
                continue
            if not (version/'include'/'vcruntime.h').is_file():
                continue
            if not all((lib/name).is_file() for name in (
                'msvcrt.lib', 'oldnames.lib', 'vcruntime.lib')):
                continue
            found.append(WindowsCxxToolset(root,version.name,compiler,lib,
                                           sdkroot,sdversion))
    if not found:
        return None
    # A modern full installation beats an older/incomplete one, regardless
    # of which toolset happens to be injected into a Developer Shell's PATH.
    found.sort(key=lambda t: (int(t.vs_root.parent.name),_version_key(Path(t.version))),reverse=True)
    return found[0]


def windows_crt_library_dirs(arch: str = 'x64') -> list[Path]:
    """Resolve MSVC CRT, Windows UCRT and Windows API import library dirs.

    A successful C compile is insufficient: native Windows tests require
    all three sets of import libraries. Search for the selected architecture
    only; silently mixing x86 and x64 libraries causes confusing LLD errors.
    """
    if os.name != 'nt':
        return []
    vsroots, sdkroots = _windows_install_roots()
    envpaths = [Path(x) for x in os.environ.get('LIB', '').split(os.pathsep)
                if x and Path(x).name.lower() == arch.lower()]
    msvc=[]
    for root in vsroots:
        d=root/'VC'/'Tools'/'MSVC'
        if d.is_dir():
            msvc.extend(v/'lib'/arch for v in sorted(d.iterdir(),key=_version_key,reverse=True)
                        if v.is_dir())
    sdk=[]
    for root in sdkroots:
        d=root/'Lib'
        if d.is_dir():
            for v in sorted(d.iterdir(),key=_version_key,reverse=True):
                if v.is_dir():
                    sdk.extend((v/'ucrt'/arch, v/'um'/arch))
    candidates=list(dict.fromkeys(_existing_dirs(envpaths+msvc+sdk)))
    selected = windows_complete_msvc_toolset(arch)
    if selected:
        # Keep host-native mock and CMake tests on the SAME complete toolset.
        candidates = [selected.library_dir] + [p for p in candidates if p != selected.library_dir]
    ms=next((p for p in candidates if (p/'msvcrt.lib').is_file()
             and (p/'oldnames.lib').is_file()),None)
    ucrt=next((p for p in candidates if (p/'ucrt.lib').is_file()),None)
    um=next((p for p in candidates if (p/'kernel32.lib').is_file()),None)
    return [p for p in (ms,ucrt,um) if p is not None]


def windows_crt_include_dirs() -> list[Path]:
    """Resolve actual C runtime *headers*, not just their import libraries.

    This closes the `stdio.h not found` failure in a normal PowerShell. The
    Windows SDK provides ucrt/stdio.h; MSVC provides vcruntime.h and related
    headers. Explicit Clang system-include flags eliminate reliance on a
    preconfigured INCLUDE variable or Developer PowerShell shell state.
    """
    if os.name != 'nt':
        return []
    vsroots, sdkroots = _windows_install_roots()
    envdirs=[Path(x) for x in os.environ.get('INCLUDE','').split(os.pathsep) if x]
    msvc=[]
    for root in vsroots:
        d=root/'VC'/'Tools'/'MSVC'
        if d.is_dir():
            msvc.extend(v/'include' for v in sorted(d.iterdir(),key=_version_key,reverse=True)
                        if v.is_dir())
    sdk=[]
    for root in sdkroots:
        d=root/'Include'
        if d.is_dir():
            for version in sorted(d.iterdir(),key=_version_key,reverse=True):
                if version.is_dir():
                    sdk.extend(version/part for part in ('ucrt','shared','um','winrt'))
    candidates=list(dict.fromkeys(_existing_dirs(envdirs+msvc+sdk)))
    selected = windows_complete_msvc_toolset('x64')
    if selected:
        selected_include = selected.compiler.parents[3] / 'include'
        # compiler = MSVC/<version>/bin/Hostx64/x64/cl.exe ; parents[3]=<version>
        candidates = [selected_include] + [p for p in candidates if p != selected_include]
    vc=next((p for p in candidates if (p/'vcruntime.h').is_file()),None)
    ucrt=next((p for p in candidates if (p/'stdio.h').is_file()),None)
    if not vc or not ucrt:
        return []
    # Keep the SDK's optional headers available to CRT headers if requested;
    # the native Miles mock itself only needs the UCRT and MSVC C headers.
    extras=[p for p in candidates if p not in (vc,ucrt) and p.name.lower() in ('shared','um','winrt')]
    return [vc,ucrt,*extras]


def native_mock_ready() -> tuple[bool, str]:
    if not program('clang'):
        return False, 'Clang is not available on PATH'
    if os.name != 'nt':
        return True, 'Host-native Clang available'
    dirs = windows_crt_library_dirs('x64')
    headers = windows_crt_include_dirs()
    if len(dirs) < 3 or len(headers) < 2:
        return False, ('Missing x64 MSVC CRT, C headers or Windows SDK. '
                       'Install MSVC x64/x86 Build Tools and Windows SDK; see Docs/ONE_CLICK_BUILD.md.')
    return True, 'Microsoft CRT/SDK header and library directories discovered automatically'


def compile_native_mock(source: Path, output: Path) -> subprocess.CompletedProcess:
    """Compile a host-native *test executable*, not a redistributable A3D DLL."""
    compiler = program('clang')
    if not compiler:
        raise RuntimeError('clang was not found')
    cmd = [compiler, '-std=c11', '-O1', '-Wno-ignored-attributes']
    if os.name == 'nt':
        # Explicit target and linker paths work even in normal PowerShell,
        # where the Visual Studio Developer Shell has never been initialized.
        cmd.extend(['-target', 'x86_64-pc-windows-msvc', '-fms-runtime-lib=dll'])
        for directory in windows_crt_include_dirs():
            cmd.extend(['-isystem', str(directory)])
        for directory in windows_crt_library_dirs('x64'):
            cmd.extend(['-Xlinker', '/LIBPATH:' + str(directory)])
        # Clang's /MD-compatible declarations import UCRT entrypoints such as
        # __imp_puts.  Never mix them with the static libucrt.lib: selecting
        # that library can leave __imp_puts unresolved and trigger LNK4098.
        # Keep the dynamic UCRT import library alongside the dynamic MSVC CRT.
        cmd.extend(['-Xlinker', '/NODEFAULTLIB:libucrt.lib',
                    '-Xlinker', '/DEFAULTLIB:ucrt.lib'])
    cmd.extend([str(source), '-o', str(output)])
    return subprocess.run(cmd, capture_output=True, text=True)
