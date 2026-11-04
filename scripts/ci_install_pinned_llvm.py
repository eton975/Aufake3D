#!/usr/bin/env python3
"""Provision checked LLVM 19.1.7 for Actions without a Node.js 20 action.

Reuses the exact official LLVM release archive URLs and hardcoded SHA-256s
of the existing local reproducible-build toolchain. Never installs under the
Git checkout; the two clean-build copies must not include compiler binaries.
"""
from __future__ import annotations

import os
from pathlib import Path
import platform
import sys

from build_pinned import LLVM_VERSION, cache_root, pinned_llvm


def provision(env: dict[str, str] | None = None) -> Path:
    """Export LLVM to future Actions steps, after verifying archive SHA-256."""
    e = os.environ if env is None else env
    required = ('RUNNER_TEMP', 'GITHUB_PATH', 'GITHUB_ENV')
    missing = [name for name in required if not e.get(name)]
    if missing:
        raise RuntimeError('Required GitHub Actions environment missing: ' + ', '.join(missing))
    if platform.machine().lower() not in ('x86_64', 'amd64'):
        raise RuntimeError('The pinned LLVM 19.1.7 assets require x86-64')
    host = 'windows' if os.name == 'nt' else 'linux'
    # Select a transient compiler cache outside the workspace for the three
    # independent-build test. This is NOT a fallback to the host LLVM.
    cache = (Path(e['RUNNER_TEMP']).resolve() / 'aufake3d-pinned-ci-llvm')
    e['A3D_PINNED_CACHE'] = str(cache)
    bin_dir = pinned_llvm(cache_root(e), host)
    suffix = '.exe' if host == 'windows' else ''
    for tool in ('clang', 'lld-link'):
        if not (bin_dir / (tool + suffix)).is_file():
            raise RuntimeError('Pinned LLVM missing required binary: ' + tool)

    with Path(e['GITHUB_PATH']).open('a', encoding='utf-8', newline='\n') as handle:
        handle.write(str(bin_dir) + '\n')
    with Path(e['GITHUB_ENV']).open('a', encoding='utf-8', newline='\n') as handle:
        handle.write('LLVM_PATH=' + str(bin_dir.parent) + '\n')
        if host == 'linux':
            library_path = str(bin_dir.parent / 'lib')
            previous = e.get('LD_LIBRARY_PATH', '')
            handle.write('LD_LIBRARY_PATH=' + library_path + (os.pathsep + previous if previous else '') + '\n')
    print('Installed SHA-256-pinned official LLVM', LLVM_VERSION, 'at', bin_dir)
    print('LLVM binaries are outside the Git checkout; no Node.js action required.')
    return bin_dir


def main() -> int:
    try:
        provision()
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print('CI PINNED LLVM INSTALL FAILED:', exc, file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
