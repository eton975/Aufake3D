#!/usr/bin/env python3
"""Fail-closed recovery if the project-hosted slim LLVM release is unavailable.

The independent fallback is the official LLVM 19.1.7 release archive, pinned
by its *whole-archive* SHA-256. Only the files needed by the slim toolchain
are extracted, and the compiler/linker binaries must match the original CI
installed toolchain byte for byte. The finished game runtime must still pass
the existing 20-PE and complete-ZIP CI reference checks.

This is not a compiler-version-only fallback and never replaces system LLVM.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import tarfile

VERSION = '19.1.7'

# Independent of eton975/Aufake3D release assets. Whole archive digests from
# official upstream LLVM 19.1.7 releases, not floating URLs/branch references.
UPSTREAM_ASSETS = {
    'linux': (
        'https://github.com/llvm/llvm-project/releases/download/llvmorg-19.1.7/LLVM-19.1.7-Linux-X64.tar.xz',
        '4a5ec53951a584ed36f80240f6fbf8fdd46b4cf6c7ee87cc2d5018dc37caf679',
    ),
    'windows': (
        'https://github.com/llvm/llvm-project/releases/download/llvmorg-19.1.7/clang+llvm-19.1.7-x86_64-pc-windows-msvc.tar.xz',
        'b4557b4f012161f56a2f5d9e877ab9635cafd7a08f7affe14829bd60c9d357f0',
    ),
}

# SHA-256 logged by the successful upstream-derived slim-package CI build
# (run 41777704477). A different binary with the same version string fails.
CI_COMPILER_SHA256 = {
    'linux': {
        'bin/clang': 'c57e2928bc629e58da157867bb9af550edfc1195e7b003edfcfecd57faf2b71b',
        'bin/lld-link': '75f69d8a4e4a402585d0fc1e59ff97a8d38499f58e5119724e785360dfb0e225',
    },
    'windows': {
        'bin/clang.exe': '56ef1abd0df11a3b1b77822193e927c6345078c24511567ae10b3afd803d03a3',
        'bin/lld-link.exe': '5db15319c74b694483a7c1f8b6a31e9d468c5d4243c700656cbc9f6d6754f9f4',
    },
}


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def selected_input(relative: PurePosixPath, host: str) -> bool:
    """Mirror ci_make_slim_llvm.source_files without unpacking full LLVM."""
    path = relative.as_posix()
    if path in CI_COMPILER_SHA256[host]:
        return True
    parts = relative.parts
    if host == 'windows':
        if len(parts) == 2 and parts[0] == 'bin' and parts[1].lower().endswith('.dll'):
            return True
    else:
        if len(parts) == 2 and parts[0] == 'lib':
            return any(relative.name.startswith(prefix) and '.so' in relative.name
                       for prefix in ('libLLVM', 'libclang-cpp', 'libc++', 'libunwind'))
    if len(parts) >= 5 and parts[:2] == ('lib', 'clang') and parts[3] == 'include':
        return True
    if len(parts) >= 3 and parts[:2] == ('share', 'clang'):
        return True
    return False


def extract_upstream_llvm(archive: Path, destination: Path, host: str) -> dict:
    """Stream only required files from a SHA-verified official full LLVM tar.xz.

    The caller MUST verify the official full archive SHA-256 first. This
    function does not execute the downloaded archive, elevate, or modify PATH.
    Tar symlinks are dereferenced into ordinary files; traversal, duplicate
    entries, and inconsistent root names are rejected. Only the selected
    compiler dependencies can be written into destination.
    """
    if host not in CI_COMPILER_SHA256:
        raise ValueError('Unsupported LLVM host: ' + host)
    destination.mkdir(parents=True, exist_ok=True)
    selected: dict[str, str] = {}
    roots: set[str] = set()
    with tarfile.open(archive, mode='r:xz') as source:
        for member in source:
            raw = PurePosixPath(member.name)
            if raw.is_absolute() or '..' in raw.parts or '\\' in member.name:
                raise RuntimeError('Unsafe upstream LLVM archive member: ' + member.name)
            parts = raw.parts
            if len(parts) < 2:
                continue
            roots.add(parts[0])
            if len(roots) != 1:
                raise RuntimeError('Unexpected multiple top-level LLVM archive directories')
            relative = PurePosixPath(*parts[1:])
            if not selected_input(relative, host):
                continue
            # Upstream tarballs contain normal resource-directory entries
            # (e.g. lib/clang/19/include/cuda_wrappers). The slim packager
            # selects only actual files under those directories.
            if member.isdir():
                continue
            name = relative.as_posix()
            if name in selected:
                raise RuntimeError('Duplicate upstream LLVM selected file: ' + name)
            if not (member.isfile() or member.issym() or member.islnk()):
                raise RuntimeError('Non-file selected upstream LLVM member: ' + name)
            dest = destination.joinpath(*relative.parts)
            dest.parent.mkdir(parents=True, exist_ok=True)
            input_stream = source.extractfile(member)
            if input_stream is None:
                raise RuntimeError('Missing upstream LLVM file bytes: ' + name)
            with input_stream, dest.open('wb') as output:
                shutil.copyfileobj(input_stream, output, length=1024 * 1024)
            if host == 'linux':
                dest.chmod(0o755 if name.startswith('bin/') or '.so' in name else 0o644)
            selected[name] = sha_file(dest)

    for name, expected in CI_COMPILER_SHA256[host].items():
        if selected.get(name) != expected:
            raise RuntimeError(
                f'Official upstream LLVM {host} compiler differs from certified slim compiler: '
                f'{name}: upstream={selected.get(name, "<missing>")} expected={expected}. '
                'Refusing an ABI/version-only substitution.'
            )
    # Use the committed licence from the exact upstream LLVM release tag.
    licence = Path(__file__).resolve().parents[1] / 'ThirdParty' / 'LLVM-19.1.7-LICENSE.TXT'
    if not licence.is_file() or 'Apache License' not in licence.read_text(encoding='utf-8'):
        raise RuntimeError('Pinned upstream LLVM licence is missing')
    shutil.copyfile(licence, destination / 'LLVM_LICENSE.TXT')
    selected['LLVM_LICENSE.TXT'] = sha_file(destination / 'LLVM_LICENSE.TXT')
    manifest = {
        'schema': 1,
        'llvm_version': VERSION,
        'host': host,
        'upstream_release': 'llvmorg-19.1.7',
        'licence': 'LLVM_LICENSE.TXT',
        'recovery_source': 'official-upstream-full-archive',
        'upstream_archive_sha256': UPSTREAM_ASSETS[host][1],
        'files_sha256': dict(sorted(selected.items())),
    }
    (destination / 'AUFAKE3D_LLVM_PROVENANCE.json').write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + '\n', encoding='utf-8'
    )
    print('Verified official upstream LLVM fallback:', len(selected),
          'files, compiler and linker match CI byte for byte.', flush=True)
    return manifest
