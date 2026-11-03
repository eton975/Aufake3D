#!/usr/bin/env python3
"""Independent, source-only, deterministic five-way Alice audio reference target.

Deliberately does NOT import or invoke the core Aufake3D Win32 build system.
Python stdlib only for packaging; numpy/scipy are used by the optional tests
and packaged WAV analyzer, not by this builder.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'Audio_Reference'
DIST = ROOT / 'dist' / 'audio-reference'
RELEASE = '0.9.2'
PACKAGE_ROOT = 'Aufake3D_Alice_Five_Way_Audio_Test_Kit'
OUTPUT_NAME = f'Aufake3D_Alice_Five_Way_Audio_Reference_Kit_v{RELEASE}.zip'
# Intentional source allowlist: captured WAVs, user DM3s, game assets and
# generated reports MUST NOT accidentally enter distributed releases.
INPUTS = tuple(sorted([
    *('ALICE_BASE_CFGS/' + s for s in (
        'a3d5_load_hedge1.cfg', 'a3d5_play_2000.cfg', 'a3d5_play_2011.cfg',
        'a3d5_record_2000.cfg', 'a3d5_record_2011.cfg', 'a3d5_setup.cfg',
        'a3d5_stage.cfg', 'a3d5_stop.cfg')),
    'CAPTURE_WORKSHEET.md', 'README_FIRST.md', 'VERSION.txt',
    'profiles/five_way.json', 'recordings/PLACE_WAVS_HERE.txt',
    'requirements.txt', 'tests/test_analyzer.py', 'tests/test_audio_formats.py',
    'tools/analyze_five_way.py', 'tools/demo_sha256.py',
    'tools/make_synthetic_fixture.py',
]))


def fail(message: str):
    raise SystemExit('ERROR: ' + message)


def _read_inputs():
    result = {}
    for name in INPUTS:
        path = SRC / name
        if not path.is_file():
            fail(f'Missing audio-reference source: {path}')
        data = path.read_bytes()
        if not data:
            fail(f'Empty audio-reference source: {path}')
        result[name] = data
    return result


def package_files():
    result = _read_inputs()
    checksums = ''.join(
        f'{hashlib.sha256(data).hexdigest()}  {name}\n'
        for name, data in sorted(result.items())
    ).encode('ascii')
    result['SHA256SUMS.txt'] = checksums
    return result


def produce_zip() -> bytes:
    payload = package_files()
    stream = io.BytesIO()
    # Stored (uncompressed) entries avoid zlib version differences across
    # Windows and Linux and preserve cross-host byte-for-byte ZIP identity.
    with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_STORED, allowZip64=True) as z:
        for path, data in sorted(payload.items()):
            item = zipfile.ZipInfo(f'{PACKAGE_ROOT}/{path}', date_time=(1980,1,1,0,0,0))
            item.create_system = 3
            item.external_attr = 0o100644 << 16
            item.compress_type = zipfile.ZIP_STORED
            z.writestr(item, data)
    return stream.getvalue()


def _verify_zip(data: bytes, require_source_match=True) -> str:
    with zipfile.ZipFile(io.BytesIO(data), 'r') as z:
        infos = z.infolist()
        names = [v.filename for v in infos]
        expected = {f'{PACKAGE_ROOT}/{n}' for n in INPUTS}
        expected.add(f'{PACKAGE_ROOT}/SHA256SUMS.txt')
        if len(names) != len(expected) or set(names) != expected or len(names) != len(set(names)):
            fail('Archive contains missing, duplicate or unexpected files')
        if any(n.startswith('/') or '..' in Path(n).parts for n in names):
            fail('Unsafe archive path')
        if any(i.compress_type != zipfile.ZIP_STORED for i in infos):
            fail('Unexpected compression type')
        if z.testzip() is not None:
            fail('Corrupted ZIP member')
        members = {i.filename[len(PACKAGE_ROOT)+1:]:z.read(i) for i in infos}
        expected_manifest = ''.join(
            f'{hashlib.sha256(members[name]).hexdigest()}  {name}\n'
            for name in INPUTS
        ).encode('ascii')
        if members['SHA256SUMS.txt'] != expected_manifest:
            fail('Member SHA256 manifest mismatch')
        if require_source_match and members != package_files():
            fail('Built package differs from current audio-reference source files')
    return hashlib.sha256(data).hexdigest()


def run_tests():
    command = [sys.executable, '-m', 'unittest', 'discover', '-s',
               str(SRC / 'tests'), '-p', 'test_*.py', '-v']
    print('Running five-way analyzer regressions:', ' '.join(command), flush=True)
    proc = subprocess.run(command, cwd=ROOT, check=False)
    if proc.returncode:
        fail('Audio reference analyzer tests failed. For dependencies: '
             'python -m pip install -r Audio_Reference/requirements.txt')


def doctor():
    print('Aufake3D independent audio-reference build doctor')
    print('Python:', sys.version.split()[0])
    print('Source:', SRC)
    print('Files:', len(_read_inputs()))
    try:
        import numpy  # noqa: F401
        import scipy  # noqa: F401
        print('Analyzer dependencies: available (NumPy + SciPy)')
    except ImportError:
        print('Analyzer dependencies: NOT installed (not needed for package build)')
        print('Install for tests/analysis: python -m pip install -r Audio_Reference/requirements.txt')
    print('Core Win32 compiler/toolchain: NOT required')
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--doctor', action='store_true', help='Check files and optional dependencies')
    mode.add_argument('--test', action='store_true', help='Run analyzer tests only (needs NumPy and SciPy)')
    mode.add_argument('--verify', action='store_true', help='Verify existing built ZIP against sources')
    mode.add_argument('--emit', type=Path, metavar='ZIP', help=argparse.SUPPRESS)
    parser.add_argument('--out', type=Path, default=DIST / OUTPUT_NAME,
                        help='Output ZIP (default: dist/audio-reference/)')
    opts = parser.parse_args(argv)
    if sys.version_info < (3,10):
        fail('Python 3.10+ is required')
    if opts.doctor:
        return doctor()
    if opts.test:
        run_tests()
        print('Audio-reference tests PASSED')
        return 0
    if opts.verify:
        if not opts.out.is_file():
            fail('No audio-reference ZIP to verify: ' + str(opts.out))
        digest = _verify_zip(opts.out.read_bytes())
        # Canonical ZIP bytes and ordering must match, not just member hashes.
        if opts.out.read_bytes() != produce_zip():
            fail('ZIP metadata/order differs from canonical deterministic build')
        print('Audio-reference archive VERIFIED:', opts.out)
        print('SHA-256:', digest)
        return 0
    if opts.emit is not None:
        payload = produce_zip()
        _verify_zip(payload)
        opts.emit.parent.mkdir(parents=True, exist_ok=True)
        opts.emit.write_bytes(payload)
        return 0

    # Separate independent Python processes; no core build, no compiler and
    # no silent downgrade of a failed reproducibility test.
    with tempfile.TemporaryDirectory(prefix='aufake3d-audio-ref-') as scratch:
        outputs = []
        for i in range(3):
            path = Path(scratch) / f'candidate_{i}.zip'
            subprocess.run([sys.executable, str(Path(__file__).resolve()),
                            '--emit', str(path)], cwd=ROOT, check=True)
            outputs.append(path.read_bytes())
        if outputs[0] != outputs[1] or outputs[1] != outputs[2]:
            fail('Three-process deterministic archive reproducibility FAILED')
        digest = _verify_zip(outputs[0])
        opts.out.parent.mkdir(parents=True, exist_ok=True)
        tmp = opts.out.with_name(opts.out.name + '.tmp')
        try:
            tmp.write_bytes(outputs[0])
            os.replace(tmp, opts.out)
        finally:
            if tmp.exists():
                tmp.unlink()
    print('Audio-reference build PASS (3 identical independent processes)')
    print('Archive:', opts.out)
    print('SHA-256:', digest)
    print('Contains', len(INPUTS), 'source files plus SHA256SUMS.txt')
    print('Main Aufake3D binaries were NOT compiled or modified.')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, zipfile.BadZipFile, subprocess.CalledProcessError) as exc:
        fail(str(exc))
