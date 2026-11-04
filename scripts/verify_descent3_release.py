#!/usr/bin/env python3
"""Fail-closed five-target identity check for the public Descent 3 ZIP.

This supplements (never replaces) the certified universal-runtime five-target
comparison. It does NOT certify audio quality, HRTF, gameplay or game assets.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts import package_descent3_release as pkg

TARGETS = ('windows-2022', 'ubuntu-24.04', 'ubuntu-26.04', 'ubuntu-26.10', 'debian-13')
RUNTIME_NAME = f'Aufake3D_v{pkg.VERSION}_Local_Runtime.zip'


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_validated(folder: Path, expected_commit: str) -> tuple[bytes, dict[str, str]]:
    """Check real ZIP bytes and shared-core identity, not just manifest claims."""
    evidence = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
    if evidence.get('source_commit') != expected_commit:
        raise ValueError(f'{folder}: source commit differs from checked-out CI commit')
    if evidence.get('local_verification') != 'three-way-bit-identical':
        raise ValueError(f'{folder}: missing same-host three-build verification')
    if evidence.get('runtime_zip_name') != RUNTIME_NAME:
        raise ValueError(f'{folder}: unexpected parent runtime ZIP')
    runtime_path = folder / RUNTIME_NAME
    runtime_bytes = runtime_path.read_bytes()
    if sha(runtime_bytes) != evidence.get('runtime_zip_sha256'):
        raise ValueError(f'{folder}: parent runtime differs from CI evidence')
    with zipfile.ZipFile(runtime_path) as runtime:
        names = runtime.namelist()
        cores = {}
        for name in pkg.CORE:
            entry = f'Aufake3D-v{pkg.VERSION}-Local/Universal_Core/{name}'
            if names.count(entry) != 1:
                raise ValueError(f'{folder}: missing or duplicate universal core {name}')
            cores[name] = runtime.read(entry)
    expected_package = pkg.make_zip(pkg.payload_from_core(cores))
    actual_package = (folder / pkg.FILENAME).read_bytes()
    if actual_package != expected_package:
        raise ValueError(f'{folder}: public Descent 3 ZIP differs from deterministic rebuild using its certified universal core')
    return actual_package, {name: sha(cores[name]) for name in pkg.CORE}


def certify(folders: dict[str, Path], expected_commit: str, base_certificate: Path) -> dict:
    if set(folders) != set(TARGETS):
        raise ValueError('All five mandatory CI environments must be supplied')
    if not re.fullmatch(r'[0-9a-f]{40}', expected_commit):
        raise ValueError('Expected source commit must be a full 40-character hexadecimal hash')
    parent = json.loads(base_certificate.read_text(encoding='utf-8'))
    if (parent.get('source_commit') != expected_commit or
            parent.get('targets') != list(TARGETS) or
            parent.get('runtime_zip_name') != RUNTIME_NAME or
            not parent.get('runtime_zip_sha256')):
        raise ValueError('Mandatory five-platform universal-runtime certificate missing or inconsistent')
    packages: dict[str, bytes] = {}
    core_hashes: dict[str, dict[str, str]] = {}
    for target in TARGETS:
        folder = folders[target]
        manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
        if manifest.get('target') != target:
            raise ValueError(f'{target}: incorrect runner identity in evidence')
        if manifest.get('runtime_zip_sha256') != parent['runtime_zip_sha256']:
            raise ValueError(f'{target}: parent runtime hash differs from approved five-platform certificate')
        packages[target], core_hashes[target] = read_validated(folder, expected_commit)
    baseline = packages[TARGETS[0]]
    hashes = core_hashes[TARGETS[0]]
    for target in TARGETS[1:]:
        if packages[target] != baseline:
            raise ValueError(f'{target}: public Descent 3 ZIP NOT byte-for-byte identical to Windows')
        if core_hashes[target] != hashes:
            raise ValueError(f'{target}: universal DLLs disagree across platforms')
    return {
        'schema': 1,
        'status': 'five-target-byte-identical',
        'compatibility': 'experimental; spatialisation and gameplay NOT certified',
        'version': pkg.VERSION,
        'source_commit': expected_commit,
        'targets': list(TARGETS),
        'parent_runtime_zip_sha256': parent['runtime_zip_sha256'],
        'public_zip_name': pkg.FILENAME,
        'public_zip_sha256': sha(baseline),
        'shared_core_sha256': hashes,
        'verification': 'exact raw ZIP bytes plus reconstruction from the certified universal-core DLLs',
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--windows', type=Path, required=True)
    parser.add_argument('--linux-target', action='append', default=[], metavar='NAME=DIR')
    parser.add_argument('--base-certificate', type=Path, required=True)
    parser.add_argument('--expected-commit', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.unlink(missing_ok=True)
    try:
        folders = {TARGETS[0]: args.windows}
        for entry in args.linux_target:
            name, delim, folder = entry.partition('=')
            if not delim or not folder or name not in TARGETS[1:] or name in folders:
                raise ValueError('Invalid, unexpected or duplicate Linux runner: '+entry)
            folders[name] = Path(folder)
        report = certify(folders, args.expected_commit, args.base_certificate)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, sort_keys=True, indent=2) + '\n', encoding='utf-8')
        print('PASS: Descent 3 public ZIP is bit-identical across ALL five mandatory CI targets')
        print('SHA-256:', report['public_zip_sha256'])
        return 0
    except (OSError, RuntimeError, KeyError, TypeError, ValueError, zipfile.BadZipFile) as exc:
        print('FAIL: public Descent 3 ZIP cross-platform certification:', exc, file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
