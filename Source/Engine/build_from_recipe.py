#!/usr/bin/env python3
"""Build the freestanding PE32 A3D components with Clang/LLD on Windows or Linux.

Uses the same pinned argument recipe as the native Codex Windows build.
No native MSVC headers, import-library SDK, installation, or Wine required.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--clang', default='clang')
    ap.add_argument('--linker', default='lld-link')
    ap.add_argument('--only-launchers', action='store_true')
    args = ap.parse_args()
    compiler = shutil.which(args.clang)
    linker = shutil.which(args.linker)
    if not compiler or not linker:
        ap.error('Clang and lld-link must be installed and on PATH')
    recipe = json.loads((ROOT/'windows-build-recipe.json').read_text())
    for n, step in enumerate(recipe):
        if args.only_launchers and n < 21:
            continue
        cwd = ROOT / step['directory']
        (cwd/'build').mkdir(exist_ok=True)
        program = compiler if step['program'].lower() == 'clang.exe' else linker
        command = [program] + step['args']
        print(f'[{n+1:02}/{len(recipe):02}] {step["directory"]}: {step["program"]}', flush=True)
        subprocess.run(command, cwd=cwd, check=True)
    for path in (ROOT/'win32/build/a3dapi.dll', ROOT/'win32/build/a3d.dll',
                 ROOT/'native/quake3-a3d-native.exe', ROOT/'classic2000/alice-a3d2000-native.exe',
                 ROOT/'remaster2011/alice-a3d2011-native.exe'):
        data = path.read_bytes()
        pe = int.from_bytes(data[0x3c:0x40],'little')
        if data[:2]!=b'MZ' or data[pe:pe+4]!=b'PE\0\0' or int.from_bytes(data[pe+4:pe+6],'little')!=0x14c:
            raise SystemExit(f'Not 32-bit Windows PE: {path}')
        print(f'PE32 verified: {path.relative_to(ROOT)} ({len(data)} bytes)')
    return 0

if __name__ == '__main__':
    sys.exit(main())
