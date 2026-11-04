#!/usr/bin/env python3
"""Verify Aufake3D release-artifact bit-for-bit reproducibility.

Use two independent clean source-tree copies with the SAME compiler/linker
installation. This is a local same-toolchain guarantee, not proof that two
arbitrarily different Clang/LLD versions produce identical machine code.

  python scripts/verify_reproducible.py --self-test
  python scripts/verify_reproducible.py --verify-current
  python scripts/verify_reproducible.py --check-report
  python scripts/verify_reproducible.py --compare first.zip second.zip
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
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = json.loads((ROOT/'packaging/Game_Kits/INSTALL_MAP.json').read_text())['version']
OUTPUT = f'dist/Aufake3D_v{VERSION}_Local_Runtime.zip'
REPORT = 'dist/REPRODUCIBILITY_VERIFIED.json'
DESCENT3_OUTPUT = 'dist/Aufake3D_v0.9.2_Descent3_Experimental_Win32.zip'
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
    def ignore(directory: str, names: list[str]) -> set[str]:
        excluded = {name for name in names if name in IGNORED_DIRS or
                    Path(name).suffix.lower() in IGNORED_EXTENSIONS or
                    name.endswith('.log')}
        # Regression guard for GitHub Actions installers that put their full
        # LLVM toolchain in ./llvm. It is an EXTERNAL BUILD INPUT, not project
        # source, and copying it twice can exhaust a hosted runner's disk.
        # Only skip the root-level directory when it really contains LLVM;
        # nested project source named "llvm" must still be copied.
        if Path(directory).resolve() == ROOT.resolve() and 'llvm' in names:
            bin_dir = ROOT / 'llvm' / 'bin'
            if any((bin_dir / exe).is_file() for exe in
                   ('clang', 'clang.exe', 'lld-link', 'lld-link.exe')):
                excluded.add('llvm')
        return excluded
    shutil.copytree(ROOT, destination, ignore=ignore)


def build(source: Path) -> None:
    cmd = [sys.executable, str(source/'scripts/build.py'), '--no-tests', '--no-acoustics',
           '--skip-repro-check']
    print('BUILD:', source, flush=True)
    subprocess.run(cmd, cwd=source, check=True)


def compiled_pe_hashes(source: Path) -> dict[str, str]:
    """Include all generated PE files, not only the two core DLLs."""
    roots = (source/'dist', source/'Source/Engine')
    results = {}
    for base in roots:
        for p in base.rglob('*'):
            # Descent 3's opt-in synthetic probe and its copied core DLLs
            # are NOT part of the 20-PE certified game runtime. Exclude
            # both the new persistent target and the historical probe tree.
            # Only these explicitly named experimental paths are excluded;
            # all normal generated PE outputs remain mandatory.
            relative = p.relative_to(source).parts
            if len(relative) > 2 and relative[:2] in (
                    ('dist', 'descent3'), ('dist', 'experimental-descent3')):
                continue
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
    return (not differences and compare_zips(alpha/OUTPUT, beta/OUTPUT) and
            compare_zips(alpha/DESCENT3_OUTPUT, beta/DESCENT3_OUTPUT))


def verify_current(work_dir: Path) -> bool:
    """Gate a local build against TWO independent fresh, same-toolchain builds.

    If verification fails, there is no approval sidecar. The report is kept
    outside the runtime ZIP so the act of certifying cannot change ZIP bytes.
    """
    report = ROOT/REPORT
    report.unlink(missing_ok=True)
    current_zip = ROOT/OUTPUT
    if not current_zip.is_file():
        raise FileNotFoundError('Build the current runtime first: '+str(current_zip))
    alpha, beta = work_dir/'source-a', work_dir/'source-b'
    for name in ('clang', 'lld-link'):
        p = shutil.which(name)
        if p:
            version = subprocess.run([p, '--version'], capture_output=True, text=True, check=True)
            print(name, version.stdout.splitlines()[0], flush=True)
    copy_clean_source(alpha)
    copy_clean_source(beta)
    build(alpha)
    build(beta)
    hashes = [compiled_pe_hashes(tree) for tree in (ROOT, alpha, beta)]
    names = set().union(*(h.keys() for h in hashes))
    differences = [name for name in sorted(names)
                   if not (hashes[0].get(name) == hashes[1].get(name) == hashes[2].get(name))]
    if not names:
        print('FAIL: no compiled PE binaries found')
        return False
    if differences:
        print('FAIL: current, clean A and clean B generated different PE binaries:')
        for name in differences[:30]:
            print(' -', name, *(h.get(name, '(missing)') for h in hashes))
        return False
    if not (compare_zips(current_zip, alpha/OUTPUT) and
            compare_zips(current_zip, beta/OUTPUT)):
        return False
    # The public Descent 3 ZIP must have identical raw bytes across all
    # three same-host builds, not merely identical decompressed DLLs.
    descent3_zip = ROOT/DESCENT3_OUTPUT
    if not (compare_zips(descent3_zip, alpha/DESCENT3_OUTPUT) and
            compare_zips(descent3_zip, beta/DESCENT3_OUTPUT)):
        return False
    approved = {
        'schema': 1,
        'version': VERSION,
        'verification': 'three-way-bit-identical',
        'scope': 'same-host-and-toolchain; cross-host identity NOT established',
        'runtime_zip': OUTPUT,
        'runtime_sha256': file_hash(current_zip),
        'descent3_zip': DESCENT3_OUTPUT,
        'descent3_zip_sha256': file_hash(descent3_zip),
        'generated_pe_sha256': dict(sorted(hashes[0].items())),
    }
    report.parent.mkdir(exist_ok=True)
    report.write_text(json.dumps(approved, sort_keys=True, indent=2)+'\n', encoding='utf-8')
    print('PASS: generated files and complete runtime ZIP match THREE independent builds')
    print('VERIFIED REPORT:', report)
    return True


def check_report() -> bool:
    report = ROOT/REPORT
    if not report.exists():
        print('FAIL: reproducibility verification report missing')
        return False
    content = json.loads(report.read_text(encoding='utf-8'))
    if (content.get('version') != VERSION or
            content.get('verification') != 'three-way-bit-identical' or
            content.get('runtime_zip') != OUTPUT or
            content.get('runtime_sha256') != file_hash(ROOT/OUTPUT) or
            content.get('generated_pe_sha256') != dict(sorted(compiled_pe_hashes(ROOT).items()))):
        print('FAIL: reproducibility report is stale or artifacts changed')
        return False
    # Preserve compatibility with historical report fixtures, but a new
    # v0.9.2 report that names the public kit may never pass if it was removed
    # or repacked after certification.
    public_archive = content.get('descent3_zip')
    public_digest = content.get('descent3_zip_sha256')
    if (public_archive is None) != (public_digest is None):
        print('FAIL: incomplete Descent 3 release ZIP evidence')
        return False
    if public_archive is not None:
        path = ROOT/DESCENT3_OUTPUT
        if (public_archive != DESCENT3_OUTPUT or not path.is_file() or
                file_hash(path) != public_digest):
            print('FAIL: Descent 3 public release ZIP is missing or changed')
            return False
    print('PASS: all verified local artifacts still match the recorded SHA-256 manifest')
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--self-test', action='store_true', help='Rebuild twice in fresh, separate directories and compare')
    group.add_argument('--verify-current', action='store_true',
                       help='Release gate: compare current build with TWO clean rebuilds and write verified report')
    group.add_argument('--check-report', action='store_true',
                       help='Fail if verified manifest is missing or its artifact hashes changed')
    group.add_argument('--compare', nargs=2, type=Path, metavar=('FIRST.zip', 'SECOND.zip'),
                       help='Compare two previously built complete runtime ZIPs')
    parser.add_argument('--keep-dir', type=Path, help='Retain fresh self-test source copies/logs under this NEW directory')
    args = parser.parse_args()
    try:
        if args.check_report:
            return 0 if check_report() else 1
        if args.compare:
            if args.keep_dir:
                parser.error('--keep-dir is only valid with --self-test')
            return 0 if compare_zips(*args.compare) else 1
        if args.keep_dir:
            directory = args.keep_dir.resolve()
            directory.mkdir(parents=True, exist_ok=False)
            passed = verify_current(directory) if args.verify_current else self_test(directory)
            return 0 if passed else 1
        with tempfile.TemporaryDirectory(prefix='aufake3d-repro-') as temp:
            passed = verify_current(Path(temp)) if args.verify_current else self_test(Path(temp))
            return 0 if passed else 1
    except (OSError, RuntimeError, subprocess.CalledProcessError, zipfile.BadZipFile) as exc:
        print('REPRODUCIBILITY CHECK FAILED:', exc, file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
