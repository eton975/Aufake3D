#!/usr/bin/env python3
# v0.5.0 SOURCE COMMENTARY — Installer / launcher support
# Supports reversible game-local deployment and diagnostics; the original executable
# and vendor Miles modules should remain untouched.
"""Install an experimental *application-local* A3D replacement safely.

This tool deliberately does not register system-wide COM classes or edit the
original game binary. It creates a sidecar Win32 activation-context manifest
and copies our independently authored Windows x86 DLL(s) beside the game.

Manifest activation is a testable route to a drop-in installer, but it is NOT
proved to work on every Windows build or Wine version. Use the included 32-bit
COM canary with the same manifest to distinguish registration-free activation
from ordinary COM registry activation.

For Alice versions with the documented A3D hardware gate, --patch-alice
creates Alice-A3D2.exe by changing one guarded conditional jump. The source
Alice.exe stays untouched. We never overwrite existing files. A manifest may
not take precedence when an executable already contains an embedded manifest.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import xml.etree.ElementTree as ET

A3D_CLSID = '{92FA2C24-253C-11D2-90FB-006008A1F441}'
ASM_NS = 'urn:schemas-microsoft-com:asm.v1'
ORIGINAL = bytes.fromhex('B000520053E87095070083C40885C0751A')
PATCHED = bytes.fromhex('B000520053E87095070083C40885C0741A')
MANIFEST_STEM = 'Unofficial.A3D.Local.'


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def make_manifest(game_exe: str) -> bytes:
    """Create a Win32 activation context with a local A3D class factory.

    COM obtains the A3D2 class through the manifest's <comClass> element;
    a3dapi.dll exports DllGetClassObject and implements the COM root. Names
    follow Microsoft's documented registration-free unmanaged COM format.
    """
    ET.register_namespace('', ASM_NS)
    tag = lambda key: f'{{{ASM_NS}}}{key}'
    assembly = ET.Element(tag('assembly'), {'manifestVersion': '1.0'})
    identity = ''.join(c if c.isalnum() or c in '._-' else '_' for c in game_exe)
    ET.SubElement(assembly, tag('assemblyIdentity'), {
        'type': 'win32', 'name': MANIFEST_STEM + identity,
        'version': '1.0.0.0'})
    library = ET.SubElement(assembly, tag('file'), {'name': 'a3dapi.dll'})
    ET.SubElement(library, tag('comClass'), {
        'clsid': A3D_CLSID, 'threadingModel': 'Both'})
    return b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + ET.tostring(assembly, encoding='utf-8') + b'\n'


def patch_alice(game: bytes) -> bytes:
    """Guard the exact known hardware-detection bytes; never blindly patch."""
    before, after = game.count(ORIGINAL), game.count(PATCHED)
    if before == 1 and after == 0:
        return game.replace(ORIGINAL, PATCHED, 1)
    if before == 0 and after == 1:
        return game
    raise ValueError(f'Unknown Alice executable: original={before}, patched={after}; no patch applied')


def image_is_pe32(data: bytes) -> bool:
    """Read DOS+PE headers, no third-party PE parser or execution needed."""
    if len(data) < 0x100 or data[:2] != b'MZ':
        return False
    pe = int.from_bytes(data[0x3c:0x40], 'little')
    if pe+26 > len(data) or data[pe:pe+4] != b'PE\0\0':
        return False
    return int.from_bytes(data[pe+4:pe+6], 'little') == 0x14c and int.from_bytes(data[pe+24:pe+26], 'little') == 0x10b


def atomic_new(path: Path, blob: bytes):
    """Exclusive creation: an existing user file is never silently replaced."""
    with path.open('xb') as f:
        f.write(blob)


def install(exe: Path, payload: Path, kind: str, patch: bool, include_canary: bool=True) -> list[Path]:
    """Install a per-game DLL/manifest set with rollback if any step fails."""
    exe = exe.resolve(strict=True)
    if kind == 'auto':
        kind = { 'alice.exe': 'alice', 'quake3.exe': 'quake3' }.get(exe.name.lower())
        if kind is None:
            raise ValueError('Auto detection requires Alice.exe or quake3.exe; pass --kind explicitly')
    if kind not in ('alice', 'quake3'):
        raise ValueError('Choose --kind alice or --kind quake3')
    if patch and (kind != 'alice' or exe.name.lower() != 'alice.exe'):
        raise ValueError('--patch-alice requires an executable named Alice.exe')
    binaries = ['a3dapi.dll', 'a3d.dll'] if kind == 'quake3' else ['a3dapi.dll']
    data = exe.read_bytes()
    if not image_is_pe32(data):
        raise ValueError('Expected a 32-bit Windows PE executable; refusing to install')
    game_dir = exe.parent
    proposed: dict[Path,bytes] = {}
    candidate = exe
    if patch:
        candidate = game_dir / 'Alice-A3D2.exe'
        proposed[candidate] = patch_alice(data)
    proposed[game_dir / (candidate.name + '.manifest')] = make_manifest(candidate.name)
    for filename in binaries:
        binary = payload / filename
        if not binary.is_file():
            raise FileNotFoundError(f'Missing compiled binary: {binary}')
        blob = binary.read_bytes()
        if not image_is_pe32(blob):
            raise ValueError(f'Invalid PE32 DLL: {binary}')
        proposed[game_dir / filename] = blob
    if include_canary:
        test_exe=payload/'a3d-comtest.exe'
        if test_exe.exists():
            proposed[game_dir/'a3d-comtest.exe'] = test_exe.read_bytes()
            proposed[game_dir/'a3d-comtest.exe.manifest']=make_manifest('a3d-comtest.exe')
    # The uninstaller records exactly what this invocation created.
    record = game_dir/'.a3d-dropin-v040.json'
    if record.exists():
        raise FileExistsError('An A3D installation record already exists; uninstall first')
    duplicates = [str(p) for p in proposed if p.exists()]
    if duplicates:
        raise FileExistsError('Existing game files would be overwritten; nothing changed:\n'+'\n'.join(duplicates))
    made=[]
    try:
        for p,blob in proposed.items():
            atomic_new(p,blob)
            made.append(p)
        atomic_new(record,json.dumps({
            'format':1,'game':str(exe),'mode':kind,
            'created':{p.name:sha256(blob) for p,blob in proposed.items()}
        },indent=2).encode('utf-8')+b'\n')
    except Exception:
        for p in reversed(made):
            p.unlink(missing_ok=True)
        raise
    return list(proposed)


def uninstall(exe: Path):
    """Remove only exactly unchanged files listed in our installation record."""
    directory=exe.resolve(strict=True).parent
    record=directory/'.a3d-dropin-v040.json'
    obj=json.loads(record.read_text())
    expected=obj['created']
    # Verify every checksum before deleting any content.
    for name, digest in expected.items():
        f=directory/name
        if not f.is_file() or sha256(f.read_bytes()) != digest:
            raise ValueError(f'File missing or changed; uninstall aborted: {f}')
    for name in expected:
        (directory/name).unlink()
    record.unlink()
    return sorted(expected)


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--game',type=Path,required=True,help='Path to existing Alice.exe or older quake3.exe')
    ap.add_argument('--payload',type=Path,default=Path(__file__).resolve().parent / 'bin')
    ap.add_argument('--kind',choices=('auto','alice','quake3'),default='auto')
    ap.add_argument('--patch-alice',action='store_true',help='Create a separately named, optional Alice copy with the known hardware check bypass')
    ap.add_argument('--uninstall',action='store_true')
    ns=ap.parse_args(argv)
    try:
        if ns.uninstall:
            print('Removed unchanged emulator files:', ', '.join(uninstall(ns.game)))
        else:
            paths=install(ns.game,ns.payload,ns.kind,ns.patch_alice)
            print('Created game-local files:')
            for path in paths: print('  ',path)
            if ns.patch_alice: print('Launch Alice-A3D2.exe, not the original Alice.exe.')
            print('Run a3d-comtest.exe in the game directory to verify registration-free COM activation.')
            print('No Windows registry changes were made. Manifest activation needs live verification.')
    except (OSError,ValueError,KeyError) as exc:
        ap.exit(1,f'ERROR: {exc}\n')

if __name__ == '__main__':
    main()
