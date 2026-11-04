#!/usr/bin/env python3
"""Opt-in Descent 3 A3D2 experimental PE32 probe and standalone adapter build.

Outputs to dist/descent3/ only. The executable is a synthetic A3D2 COM smoke
probe, NOT the Descent 3 game. The adapter .obj is compiled with a standalone
ABI shim and is NOT a drop-in DLL or a proven game-engine linkable object.

Existing certified Aufake3D game runtime ZIP and the 20-PE verification
certificate are deliberately not changed by this optional build target.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts import build_pinned as pin  # noqa: E402

DEST = ROOT / 'dist' / 'descent3'
ADAPTER = ROOT / 'Integrations' / 'Descent3_Source' / 'aufake3d_aureal.cpp'
PROBE_SCRIPT = ROOT / 'scripts' / 'build_descent3_contract_probe.py'
PROBE_C = ROOT / 'Source' / 'Engine' / 'win32' / 'descent3_contract_probe.c'
PROBE_DEF = ROOT / 'Source' / 'Engine' / 'win32' / 'descent3_probe_kernel32.def'
PROBE_NAME = 'a3d-descent3-contract-probe.exe'
ADAPTER_NAME = 'descent3-aureal-standalone-adapter.obj'
CORE_NAMES = ('a3dapi.dll', 'a3d.dll')
EXPERIMENTAL_NOTICE = (
    'EXPERIMENTAL ONLY: not the retail or source-built Descent 3 game; '
    'not validated for gameplay, authentic A3D2 activation, or audio fidelity.'
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    return digest(path.read_bytes())


def check_pe32(path: Path) -> None:
    data = path.read_bytes()
    if len(data) < 256 or data[:2] != b'MZ':
        raise RuntimeError(f'Not a Windows x86 PE executable/DLL: {path}')
    header = struct.unpack_from('<I', data, 0x3c)[0]
    if header + 6 > len(data) or data[header:header+4] != b'PE\0\0':
        raise RuntimeError(f'Invalid Windows PE header: {path}')
    if struct.unpack_from('<H', data, header + 4)[0] != 0x14c:
        raise RuntimeError(f'Expected 32-bit x86 Windows PE: {path}')


def check_coff_i386(path: Path) -> None:
    data = path.read_bytes()
    if len(data) < 20 or struct.unpack_from('<H', data, 0)[0] != 0x14c:
        raise RuntimeError('Descent 3 adapter must be an i386 COFF object, not a native ELF/PE')
    if struct.unpack_from('<H', data, 2)[0] == 0:
        raise RuntimeError('Empty Descent 3 COFF adapter object')


def command_version(exe: str, env: dict[str, str]) -> str:
    p = subprocess.run([exe, '--version'], check=True, text=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    return p.stdout.splitlines()[0] if p.stdout else p.stderr.splitlines()[0]


def tools_from_args(args: argparse.Namespace) -> tuple[str, str, dict[str, str], bool]:
    if bool(args.clang) != bool(args.linker):
        raise RuntimeError('Specify --clang AND --linker together, or neither (pinned default)')
    if args.clang:
        if not args.allow_unpinned_tools:
            raise RuntimeError('Custom tools require --allow-unpinned-tools; never claim CI certification')
        clang, linker = args.clang, args.linker
        for tool in (clang, linker):
            if shutil.which(tool) is None and not Path(tool).is_file():
                raise RuntimeError(f'Cannot find compiler/linker: {tool}')
        return clang, linker, dict(os.environ), False
    host = 'windows' if os.name == 'nt' else 'linux'
    cache = pin.cache_root()
    cache.mkdir(parents=True, exist_ok=True)
    compiler_bin = pin.pinned_llvm(cache, host)
    # Use exactly the same compiler from the official CI reference pinned
    # local builder, not the unrelated /usr/bin/clang++ from Debian.
    env = pin.build_env(cache, Path(sys.executable), compiler_bin)
    if host == 'linux':
        check = subprocess.run([str(compiler_bin / 'lld-link'), '--version'],
                               env=env, capture_output=True, text=True)
        if check.returncode and 'libxml2.so.2' in check.stderr:
            print('Building pinned private libxml2 compatibility dependency.', flush=True)
            subprocess.run(['bash', str(ROOT/'scripts/local_prepare_llvm_compat.sh'),
                            str(compiler_bin.parent), str(cache/'legacy-libxml2')],
                           check=True, env=env)
    pin.assert_versions(compiler_bin, env)
    suffix = '.exe' if host == 'windows' else ''
    return (str(compiler_bin / ('clang' + suffix)),
            str(compiler_bin / ('lld-link' + suffix)), env, True)


def compile_adapter(clang: str, env: dict[str, str], output: Path) -> None:
    """Build the historical adapter against the *standalone* ABI shim only."""
    argv = [clang, '-x', 'c++', '-target', 'i686-pc-windows-msvc',
            '-std=c++11', '-O2', '-fno-exceptions', '-fno-rtti',
            '-ffreestanding', '-fno-stack-protector', '-fno-builtin',
            '-Wall', '-Wextra', '-Werror',
            '-DAUFAKE3D_ADAPTER_STANDALONE',
            '-c', str(ADAPTER), '-o', str(output)]
    result = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f'Experimental Descent 3 adapter failed to compile:\n'
                           f'{result.stdout}\n{result.stderr}')
    check_coff_i386(output)


def build_probe(clang: str, linker: str, env: dict[str, str], output: Path) -> None:
    # Its existing builder already does two independently rebuilt, byte-for-byte
    # identical PE32 tests; reuse it, don't weaken that established contract.
    subprocess.run([sys.executable, str(PROBE_SCRIPT), '--clang', clang,
                    '--linker', linker, '--out', str(output)],
                   cwd=ROOT, env=env, check=True)
    check_pe32(output)


def copy_core_to_stage(stage: Path) -> dict[str, str]:
    core = ROOT / 'dist' / 'core'
    hashes: dict[str, str] = {}
    for filename in CORE_NAMES:
        src = core / filename
        if not src.is_file():
            raise RuntimeError(
                f'Missing {src}. Build the Aufake3D core first with BUILD_LINUX.sh '
                '(or BUILD_WINDOWS.cmd), or use --probe-only to build without DLLs.'
            )
        check_pe32(src)
        shutil.copyfile(src, stage / filename)
        hashes[filename] = sha_file(stage / filename)
    return hashes


def write_reports(stage: Path, clang: str, linker: str,
                  env: dict[str, str], pinned: bool, core_hashes: dict[str, str]) -> None:
    source_files = (ADAPTER, PROBE_C, PROBE_DEF, PROBE_SCRIPT)
    outputs = [PROBE_NAME, ADAPTER_NAME, *core_hashes]
    details = {
        'schema': 1,
        'status': 'EXPERIMENTAL_ONLY_NOT_GAMEPLAY_VALIDATED',
        'scope': 'synthetic Descent 3 A3D2 COM probe and standalone shim object; NOT a game binary',
        'compiler': {
            'clang_version': command_version(clang, env),
            'linker_version': command_version(linker, env),
            'clang_sha256': sha_file(Path(shutil.which(clang) or clang)),
            'lld_link_sha256': sha_file(Path(shutil.which(linker) or linker)),
            'official_pinned_llvm_19_1_7': pinned,
        },
        'source_sha256': {p.relative_to(ROOT).as_posix(): sha_file(p) for p in source_files},
        'outputs_sha256': {name: sha_file(stage / name) for name in sorted(outputs)},
        'probe_rebuilt_twice_identical': True,
        'adapter_object_rebuilt_twice_identical': True,
        'gameplay_verified': False,
        'original_retail_exe_tested': False,
        'descent3_engine_linked': False,
        'runtime_compatibility_certified': False,
        'release_runtime_zip_modified': False,
    }
    (stage / 'EXPERIMENTAL_BUILD_MANIFEST.json').write_text(
        json.dumps(details, sort_keys=True, indent=2) + '\n', encoding='utf-8'
    )
    note = f'''Aufake3D — Descent 3 EXPERIMENTAL diagnostics (NOT GAME SUPPORT)

{EXPERIMENTAL_NOTICE}

{PROBE_NAME}: independent x86 Windows PE synthetic A3D2 COM contract probe.
{ADAPTER_NAME}: x86 COFF translation-unit object compiled with STANDALONE ABI
    shims. It is NOT a drop-in game DLL or a source-engine-linked object.
a3dapi.dll / a3d.dll: copies of your own previously compiled Aufake3D core
    (if present); NOT original Aureal drivers and NOT Descent 3 binaries.

Run Windows: {PROBE_NAME}
Run Debian 13/Wine: wine ./{PROBE_NAME}
Optional audible test, only on explicit request: --audio

Probe is read-only relative to Descent 3 games: no EXE modification,
registration, administrator rights or game files needed.
For actual Descent 3 integration, use the separate source-engine installer
Integrations/Descent3_Source/install_into_checkout.py on an appropriate
Descent3 source checkout, then compile that engine with its own toolchain.

Read EXPERIMENTAL_BUILD_MANIFEST.json for exact input/output SHA-256.
This build is outside the mandatory 20-PE/ZIP release certificate.
'''
    (stage / 'README_EXPERIMENTAL.txt').write_text(note, encoding='utf-8')
    (stage / 'RUN_PROBE_WINDOWS.cmd').write_bytes(
        b'@echo off\r\ncd /d "%~dp0"\r\na3d-descent3-contract-probe.exe %*\r\nexit /b %ERRORLEVEL%\r\n'
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--clang', help='Override Clang (requires --allow-unpinned-tools)')
    parser.add_argument('--linker', help='Override LLD (requires --allow-unpinned-tools)')
    parser.add_argument('--allow-unpinned-tools', action='store_true',
                        help='Developer smoke-test only; output will NOT be CI certified')
    parser.add_argument('--probe-only', action='store_true',
                        help='Build probe + adapter object but omit Aufake3D core DLL copies')
    args = parser.parse_args(argv)
    try:
        clang, linker, env, pinned = tools_from_args(args)
        with tempfile.TemporaryDirectory(prefix='aufake3d-descent3-exp-') as tmp:
            root = Path(tmp)
            first = root/'first'
            second = root/'second'
            first.mkdir(); second.mkdir()
            compile_adapter(clang, env, first/ADAPTER_NAME)
            compile_adapter(clang, env, second/ADAPTER_NAME)
            if (first/ADAPTER_NAME).read_bytes() != (second/ADAPTER_NAME).read_bytes():
                raise RuntimeError('Descent 3 standalone adapter COFF outputs are not byte-identical')
            print('PASS: two independently compiled Descent 3 COFF adapters match.')
            build_probe(clang, linker, env, first/PROBE_NAME)
            core_hashes = {} if args.probe_only else copy_core_to_stage(first)
            write_reports(first, clang, linker, env, pinned, core_hashes)
            DEST.parent.mkdir(parents=True, exist_ok=True)
            # Remove only the dedicated opt-in output tree; never disturb the
            # runtime ZIP, installed games or main compiled engine products.
            if DEST.is_symlink():
                raise RuntimeError('Refusing a symlink at dist/descent3 output path')
            if DEST.exists():
                shutil.rmtree(DEST)
            shutil.copytree(first, DEST)
        print('EXPERIMENTAL DESCENT 3 OUTPUT:', DEST, flush=True)
        for file in sorted(DEST.iterdir()):
            print(' ', file.name, file.stat().st_size, 'bytes', flush=True)
        print(EXPERIMENTAL_NOTICE, flush=True)
        return 0
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as exc:
        print('DESCENT 3 EXPERIMENTAL BUILD FAILED:', exc, file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
