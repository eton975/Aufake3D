#!/usr/bin/env python3
"""Verify Aufake3D release-artifact bit-for-bit reproducibility.

Use two independent clean source-tree copies with the SAME compiler/linker
installation. This is a local same-toolchain guarantee, not proof that two
arbitrarily different Clang/LLD versions produce identical machine code.

  python scripts/verify_reproducible.py --self-test
  python scripts/verify_reproducible.py --compare first.zip second.zip
"""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = 'dist/Aufake3D_v0.9.0_Local_Runtime.zip'
IGNORED_DIRS = {'.git', 'build', 'dist', '__pycache__', '.pytest_cache', '.mypy_cache', '.venv', 'venv'}
IGNORED_EXTENSIONS = {'.dll', '.exe', '.lib', '.obj', '.o', '.exp', '.pdb', '.pyc'}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_hash(path: Path) -> str:
    return sha256(path.read_bytes())


def zip_differences(left: Path, right: Path) -> list[str]:
    """List differences in entry bytes, even when ZIP compression differs."""
    with zipfile.ZipFile(left) as za, zipfile.ZipFile(right) as zb:
        a, b = set(za.namelist()), set(zb.namelist())
        result = [f'Only in first archive: {n}' for n in sorted(a - b)]
        result += [f'Only in second archive: {n}' for n in sorted(b - a)]
        result += [f'Entry differs: {n}' for n in sorted(a & b)
                   if sha256(za.read(n)) != sha256(zb.read(n))]
        if not result and file_hash(left) != file_hash(right):
            result.append('All entries match; container metadata/compression differs')
        return result


def compare_zips(first: Path, second: Path) -> bool:
    if not first.is_file() or not second.is_file():
        raise FileNotFoundError('Both runtime ZIP files must exist')
    a, b = file_hash(first), file_hash(second)
    print('FIRST: ', a, first, flush=True)
    print('SECOND:', b, second, flush=True)
    if a == b:
        print('PASS: complete runtime ZIPs are SHA-256 identical')
        return True
    print('FAIL: runtime ZIP SHA-256 mismatch')
    for item in zip_differences(first, second)[:30]:
        print(' -', item)
    return False


def copy_clean_source(destination: Path) -> None:
    """Copy the same source inputs into a separate build directory."""
    def ignore(_directory: str, names: list[str]) -> set[str]:
        return {name for name in names if name in IGNORED_DIRS or
                Path(name).suffix.lower() in IGNORED_EXTENSIONS or name.endswith('.log')}
    shutil.copytree(ROOT, destination, ignore=ignore)


def build(source: Path) -> None:
    cmd = [sys.executable, str(source/'scripts/build.py'), '--no-tests', '--no-acoustics']
    print('BUILD:', source, flush=True)
    subprocess.run(cmd, cwd=source, check=True)


def compiled_pe_hashes(source: Path) -> dict[str, str]:
    """Include all generated PE files, not only the two core DLLs."""
    roots = (source/'dist', source/'Source/Engine')
    results = {}
    for base in roots:
        for p in base.rglob('*'):
            if p.is_file() and p.suffix.lower() in ('.exe', '.dll'):
                data = p.read_bytes()
                if data[:2] == b'MZ':
                    results[p.relative_to(source).as_posix()] = sha256(data)
    return results


def self_test(work_dir: Path) -> bool:
    alpha, beta = work_dir/'source-a', work_dir/'source-b'
    if alpha.exists() or beta.exists():
        raise RuntimeError('Refusing to overwrite existing source-a or source-b')
    for name in ('clang', 'lld-link'):
        p = shutil.which(name)
        if p:
            completed = subprocess.run([p, '--version'], capture_output=True, text=True)
            print(name, completed.stdout.splitlines()[0] if completed.stdout else p, flush=True)
    copy_clean_source(alpha)
    copy_clean_source(beta)
    build(alpha)
    build(beta)
    a, b = compiled_pe_hashes(alpha), compiled_pe_hashes(beta)
    differences = [name for name in sorted(a.keys() | b.keys()) if a.get(name) != b.get(name)]
    if differences:
        print('FAIL: generated PE files differ:')
        for name in differences[:30]:
            print(' -', name, a.get(name, '(missing)'), b.get(name, '(missing)'))
    else:
        print(f'PASS: {len(a)} generated PE executables and DLLs SHA-256 identical')
    return not differences and compare_zips(alpha/OUTPUT, beta/OUTPUT)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--self-test', action='store_true', help='Rebuild twice in fresh, separate directories and compare')
    group.add_argument('--compare', nargs=2, type=Path, metavar=('FIRST.zip', 'SECOND.zip'),
                       help='Compare two previously built complete runtime ZIPs')
    parser.add_argument('--keep-dir', type=Path, help='Retain fresh self-test source copies/logs under this NEW directory')
    args = parser.parse_args()
    try:
        if args.compare:
            if args.keep_dir:
                parser.error('--keep-dir is only valid with --self-test')
            return 0 if compare_zips(*args.compare) else 1
        if args.keep_dir:
            directory = args.keep_dir.resolve()
            directory.mkdir(parents=True, exist_ok=False)
            return 0 if self_test(directory) else 1
        with tempfile.TemporaryDirectory(prefix='aufake3d-repro-') as temp:
            return 0 if self_test(Path(temp)) else 1
    except (OSError, RuntimeError, subprocess.CalledProcessError, zipfile.BadZipFile) as exc:
        print('REPRODUCIBILITY CHECK FAILED:', exc, file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
