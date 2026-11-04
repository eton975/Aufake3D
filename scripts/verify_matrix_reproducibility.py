#!/usr/bin/env python3
"""Fail-closed cross-OS certification for Windows plus ALL three Ubuntu targets.

All four CI artifacts must exist and match, including exact bytes of every
compiled PE, the complete runtime ZIP and every tracked source file. Never
issue a successful certificate for a partial matrix.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import verify_cross_platform as v

WINDOWS = 'windows-2022'
UBUNTU_TARGETS = ('ubuntu-24.04', 'ubuntu-26.04', 'ubuntu-26.10')
LLVM_VERSION = '19.1.7'
PYTHON_VERSION = '3.13.7'


def load_bundle(folder: Path) -> tuple[dict, Path, Path]:
    manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
    # Malformed/malicious manifest names must not escape their artifact directory.
    for field in ('runtime_zip_name', 'generated_pe_bundle_name'):
        name = manifest.get(field)
        if not isinstance(name, str) or Path(name).name != name or name in ('', '.', '..'):
            raise ValueError(f'Invalid {field} in {folder}: {name!r}')
    return (manifest, folder / manifest['runtime_zip_name'],
            folder / manifest['generated_pe_bundle_name'])


def compare_matrix(windows: tuple[dict, Path, Path],
                   linux: dict[str, tuple[dict, Path, Path]],
                   expected_commit: str) -> tuple[dict | None, list[str]]:
    errors: list[str] = []
    if not re.fullmatch(r'[0-9a-f]{40}', expected_commit):
        errors.append('Expected Git commit must be a full lowercase 40-character SHA')
    if set(linux) != set(UBUNTU_TARGETS):
        errors.append('Missing or unexpected Ubuntu targets; mandatory targets are '
                      + ', '.join(UBUNTU_TARGETS))
    w, wzip, wpe = windows
    if w.get('target') != WINDOWS or w.get('host') != 'windows' or w.get('os_id') != 'windows':
        errors.append('Windows reference has missing/incorrect Windows runner identity')
    all_bundles = {WINDOWS: windows, **linux}
    for name, (manifest, _, _) in all_bundles.items():
        if manifest.get('source_commit') != expected_commit:
            errors.append(f'{name}: source commit does not match CI checkout')
        if manifest.get('python_version') != PYTHON_VERSION:
            errors.append(f'{name}: Python must be pinned to {PYTHON_VERSION}')
        if manifest.get('llvm_versions') != {'clang': LLVM_VERSION, 'lld-link': LLVM_VERSION}:
            errors.append(f'{name}: LLVM must be pinned to {LLVM_VERSION}')
        if name in UBUNTU_TARGETS:
            version = name.removeprefix('ubuntu-')
            if (manifest.get('target'), manifest.get('host'),
                    manifest.get('os_id'), manifest.get('os_version')) != (
                    name, 'linux', 'ubuntu', version):
                errors.append(f'{name}: claimed target does not match authenticated OS release')
    for name in UBUNTU_TARGETS:
        if name not in linux:
            continue
        m, z, pe = linux[name]
        _, failures = v.compare_builds(w, m, wzip, z, wpe, pe,
                                       expected_commit=expected_commit)
        errors.extend(f'{name}: {error}' for error in failures)
    if errors:
        return None, errors
    return {
        'schema': 3,
        'verification': 'windows-ubuntu-24.04-26.04-26.10-byte-identical',
        'source_commit': expected_commit,
        'targets': [WINDOWS, *UBUNTU_TARGETS],
        'runtime_zip_name': w['runtime_zip_name'],
        'runtime_zip_sha256': w['runtime_zip_sha256'],
        'generated_pe_bundle_sha256': w['generated_pe_bundle_sha256'],
        'generated_pe_sha256': w['generated_pe_sha256'],
        'llvm_versions': w['llvm_versions'],
        'python_version': w['python_version'],
        'tracked_source_count': len(w['tracked_source_sha256']),
        'runtime_entry_count': len(w['runtime_entries_sha256']),
        'scope': 'Four checked CI target environments; Win32 PE and full runtime ZIP only, not gameplay',
    }, []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--windows', type=Path, required=True)
    parser.add_argument('--linux-target', action='append', default=[],
                        metavar='UBUNTU-VERSION=ARTIFACT-DIRECTORY',
                        help='Required exactly once for each Ubuntu 24.04, 26.04 and 26.10')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--expected-commit', required=True)
    args = parser.parse_args()
    args.out.unlink(missing_ok=True)  # a failed rerun must NEVER retain previous proof
    try:
        paths: dict[str, Path] = {}
        for item in args.linux_target:
            name, separator, path = item.partition('=')
            if not separator or not path or name not in UBUNTU_TARGETS or name in paths:
                raise ValueError(f'Invalid or duplicate mandatory Ubuntu target {item!r}')
            paths[name] = Path(path)
        if set(paths) != set(UBUNTU_TARGETS):
            raise ValueError('All three Ubuntu target artifacts are mandatory')
        windows = load_bundle(args.windows)
        linux = {name: load_bundle(paths[name]) for name in UBUNTU_TARGETS}
        certificate, errors = compare_matrix(windows, linux, args.expected_commit)
        if errors:
            print('FAIL: four-target reproducibility is NOT certified:')
            for error in errors[:100]:
                print(' -', error)
            return 1
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(certificate, indent=2, sort_keys=True)+'\n', encoding='utf-8')
        print('PASS: Windows, Ubuntu 24.04, 26.04 and 26.10 are bit-identical: '
              + certificate['runtime_zip_sha256'])
        return 0
    except (OSError, KeyError, ValueError, TypeError, subprocess.CalledProcessError,
            zipfile.BadZipFile) as exc:
        print('FAIL: cross-platform reproducibility NOT certified:', exc, file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
