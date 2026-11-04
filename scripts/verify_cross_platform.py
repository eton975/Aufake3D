#!/usr/bin/env python3
"""Cross-OS reproducibility gate for Aufake3D's Win32 PE runtime.

CI runs `emit` on each separately built Windows/Linux runner, uploads the
actual runtime ZIP and manifest, then runs `compare` on both downloaded sets.
No cross-platform certificate is written until both raw ZIPs, all built PE
hashes, and every tracked source byte match. Same-host proofs are independent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import verify_reproducible as local_repro  # noqa: E402

SCHEMA = 2
DEFAULT_ZIP = local_repro.OUTPUT
# A separate, deterministic archive contains every generated PE found by the
# existing local verifier, including PE files not included in the runtime ZIP.
PE_EVIDENCE_NAME = 'Aufake3D_Generated_PE_Evidence.zip'


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command_stdout(args: list[str], *, cwd: Path | None = None) -> str:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


def llvm_versions() -> dict[str, str]:
    versions = {}
    for name in ('clang', 'lld-link'):
        output = command_stdout([name, '--version'])
        # The first version following clang/LLD is the compiler's actual version,
        # not a library/SDK version which might also appear in the output.
        match = re.search(r'\b(?:clang version|LLD)\s+(\d+\.\d+\.\d+)\b', output)
        if not match:
            raise ValueError(f'Cannot identify {name} version from {output[:150]!r}')
        versions[name] = match.group(1)
    return versions


def clean_checkout_commit(root: Path) -> str:
    """A certificate must name the exact committed source, never dirty files."""
    commit = command_stdout(['git', 'rev-parse', 'HEAD'], cwd=root)
    dirty = command_stdout(['git', 'status', '--porcelain', '--untracked-files=all'], cwd=root)
    if dirty:
        raise ValueError('Cannot certify a dirty checkout; commit all source changes first')
    if not re.fullmatch(r'[0-9a-f]{40}', commit):
        raise ValueError('Not a full Git commit ID: ' + commit)
    return commit


def tracked_source_hashes(root: Path) -> dict[str, str]:
    # Do not use git's index object IDs: a checkout may contain CRLF-modified
    # file bytes while the git blob IDs still agree across hosts.
    paths = subprocess.run(['git', 'ls-files', '-z'], cwd=root,
                           check=True, capture_output=True).stdout.split(b'\0')
    result: dict[str, str] = {}
    for raw in paths:
        if not raw:
            continue
        name = raw.decode('utf-8', errors='surrogateescape').replace('\\', '/')
        path = root / name
        if not path.is_file():
            raise ValueError(f'Tracked source missing: {name}')
        result[name] = digest(path)
    if not result:
        raise ValueError('No git-tracked source files found')
    return dict(sorted(result.items()))


def archive_entries(path: Path) -> dict[str, str]:
    with zipfile.ZipFile(path, 'r') as z:
        names = z.namelist()
        if len(names) != len(set(names)):
            raise ValueError('Runtime ZIP has duplicate entry names')
        if not names:
            raise ValueError('Runtime ZIP is empty')
        entries = {name: hashlib.sha256(z.read(name)).hexdigest() for name in names}
    return dict(sorted(entries.items()))


def write_pe_evidence(root: Path, destination: Path, pe_hashes: dict[str, str]) -> None:
    """Archive actual compiler outputs; don't trust unverified digest claims.

    Raw ZIP_STORED bytes and metadata are deterministic on Windows and Linux.
    The archive is evidence only; it is NOT packaged into game distributions.
    """
    if not pe_hashes:
        raise ValueError('Cannot create empty PE evidence archive')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, 'w', compression=zipfile.ZIP_STORED) as z:
        for relative, expected in sorted(pe_hashes.items()):
            file = root / relative
            if (not file.is_file() or Path(relative).is_absolute() or
                    '..' in Path(relative).parts):
                raise ValueError(f'Invalid PE evidence path: {relative}')
            data = file.read_bytes()
            if not data.startswith(b'MZ') or hashlib.sha256(data).hexdigest() != expected:
                raise ValueError(f'Generated PE changed during evidence creation: {relative}')
            info = zipfile.ZipInfo(relative, date_time=(2026, 1, 1, 0, 0, 0))
            info.create_system = 3  # stable Unix metadata on BOTH hosts
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_STORED
            z.writestr(info, data)
    if archive_entries(destination) != pe_hashes:
        raise ValueError('PE evidence archive verification failed')


def create_manifest(root: Path, archive: Path, expected_llvm: str) -> dict:
    versions = llvm_versions()
    if versions != {'clang': expected_llvm, 'lld-link': expected_llvm}:
        raise ValueError(f'Pinned LLVM {expected_llvm} required; found {versions}')
    # Fail closed if the local verification report is stale or absent.
    # verify_reproducible is imported from exactly this source checkout.
    if root != ROOT:
        raise ValueError('Emit must run against its own source checkout')
    if not local_repro.check_report():
        raise ValueError('Same-host three-build verification did not pass')
    if not archive.is_file():
        raise FileNotFoundError(archive)
    pe_hashes = local_repro.compiled_pe_hashes(root)
    if not pe_hashes:
        raise ValueError('No compiled Windows PE binaries found')
    evidence = root/'dist'/PE_EVIDENCE_NAME
    write_pe_evidence(root, evidence, pe_hashes)
    return {
        'schema': SCHEMA,
        'source_commit': clean_checkout_commit(root),
        'host': platform.system().lower(),
        'python_version': platform.python_version(),
        'llvm_versions': versions,
        'local_verification': 'three-way-bit-identical',
        'runtime_zip_name': archive.name,
        'runtime_zip_sha256': digest(archive),
        'runtime_entries_sha256': archive_entries(archive),
        'generated_pe_sha256': dict(sorted(pe_hashes.items())),
        'generated_pe_bundle_name': PE_EVIDENCE_NAME,
        'generated_pe_bundle_sha256': digest(evidence),
        'tracked_source_sha256': tracked_source_hashes(root),
    }


def differences(label: str, first: dict, second: dict, limit: int = 15) -> list[str]:
    mismatched = [key for key in sorted(first.keys() | second.keys())
                  if first.get(key) != second.get(key)]
    return [f'{label}: {key}: Windows={first.get(key, "<missing>")} '
            f'Linux={second.get(key, "<missing>")}' for key in mismatched[:limit]] + (
            [f'{label}: plus {len(mismatched)-limit} more differences']
            if len(mismatched) > limit else [])


def verify_manifest_against_archive(m: dict, archive: Path) -> list[str]:
    failures = []
    if not archive.is_file():
        return [f'Missing runtime archive: {archive}']
    if archive.name != m.get('runtime_zip_name'):
        failures.append(f'Unexpected ZIP filename: {archive.name}')
    if digest(archive) != m.get('runtime_zip_sha256'):
        failures.append(f'ZIP changed after manifest emission: {archive.name}')
    actual = archive_entries(archive)
    if actual != m.get('runtime_entries_sha256'):
        failures.append(f'ZIP entries changed after manifest emission: {archive.name}')
        failures += differences('ZIP entry verification', m.get('runtime_entries_sha256', {}), actual)
    return failures


def verify_pe_evidence(manifest: dict, evidence: Path) -> list[str]:
    """Verify each *downloaded* compiled binary against the emitter's digest."""
    if not evidence.is_file():
        return [f'Missing raw PE evidence archive: {evidence}']
    errors = []
    if evidence.name != manifest.get('generated_pe_bundle_name'):
        errors.append(f'Unexpected PE evidence filename: {evidence.name}')
    if digest(evidence) != manifest.get('generated_pe_bundle_sha256'):
        errors.append(f'PE evidence archive changed after manifest emission: {evidence.name}')
    actual = archive_entries(evidence)
    expected = manifest.get('generated_pe_sha256')
    if not isinstance(expected, dict) or actual != expected:
        errors.append('Raw PE evidence differs from generated_pe_sha256')
        if isinstance(expected, dict):
            errors.extend(differences('PE evidence', expected, actual))
    return errors


def compare_builds(windows_manifest: dict, linux_manifest: dict,
                   windows_archive: Path, linux_archive: Path,
                   windows_pe: Path, linux_pe: Path,
                   expected_commit: str | None = None) -> tuple[dict | None, list[str]]:
    w, l = windows_manifest, linux_manifest
    errors = []
    for label, m, host, archive, evidence in [
            ('Windows', w, 'windows', windows_archive, windows_pe),
            ('Linux', l, 'linux', linux_archive, linux_pe)]:
        if m.get('schema') != SCHEMA:
            errors.append(f'{label}: unsupported manifest schema')
        if m.get('host') != host:
            errors.append(f'{label}: expected {host!r} host, got {m.get("host")!r}')
        if m.get('local_verification') != 'three-way-bit-identical':
            errors.append(f'{label}: missing same-host verification')
        for key in ('generated_pe_sha256', 'runtime_entries_sha256', 'tracked_source_sha256'):
            if not isinstance(m.get(key), dict) or not m[key]:
                errors.append(f'{label}: missing/empty {key}')
        errors.extend(verify_manifest_against_archive(m, archive))
        errors.extend(verify_pe_evidence(m, evidence))
        if expected_commit is not None and m.get('source_commit') != expected_commit:
            errors.append(f'{label}: source commit is not CI checkout {expected_commit}')
    for key in ('source_commit', 'python_version', 'llvm_versions', 'runtime_zip_name',
                'runtime_zip_sha256', 'generated_pe_bundle_name',
                'generated_pe_bundle_sha256'):
        if w.get(key) != l.get(key):
            errors.append(f'{key} differs: Windows={w.get(key)!r} Linux={l.get(key)!r}')
    for key in ('tracked_source_sha256', 'generated_pe_sha256', 'runtime_entries_sha256'):
        a, b = w.get(key), l.get(key)
        if isinstance(a, dict) and isinstance(b, dict):
            errors.extend(differences(key, a, b))
    # Critically, equal decompressed entries are not enough. The container
    # itself, including metadata, storage and ordering, must be identical.
    if windows_archive.is_file() and linux_archive.is_file():
        if digest(windows_archive) != digest(linux_archive):
            errors.append('Raw runtime ZIPs are NOT byte-for-byte identical '
                          '(even if all decompressed entries match)')
    if windows_pe.is_file() and linux_pe.is_file():
        if digest(windows_pe) != digest(linux_pe):
            errors.append('Raw PE evidence ZIPs are NOT byte-for-byte identical')
    if errors:
        return None, errors
    return {
        'schema': SCHEMA,
        'verification': 'windows-linux-byte-identical',
        'source_commit': w['source_commit'],
        'python_version': w['python_version'],
        'llvm_versions': w['llvm_versions'],
        'runtime_zip_name': w['runtime_zip_name'],
        'runtime_zip_sha256': w['runtime_zip_sha256'],
        'generated_pe_bundle_sha256': w['generated_pe_bundle_sha256'],
        'generated_pe_sha256': w['generated_pe_sha256'],
        'tracked_source_count': len(w['tracked_source_sha256']),
        'runtime_entry_count': len(w['runtime_entries_sha256']),
        'scope': 'Windows and Linux CI builds of Win32 PE binaries; not gameplay/hardware certification',
    }, []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    p = sub.add_parser('emit', help='On a build runner, emit a validated build evidence manifest')
    p.add_argument('--llvm', required=True, help='Required full LLVM version, e.g. 19.1.7')
    p.add_argument('--out', type=Path, required=True)
    p = sub.add_parser('compare', help='Compare downloaded Windows and Linux runtime bundles')
    p.add_argument('--windows', type=Path, required=True, help='Directory containing manifest.json and the runtime ZIP')
    p.add_argument('--linux', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--expected-commit', help='Fail if evidence is not for the exact CI checkout SHA')
    args = parser.parse_args()
    try:
        if args.action == 'emit':
            args.out.unlink(missing_ok=True)  # a failed emission cannot retain an old report
            archive = ROOT / DEFAULT_ZIP
            report = create_manifest(ROOT, archive, args.llvm)
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
            print(f'BUILD EVIDENCE: {args.out} ({len(report["generated_pe_sha256"])} PE files)')
            return 0
        args.out.unlink(missing_ok=True)  # never retain stale success on failure
        w = json.loads((args.windows/'manifest.json').read_text(encoding='utf-8'))
        l = json.loads((args.linux/'manifest.json').read_text(encoding='utf-8'))
        wzip = args.windows / w.get('runtime_zip_name', 'MISSING.zip')
        lzip = args.linux / l.get('runtime_zip_name', 'MISSING.zip')
        wpe = args.windows / w.get('generated_pe_bundle_name', 'MISSING-PE.zip')
        lpe = args.linux / l.get('generated_pe_bundle_name', 'MISSING-PE.zip')
        cert, errors = compare_builds(w, l, wzip, lzip, wpe, lpe,
                                      expected_commit=args.expected_commit)
        if errors:
            print('FAIL: cross-platform reproducibility not certified:')
            for message in errors[:65]:
                print(' -', message)
            return 1
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(cert, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        print(f'PASS: cross-platform byte identity certified: {cert["runtime_zip_sha256"]}')
        return 0
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError, zipfile.BadZipFile) as exc:
        print('FAIL: cross-platform verification:', exc, file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
