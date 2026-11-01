#!/usr/bin/env python3
# v0.5.0 SOURCE COMMENTARY — Engineering/research utility
# Supports repeatable data generation, audio tests, game-file analysis, or Wine
# probing. Inspect command-line arguments and preserve user-owned game files.
"""Optional Alice A3D card-detection workaround, **only to a new copy**.

Default is a read-only check. This is not required if the original game
already opens the provider; never use it to bypass a validation failure in
an unrelated version of the executable. Does not include game binaries.
"""
import argparse
import hashlib
from pathlib import Path

ORIGINAL = bytes.fromhex('B000520053E87095070083C40885C0751A')
PATCHED  = bytes.fromhex('B000520053E87095070083C40885C0741A')


def inspect(data: bytes):
    return data.count(ORIGINAL), data.count(PATCHED)


def patch(data: bytes) -> bytes:
    unpatched, patched = inspect(data)
    if unpatched != 1 or patched != 0:
        raise ValueError(f'Unexpected Alice binary; original={unpatched}, patched={patched}. Refusing patch.')
    output = data.replace(ORIGINAL, PATCHED, 1)
    assert len(output) == len(data)
    return output


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('alice_exe', type=Path)
    ap.add_argument('--write', action='store_true', help='Create Alice-A3D2-test.exe beside the original; never edit the original')
    args = ap.parse_args()
    exe = args.alice_exe.resolve(strict=True)
    if exe.name.lower() != 'alice.exe':
        ap.error('The source must be named Alice.exe')
    raw = exe.read_bytes()
    before, after = inspect(raw)
    print('Original sha256:', hashlib.sha256(raw).hexdigest())
    print(f'Known hardware-detection original pattern count: {before}; already-patched: {after}')
    if not args.write:
        print('READ-ONLY MODE. Nothing modified. Pass --write to create a separate test copy.')
        return
    out = exe.with_name('Alice-A3D2-test.exe')
    if out.exists():
        ap.error(f'Output already exists: {out}. Refusing to overwrite.')
    try:
        result = patch(raw)
    except ValueError as err:
        ap.error(str(err))
    # Exclusive create avoids racing/overwriting preexisting files.
    with out.open('xb') as fh:
        fh.write(result)
    print('Created:', out)
    print('Copy sha256:', hashlib.sha256(result).hexdigest())
    print('Original unchanged:', hashlib.sha256(exe.read_bytes()).digest() == hashlib.sha256(raw).digest())


if __name__ == '__main__':
    main()
