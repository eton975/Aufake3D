#!/usr/bin/env python3
# v0.6.0 SOURCE COMMENTARY — Game-neutral Python installer
# Statically inspects PE architecture, selects game-local DLL payloads, emits a
# registration-free COM manifest, refuses collisions, and records cryptographic hashes
# for safe uninstall. Profile signature detection is heuristic, not a claim that a
# named game truly supports any specific Aureal generation.
"""Portable game-local Aureal A3D 1.x/2.x compatibility frontends.

This installer never patches the game executable or registry, refuses existing
DLL/manifest collisions, and records hashes for safe verification/uninstall.
It installs independent legacy (a3d.dll) and COM (a3dapi.dll) frontends.
It does not claim that those frontends implement every original Aureal feature.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

VERSION = "0.6.0"
RECORD = ".a3d-portable-v060.json"
GUID = "{92FA2C24-253C-11D2-90FB-006008A1F441}"
NS = "urn:schemas-microsoft-com:asm.v1"
# Only this exact 2011 remaster has been disassembled and signature mapped.
# The selector bridge additionally checks instructions in the suspended child.
ALICE2011_SHA256 = "08bcbe4b549633b24c90a1ab36bf516bd8873432c68b37248c98ee4225506e50"
ALICE2011_MODULES = ("winmm.dll", "VorpalFix.ini", "SndDrivers/mss32.dll", "SndDrivers/mssa3d2.m3d")


def remaster_prerequisites(exe: Path) -> list[str]:
    """Read-only inventory; never replace VorpalFix or proprietary Miles files."""
    return [name for name in ALICE2011_MODULES if not (exe.parent / name).is_file()]



def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pe_info(data: bytes) -> dict:
    """Read PE header and import-library names without executing the binary."""
    if len(data) < 128 or data[:2] != b"MZ":
        raise ValueError("not a Windows PE executable")
    off = int.from_bytes(data[60:64], "little")
    if off < 0 or off + 26 > len(data) or data[off:off+4] != b"PE\0\0":
        raise ValueError("invalid PE header")
    machine = int.from_bytes(data[off+4:off+6], "little")
    magic = int.from_bytes(data[off+24:off+26], "little")
    if machine not in (0x14c, 0x8664) or magic not in (0x10b, 0x20b):
        raise ValueError(f"unsupported PE architecture (machine=0x{machine:x}, magic=0x{magic:x})")
    return {"architecture": "x86" if machine == 0x14c else "x64",
            "machine": machine, "sha256": sha(data)}


def read_exe(exe: Path) -> tuple[bytes, dict]:
    if not exe.is_file():
        raise ValueError(f"game executable not found: {exe}")
    data = exe.read_bytes()
    return data, pe_info(data)


def profile_report(exe: Path, blob: bytes, profile: str) -> dict:
    low = blob.lower()
    # These are *hints*, not game identification. Never assume a renamed executable
    # is Quake III; the previously submitted 'quake3.exe' was actually Alice.
    q3_hint = b"s_enable_a3d" in low or b"s_usinga3d" in low
    alice_hint = b"aureal a3d interactive" in low and b"s_milesdriver" in low
    miles_hint = b"mss32.dll" in low or b"s_milesdriver" in low
    if profile == "quake3" and alice_hint:
        raise ValueError("This executable contains Alice/Miles selector signatures, not a verified Quake III binary. Refusing Quake III profile.")
    if profile == "quake3" and exe.name.lower() != 'quake3.exe':
        raise ValueError("Quake III profile requires the genuine file named quake3.exe")
    warnings = []
    if profile == 'alice2011':
        if exe.name.lower() != 'alice.exe':
            raise ValueError('Alice 2011 profile requires alice.exe beside VorpalFix winmm.dll')
        if sha(blob) != ALICE2011_SHA256:
            raise ValueError('Unknown Alice 2011 executable SHA256; refusing RAM-only selector bridge for unmatched build')
        if not alice_hint or not miles_hint:
            raise ValueError('Alice 2011 sound-selector signatures are absent')
        absent = remaster_prerequisites(exe)
        if absent:
            warnings.append('Missing Alice 2011/VorpalFix/Miles files: ' + ', '.join(absent))
        warnings.append('2011 remaster uses RAM-only selector bridge; this is not in-game validation')
    if profile == 'quake3' and not q3_hint:
        warnings.append("Quake III A3D commands not detected; compressed or later non-A3D build may not call the wrapper")
    if profile == 'alice':
        warnings.append("Classic Alice 2000 A3D2 requires the included RAM-only selector bridge; launch via run_alice2000_wine.sh (game EXE unchanged on disk)")
    if not (q3_hint or miles_hint or b'a3d.dll' in low or b'a3dapi.dll' in low):
        warnings.append("No A3D signature found by static scan; loading cannot be assumed")
    return {"quake3_a3d_markers": q3_hint, "alice_miles_markers": alice_hint,
            "miles_markers": miles_hint, "warnings": warnings, "alice2011_missing": remaster_prerequisites(exe) if profile == "alice2011" else []}


def manifest(executable_name: str) -> bytes:
    ET.register_namespace("", NS)
    tag = lambda name: "{%s}%s" % (NS, name)
    root = ET.Element(tag('assembly'), {"manifestVersion":"1.0"})
    clean_name = ''.join(ch if ch.isalnum() or ch in '._-' else '_' for ch in executable_name)
    ET.SubElement(root, tag('assemblyIdentity'), {'type':'win32',
        'name':'Unofficial.A3D.Portable.' + clean_name, 'version':'1.0.0.0'})
    dll = ET.SubElement(root, tag('file'), {'name':'a3dapi.dll'})
    ET.SubElement(dll, tag('comClass'), {'clsid':GUID,'threadingModel':'Both'})
    return b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + ET.tostring(root, encoding='utf-8') + b'\n'


def payloads(exe: Path, bin_dir: Path, mode: str, tools: bool, profile: str = "generic") -> dict[Path, bytes]:
    outputs = {}
    for name in ({'legacy':['a3d.dll'], 'com':['a3dapi.dll'],
                  'both':['a3d.dll','a3dapi.dll']}[mode]):
        p = bin_dir / name
        if not p.is_file():
            raise ValueError(f"missing compiled DLL: {p}")
        content = p.read_bytes()
        info = pe_info(content)
        if info['architecture'] != 'x86':
            raise ValueError(f"DLL {p} must be Win32/x86")
        outputs[exe.parent / name] = content
    if mode in ('com','both'):
        outputs[exe.parent / (exe.name + '.manifest')] = manifest(exe.name)
    if profile == 'alice' and mode in ('com', 'both'):
        # Classic Alice 2000's stock selector does not recognise the a3d2
        # token. The game-specific bridge supplies the mapping in the
        # suspended child process only. This bridge is not interchangeable
        # with the 2011 remaster bridge.
        name = 'alice-a3d-bridge.exe'
        bridge = bin_dir / name
        if not bridge.is_file() or pe_info(bridge.read_bytes())['architecture'] != 'x86':
            raise ValueError('Missing 32-bit classic Alice 2000 RAM selector bridge')
        outputs[exe.parent / name] = bridge.read_bytes()
        # Registration-free COM activation must also apply to the BRIDGE
        # launcher process, not solely to alice.exe created as its child.
        outputs[exe.parent / (name + '.manifest')] = manifest(name)
    if profile == 'alice2011':
        # Never overwrite or masquerade as the remaster's own alice.exe or
        # VorpalFix's winmm.dll. A separate bridge executable owns our patch.
        name = 'alice-a3d2011-bridge.exe'
        bridge = bin_dir / name
        if not bridge.is_file() or pe_info(bridge.read_bytes())['architecture'] != 'x86':
            raise ValueError('Missing 32-bit Alice 2011 RAM selector bridge')
        outputs[exe.parent / name] = bridge.read_bytes()
    if tools:
        for program in ('a3d-legacy-probe.exe','a3d-comtest.exe'):
            if program == 'a3d-comtest.exe' and mode == 'legacy':
                continue
            if program == 'a3d-legacy-probe.exe' and mode == 'com':
                continue
            f=bin_dir / program
            if not f.is_file():
                raise ValueError(f"missing diagnostic program: {f}")
            content=f.read_bytes()
            if pe_info(content)['architecture'] != 'x86':
                raise ValueError("diagnostic program must be x86")
            outputs[exe.parent / program] = content
            if program == 'a3d-comtest.exe':
                outputs[exe.parent / (program + '.manifest')] = manifest(program)
    return outputs


def install(exe: Path, bindir: Path, mode: str, profile: str, tools: bool = True) -> dict:
    exe = exe.resolve(strict=True)
    data, info = read_exe(exe)
    if info['architecture'] != 'x86':
        raise ValueError("Current emulators are 32-bit only; no 64-bit build is provided")
    report = profile_report(exe, data, profile)
    record = exe.parent / RECORD
    if profile == 'alice2011':
        missing = remaster_prerequisites(exe)
        if missing:
            raise ValueError('Alice 2011 install prerequisites missing (not overwritten): ' + ', '.join(missing))
        if mode == 'legacy':
            raise ValueError('Alice 2011 A3D2 requires mode com or both, not legacy')
    new = payloads(exe, bindir, mode, tools, profile)
    blocked = [str(p) for p in [record, *new] if p.exists()]
    if blocked:
        raise FileExistsError("Existing files found; nothing installed. First back them up or uninstall their existing owner:\n" + '\n'.join(blocked))
    hashes = {p.name:sha(b) for p,b in new.items()}
    receipt = {'format':1,'version':VERSION,'game':exe.name,'game_sha256':info['sha256'],
               'profile':profile,'mode':mode,'created':hashes}
    created = []
    try:
        for p,b in new.items():
            with p.open('xb') as fd:
                fd.write(b)
            created.append(p)
        with record.open('xb') as fd:
            fd.write((json.dumps(receipt,indent=2,sort_keys=True)+'\n').encode())
        created.append(record)
    except BaseException:
        for path in reversed(created):
            path.unlink(missing_ok=True)
        raise
    return {'receipt':receipt,'report':report,'installed':[str(p) for p in new]}


def verify_or_uninstall(exe: Path, delete: bool) -> dict:
    exe = exe.resolve(strict=True)
    receipt_path = exe.parent / RECORD
    receipt = json.loads(receipt_path.read_text(encoding='utf8'))
    if receipt['game'] != exe.name:
        raise ValueError("record belongs to another executable")
    if sha(exe.read_bytes()) != receipt['game_sha256']:
        raise ValueError("game executable changed since installation; operation aborted")
    if receipt['format'] != 1:
        raise ValueError("unknown receipt format")
    for name, digest in receipt['created'].items():
        if '/' in name or '\\' in name or name in ('.', '..'):
            raise ValueError("unsafe file name in receipt")
        file = exe.parent / name
        if not file.is_file() or sha(file.read_bytes()) != digest:
            raise ValueError(f"missing/modified installed file: {file}; no files were removed")
    if delete:
        for name in receipt['created']:
            (exe.parent / name).unlink()
        receipt_path.unlink()
    return {'verified':len(receipt['created']), 'uninstalled':delete,'mode':receipt['mode']}


def main(argv=None) -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['inspect','install','verify','uninstall'])
    p.add_argument('game',type=Path)
    p.add_argument('--profile',choices=['generic','quake3','alice','alice2011'],default='generic')
    p.add_argument('--mode',choices=['both','legacy','com'],default='both')
    p.add_argument('--bin-dir',type=Path,default=Path(__file__).resolve().parent/'bin')
    p.add_argument('--no-probes',action='store_true')
    args=p.parse_args(argv)
    try:
        if args.command == 'inspect':
            data,info=read_exe(args.game)
            info.update(profile_report(args.game,data,args.profile))
            print(json.dumps(info,indent=2))
        elif args.command == 'install':
            print(json.dumps(install(args.game,args.bin_dir,args.mode,args.profile,not args.no_probes),indent=2))
        else:
            print(json.dumps(verify_or_uninstall(args.game,args.command=='uninstall'),indent=2))
        return 0
    except (OSError,ValueError,KeyError,json.JSONDecodeError) as exc:
        print('ERROR:',str(exc),file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
