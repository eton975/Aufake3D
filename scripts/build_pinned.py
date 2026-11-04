#!/usr/bin/env python3
"""One-click *CI-reference-gated* Win32 build on x64 Windows and Linux.

Never trust a version string from a system compiler: download the actual LLVM
19.1.7 release archive and the uv 0.10.0 archive by pinned SHA-256 into a
private user cache, then use precisely Python 3.13.7. Preserve the existing
three-independent-build proof, and compare every runtime ZIP byte to the
verified four-OS CI reference. A mismatch is a failure, NOT certification.

This program does not elevate, modify system PATH/registry, patch games or
claim arbitrary source revisions will produce the reference's hash.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
LLVM_VERSION = '19.1.7'
UV_VERSION = '0.10.0'
PYTHON_VERSION = '3.13.7'
# Exact SHA-256 from successful main-branch 2026-11-04 Actions run 41767660727.
# This is a v0.9.2 reference, NOT a hash for arbitrary future source commits.
REFERENCE_ZIP_SHA256 = 'a64f99e63e235e310c4d8dd45dff05f7b77271d744c9d060a9ca84a9b28f3848'
REFERENCE_COMMIT = 'e390fdb3063d01ae56e09d84c5930124c324e4af'
DEFAULT_REFERENCE = ROOT / 'scripts/ci_reference_v092.json'
RUNTIME_ZIP = ROOT / 'dist/Aufake3D_v0.9.2_Local_Runtime.zip'

# Hashes of official *archive bytes*, not of version strings. The Linux LLVM
# archive is large (~1.65 GB); downloaded bytes and extracted toolchain live
# outside the source tree and are never copied into the clean-build replicas.
ASSETS = {
    'linux': {
        'llvm': ('https://github.com/llvm/llvm-project/releases/download/llvmorg-19.1.7/LLVM-19.1.7-Linux-X64.tar.xz',
                 '4a5ec53951a584ed36f80240f6fbf8fdd46b4cf6c7ee87cc2d5018dc37caf679'),
        'uv': ('https://github.com/astral-sh/uv/releases/download/0.10.0/uv-x86_64-unknown-linux-gnu.tar.gz',
               '230e328948c92dd1ebad83949c4d56e83813dfe9c6362a4c519e6a227973f1ae'),
    },
    'windows': {
        # The LLVM 19.1.7 Windows archive comes from the same upstream build
        # family as the CI-installed win64.exe. The SHA gate tests output identity.
        'llvm': ('https://github.com/llvm/llvm-project/releases/download/llvmorg-19.1.7/clang+llvm-19.1.7-x86_64-pc-windows-msvc.tar.xz',
                 'b4557b4f012161f56a2f5d9e877ab9635cafd7a08f7affe14829bd60c9d357f0'),
        'uv': ('https://github.com/astral-sh/uv/releases/download/0.10.0/uv-x86_64-pc-windows-msvc.zip',
               '4037b444541f695cd2eb93188a9346de3e334af562381411deade0a31c7bf898'),
    },
}


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def cache_root(env: dict[str, str] | None = None) -> Path:
    env = os.environ if env is None else env
    override = env.get('A3D_PINNED_CACHE')
    if override:
        root = Path(override).expanduser().resolve()
    elif os.name == 'nt':
        root = (Path(env.get('LOCALAPPDATA', str(Path.home()))) / 'Aufake3D' / 'pinned-builds').resolve()
    else:
        root = (Path(env.get('XDG_CACHE_HOME', str(Path.home() / '.cache'))) / 'aufake3d' / 'pinned-builds').resolve()
    try:
        root.relative_to(ROOT.resolve())
    except ValueError:
        return root
    raise RuntimeError('Pinned tool cache must be outside the Aufake3D checkout')


def download_verified(url: str, expected_sha256: str, target: Path) -> Path:
    """Stream into a temporary file and atomically publish only checked bytes."""
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_file() and sha_file(target) == expected_sha256:
        return target
    if os.environ.get('A3D_PINNED_OFFLINE') == '1':
        raise RuntimeError(f'Offline and pinned archive is missing or corrupt: {target}')
    print('Downloading pinned build input:', url, flush=True)
    with tempfile.NamedTemporaryFile(dir=target.parent, suffix='.part', delete=False) as tmp:
        part = Path(tmp.name)
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'Aufake3D-pinned-build/1.0'})
            with urllib.request.urlopen(request, timeout=90) as response:
                shutil.copyfileobj(response, tmp, length=1024 * 1024)
        except BaseException:
            part.unlink(missing_ok=True)
            raise
    actual = sha_file(part)
    if actual != expected_sha256:
        part.unlink(missing_ok=True)
        raise RuntimeError(f'Pinned download SHA-256 mismatch for {url}: {actual} != {expected_sha256}')
    part.replace(target)
    return target


def extract_llvm(archive: Path, dest: Path) -> None:
    """Use system tar only for extracting a hash-verified upstream LLVM archive."""
    if shutil.which('tar') is None:
        raise RuntimeError('tar is required to unpack upstream LLVM (Windows 10 includes tar.exe)')
    dest.mkdir(parents=True, exist_ok=True)
    subprocess.run(['tar', '-xJf', str(archive), '-C', str(dest), '--strip-components=1'], check=True)


def pinned_llvm(cache: Path, host: str) -> Path:
    url, sha = ASSETS[host]['llvm']
    target = cache / 'llvm-19.1.7' / host
    bin_dir = target / 'bin'
    suffix = '.exe' if host == 'windows' else ''
    executables = [bin_dir / ('clang' + suffix), bin_dir / ('lld-link' + suffix)]
    stamp = target / '.aufake3d-checked.json'
    if stamp.is_file() and all(p.is_file() for p in executables):
        try:
            record = json.loads(stamp.read_text(encoding='utf-8'))
            if record == {
                'archive_sha256': sha,
                'clang_sha256': sha_file(executables[0]),
                'lld_sha256': sha_file(executables[1]),
            }:
                return bin_dir
        except (OSError, ValueError, KeyError):
            pass
    if target.exists():
        shutil.rmtree(target)
    filename = url.rsplit('/', 1)[-1]
    archive = download_verified(url, sha, cache / 'downloads' / filename)
    staging = target.with_name(target.name + '-unpacked')
    if staging.exists():
        shutil.rmtree(staging)
    try:
        extract_llvm(archive, staging)
        bins = [staging / 'bin' / p.name for p in executables]
        if not all(p.is_file() for p in bins):
            raise RuntimeError('Verified LLVM archive did not contain clang and lld-link')
        metadata = {
            'archive_sha256': sha,
            'clang_sha256': sha_file(bins[0]),
            'lld_sha256': sha_file(bins[1]),
        }
        (staging / '.aufake3d-checked.json').write_text(json.dumps(metadata, sort_keys=True) + '\n', encoding='utf-8')
        staging.rename(target)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
        # Avoid retaining a ~1.65 GB archive in addition to the LLVM tree.
        archive.unlink(missing_ok=True)
    return bin_dir


def pinned_uv(cache: Path, host: str) -> Path:
    import tarfile
    import zipfile
    url, sha = ASSETS[host]['uv']
    suffix = '.exe' if host == 'windows' else ''
    target = cache / 'uv-0.10.0' / host / ('uv' + suffix)
    stamp = target.parent / '.aufake3d-uv-sha256'
    if target.is_file() and stamp.is_file() and stamp.read_text().strip() == sha_file(target):
        proc = subprocess.run([str(target), '--version'], capture_output=True, text=True, check=True)
        if proc.stdout.strip() == f'uv {UV_VERSION}':
            return target
    target.parent.mkdir(parents=True, exist_ok=True)
    archive = download_verified(url, sha, cache / 'downloads' / url.rsplit('/', 1)[-1])
    if host == 'windows':
        with zipfile.ZipFile(archive) as z:
            members = [x for x in z.namelist() if x.rstrip('/').split('/')[-1] == 'uv.exe']
            if len(members) != 1:
                raise RuntimeError('Invalid pinned uv Windows archive: missing/ambiguous uv.exe')
            binary = z.read(members[0])
    else:
        with tarfile.open(archive, 'r:gz') as z:
            members = [x for x in z.getmembers() if x.isfile() and x.name.split('/')[-1] == 'uv']
            if len(members) != 1:
                raise RuntimeError('Invalid pinned uv Linux archive: missing/ambiguous uv executable')
            binary = z.extractfile(members[0]).read()
    target.write_bytes(binary)
    if host == 'linux':
        target.chmod(0o755)
    stamp.write_text(sha_file(target) + '\n', encoding='ascii')
    archive.unlink(missing_ok=True)
    proc = subprocess.run([str(target), '--version'], capture_output=True, text=True, check=True)
    if proc.stdout.strip() != f'uv {UV_VERSION}':
        raise RuntimeError(f'Expected uv {UV_VERSION}: {proc.stdout!r}')
    return target


def pinned_python(cache: Path, uv: Path) -> Path:
    env = dict(os.environ)
    env['UV_PYTHON_INSTALL_DIR'] = str(cache / 'python-3.13.7')
    env['UV_CACHE_DIR'] = str(cache / 'uv-cache')
    # --no-bin / --no-registry prevent persistent PATH/registry modifications.
    subprocess.run([str(uv), '--no-config', 'python', 'install', '--managed-python', '--no-bin',
                    '--no-registry', PYTHON_VERSION], env=env, check=True)
    proc = subprocess.run([str(uv), '--no-config', 'python', 'find', '--managed-python',
                           '--no-python-downloads', PYTHON_VERSION], env=env,
                          capture_output=True, text=True, check=True)
    python = Path(proc.stdout.strip())
    if not python.is_file():
        raise RuntimeError('Pinned managed Python executable does not exist: ' + str(python))
    output = subprocess.run([str(python), '-c', 'import sys; print(".".join(map(str, sys.version_info[:3])))'],
                            capture_output=True, text=True, check=True).stdout.strip()
    if output != PYTHON_VERSION:
        raise RuntimeError(f'Managed Python mismatch: {output} instead of {PYTHON_VERSION}')
    return python


def assert_versions(bin_dir: Path, env: dict[str, str]) -> None:
    for name, prefix in [('clang', 'clang version'), ('lld-link', 'LLD')]:
        executable = bin_dir / (name + ('.exe' if os.name == 'nt' else ''))
        proc = subprocess.run([str(executable), '--version'], env=env,
                              capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f'Upstream LLVM {name} cannot run: {proc.stderr.strip()}\n'
                               'If Linux is missing libxml2.so.2, install its ABI-compatible dependency '
                               'or use the checked private libxml2 build documented for Ubuntu CI.')
        if not re.search(r'\b' + re.escape(prefix) + r'\s+19\.1\.7\b', proc.stdout):
            raise RuntimeError('Wrong LLVM toolchain: ' + proc.stdout[:200])


def build_env(cache: Path, python: Path, llvm_bin: Path) -> dict[str, str]:
    env = dict(os.environ)
    env['PYTHONHASHSEED'] = '0'
    env['SOURCE_DATE_EPOCH'] = '1767225600'
    # Project build scripts and their two clean replicas inherit the same tools.
    path_parts = [str(llvm_bin), str(python.parent)]
    env['PATH'] = os.pathsep.join(path_parts + [env.get('PATH', '')])
    if os.name != 'nt':
        env['LD_LIBRARY_PATH'] = str(llvm_bin.parent / 'lib') + os.pathsep + env.get('LD_LIBRARY_PATH', '')
    return env


def load_reference(filename: Path) -> dict:
    data = json.loads(filename.read_text(encoding='utf-8'))
    pe = data.get('generated_pe_sha256')
    if (data.get('schema') != 1 or data.get('python_version') != PYTHON_VERSION or
            data.get('llvm_versions') != {'clang': LLVM_VERSION, 'lld-link': LLVM_VERSION} or
            not isinstance(pe, dict) or len(pe) < 15 or
            not all(re.fullmatch('[0-9a-f]{64}', x) for x in pe.values()) or
            not re.fullmatch('[0-9a-f]{64}', str(data.get('runtime_zip_sha256', '')))):
        raise RuntimeError('Invalid/untrusted CI reference format: ' + str(filename))
    return data


def check_compiled_pe_bytes(reference: dict) -> None:
    # Include ALL 20 generated PE files, not only those staged into the ZIP.
    from scripts.verify_reproducible import compiled_pe_hashes
    current = compiled_pe_hashes(ROOT)
    expected = reference['generated_pe_sha256']
    mismatches = [name for name in sorted(current.keys() | expected.keys())
                  if current.get(name) != expected.get(name)]
    if mismatches:
        lines = [f' - {name}: local={current.get(name, "<missing>")} CI={expected.get(name, "<missing>")}'
                 for name in mismatches[:25]]
        raise RuntimeError('FAIL: generated Windows PE binaries do not match certified CI evidence:\n' +
                           '\n'.join(lines))
    print(f'PASS: ALL {len(expected)} COMPILED WIN32 PE EXEs/DLLs match certified CI SHA-256 bytes.')


def run_build(cache: Path, extra: list[str], reference: dict) -> int:
    host = 'windows' if os.name == 'nt' else 'linux'
    if platform.machine().lower() not in ('x86_64', 'amd64'):
        raise RuntimeError('The pinned build currently supports x86-64 Windows and Linux hosts only')
    if any(flag in extra for flag in ('--skip-repro-check', '--no-package', '--no-tests')):
        raise RuntimeError('Pinned release builds cannot skip compilation/tests/packaging/reproducibility')
    cache.mkdir(parents=True, exist_ok=True)
    uv = pinned_uv(cache, host)
    python = pinned_python(cache, uv)
    llvm_bin = pinned_llvm(cache, host)
    env = build_env(cache, python, llvm_bin)
    if host == 'linux':
        probe = subprocess.run([str(llvm_bin / 'lld-link'), '--version'], env=env,
                               capture_output=True, text=True)
        if probe.returncode != 0 and 'libxml2.so.2' in probe.stderr:
            print('LLVM requires private libxml2.so.2; compiling checksum-pinned compatibility library.')
            subprocess.run(['bash', str(ROOT / 'scripts/local_prepare_llvm_compat.sh'),
                            str(llvm_bin.parent), str(cache / 'legacy-libxml2')],
                           env=env, check=True)
    assert_versions(llvm_bin, env)
    print('Using pinned upstream LLVM', LLVM_VERSION, 'and managed Python', PYTHON_VERSION, flush=True)
    subprocess.run([str(python), str(ROOT / 'scripts/build.py'), *extra], cwd=ROOT, env=env, check=True)
    # The main builder must have generated the independent three-build report.
    subprocess.run([str(python), str(ROOT / 'scripts/verify_reproducible.py'), '--check-report'],
                   cwd=ROOT, env=env, check=True)
    actual = sha_file(RUNTIME_ZIP)
    expected_sha256 = reference['runtime_zip_sha256']
    if actual != expected_sha256:
        raise RuntimeError('FAIL: local runtime differs from certified CI bytes!\n'
                           f' local SHA-256: {actual}\n expected SHA-256: {expected_sha256}\n'
                           'Run scripts/verify_reproducible.py --compare with the CI runtime ZIP '
                           'to identify differing entries. No cross-host certificate has been issued.')
    check_compiled_pe_bytes(reference)
    print('PASS: LOCAL RUNTIME ZIP SHA-256 IDENTICAL TO PINNED FOUR-TARGET CI REFERENCE:', actual)
    print('NOTE: local CI-reference match, not a new four-host certificate or gameplay test.')
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    p.add_argument('--doctor', action='store_true', help='Show pinned build configuration (no downloads)')
    p.add_argument('--reference-file', type=Path, default=DEFAULT_REFERENCE,
                   help='CI-verified manifest-derived reference, including all PE hashes')
    opts, forwarded = p.parse_known_args(argv)
    try:
        reference = load_reference(opts.reference_file)
        cache = cache_root()
        if opts.doctor:
            print('Pinned LLVM:', LLVM_VERSION, 'upstream,', ASSETS['windows' if os.name == 'nt' else 'linux']['llvm'][0])
            print('Pinned uv:', UV_VERSION, '| managed CPython:', PYTHON_VERSION)
            print('Toolchain cache (outside checkout):', cache)
            print('CI reference: commit', reference['source_commit'], 'ZIP SHA-256', reference['runtime_zip_sha256'])
            return 0
        return run_build(cache, forwarded, reference)
    except (RuntimeError, ValueError, OSError, subprocess.CalledProcessError) as exc:
        print('PINNED BUILD FAILED:', exc, file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
