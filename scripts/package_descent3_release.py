#!/usr/bin/env python3
"""Deterministic, source-only packager for the retail Descent 3 drop-in A3D DLL kit.

Run automatically by scripts/build.py after the universal core is compiled.
This does NOT build a Descent 3 executable, inject code, register COM, or
modify a retail game installation. The public ZIP contains only the existing
unified Aufake3D DLLs, checksum metadata, and instructions.
"""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import struct
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = '0.9.2'
FILENAME = f'Aufake3D_v{VERSION}_Descent3_Experimental_Win32.zip'
OUTPUT = ROOT / 'dist' / FILENAME
CORE = ('a3d.dll', 'a3dapi.dll')
PREFIX = f'Aufake3D_v{VERSION}_Descent3_Experimental/'
GAME_FOLDER = 'COPY_TO_DESCENT3_GAME_FOLDER/'
ZIP_DATE = (2026, 1, 1, 0, 0, 0)

README = f'''Aufake3D v{VERSION} -- EXPERIMENTAL RETAIL DESCENT 3 AUREAL 3D KIT
================================================================

STATUS: EXPERIMENTAL. One retail Descent 3 user test confirmed that the
unmodified game loaded Aufake3D a3dapi.dll, and that sound was present with
the DLLs, absent without them, and present again after restoring them.
Audio spatialisation, HRTF accuracy, occlusion, reflections, and wide game
compatibility are NOT yet validated. Do not represent this as full support.

INSTALL (Windows x86 retail Descent 3):
1. Exit the game and setup utility completely.
2. Back up any existing a3d.dll and a3dapi.dll next to main.exe. Do not
   overwrite or discard the only copies of your existing game files.
3. Copy BOTH files from COPY_TO_DESCENT3_GAME_FOLDER into the directory
   containing Descent 3's main.exe (not into a Windows system directory).
4. Run the game's normal Setup and select its genuine "Aureal 3D" sound
   mixer. Save settings, then launch the game as normal.
5. If you encounter missing sound or other issues, restore the backed-up
   files and revert the mixer setting in the game's setup.

No installer, admin rights, registry modifications, system DLLs, 3rd-party
Aureal drivers, EXE patches, or source-engine rebuilds are required by this kit.
No game binaries or proprietary Aureal SDK files are distributed here.
The two DLLs are COPIES of the exact same universal Aufake3D core compiled
for the other supported games, NOT a Descent 3-specific rendering fork.

The separate experimental source integration (if used) is NOT in this ZIP.
The synthetic Descent 3 contract-probe executable and .obj development
artifacts are intentionally NOT included in this public end-user kit.

Verify individual DLL bytes against CONTENT_SHA256.json. This archive is
built deterministically (fixed member order/time/permissions, ZIP_STORED),
but consider a build CERTIFIED only when the separately generated same-host
and five-OS reproducibility certificates agree with its exact archive SHA-256.
See https://github.com/eton975/Aufake3D for source, issues, and releases.
'''.encode('utf-8')


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_x86_pe(path: Path, binary: bytes) -> None:
    if len(binary) < 256 or binary[:2] != b'MZ':
        raise ValueError(f'Not a Windows PE binary: {path}')
    pe_off = struct.unpack_from('<I', binary, 0x3C)[0]
    if pe_off > len(binary) - 26 or binary[pe_off:pe_off + 4] != b'PE\0\0':
        raise ValueError(f'Invalid PE header: {path}')
    if struct.unpack_from('<H', binary, pe_off + 4)[0] != 0x14c:
        raise ValueError(f'Expected x86 PE32: {path}')
    if struct.unpack_from('<H', binary, pe_off + 24)[0] != 0x10b:
        raise ValueError(f'Expected PE32 optional header: {path}')


def payload_from_core(core_bytes: dict[str, bytes]) -> dict[str, bytes]:
    files = {}
    if set(core_bytes) != set(CORE):
        raise ValueError('Descent 3 must use exactly the two shared core DLLs')
    for name in CORE:
        data = core_bytes[name]
        validate_x86_pe(Path(name), data)
        files[GAME_FOLDER + name] = data
    files['README_FIRST.txt'] = README
    checksums = {name: sha256(data) for name, data in sorted(files.items())}
    files['CONTENT_SHA256.json'] = (json.dumps({
        'schema': 1, 'version': VERSION, 'compatibility': 'experimental',
        'engine': 'shared-universal-Aufake3D-core',
        'source_game_executable_modified': False,
        'gameplay_and_full_a3d2_fidelity_certified': False,
        'files_sha256': checksums,
    }, indent=2, sort_keys=True) + '\n').encode('utf-8')
    return files


def payload(root: Path = ROOT) -> dict[str, bytes]:
    core = {name: (root / 'dist' / 'core' / name).read_bytes() for name in CORE}
    return payload_from_core(core)


def make_zip(files: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', compression=zipfile.ZIP_STORED) as archive:
        for name, data in sorted(files.items()):
            if name.startswith('/') or '\\' in name or '..' in name.split('/'):
                raise ValueError('Invalid public ZIP member name')
            info = zipfile.ZipInfo(PREFIX + name, date_time=ZIP_DATE)
            info.create_system = 3  # identical ZIP metadata on Windows/Linux
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_STORED
            archive.writestr(info, data)
    return buf.getvalue()


def verify_archive(archive_bytes: bytes, expected: dict[str, bytes]) -> None:
    with zipfile.ZipFile(io.BytesIO(archive_bytes), 'r') as archive:
        info = archive.infolist()
        names = [member.filename for member in info]
        if names != sorted(PREFIX + key for key in expected):
            raise RuntimeError('Unexpected, duplicated or unsorted Descent 3 ZIP members')
        for member in info:
            if (member.date_time != ZIP_DATE or member.create_system != 3 or
                    member.compress_type != zipfile.ZIP_STORED or
                    (member.external_attr >> 16) != 0o100644):
                raise RuntimeError('Non-deterministic Descent 3 ZIP metadata')
            if archive.read(member) != expected[member.filename[len(PREFIX):]]:
                raise RuntimeError('Descent 3 ZIP member mismatch: ' + member.filename)
        if archive.testzip():
            raise RuntimeError('Descent 3 ZIP CRC failure')


def build(root: Path = ROOT, output: Path | None = None) -> Path:
    out = output or root / 'dist' / FILENAME
    sidecar = out.parent / 'DESCENT3_PUBLIC_RELEASE_SHA256.json'
    # A failed standalone packager invocation must never preserve stale output.
    out.unlink(missing_ok=True)
    sidecar.unlink(missing_ok=True)
    files = payload(root)
    first, second = make_zip(files), make_zip(files)
    if first != second:
        raise RuntimeError('Two independent in-memory archive assemblies differ')
    verify_archive(first, files)
    out.parent.mkdir(parents=True, exist_ok=True)
    temp = out.with_name(out.name + '.incomplete')
    try:
        temp.write_bytes(first)
        if sha256(temp.read_bytes()) != sha256(first):
            raise RuntimeError('Descent 3 public ZIP changed during write')
        temp.replace(out)
    finally:
        temp.unlink(missing_ok=True)
    # Strictly supplemental report, not self-referential inside the ZIP.
    sidecar.write_text(json.dumps({
        'schema': 1, 'status': 'EXPERIMENTAL; certificate required for release claims',
        'archive': out.name, 'archive_sha256': sha256(first),
        'core_dll_sha256': {n: sha256(files[GAME_FOLDER + n]) for n in CORE},
    }, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print('Descent 3 public experimental ZIP:', out, flush=True)
    print('SHA-256:', sha256(first), flush=True)
    return out


if __name__ == '__main__':
    try:
        build()
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile) as exc:
        print('DESCENT 3 PUBLIC RELEASE PACKAGING FAILED:', exc, file=sys.stderr)
        raise SystemExit(1)
