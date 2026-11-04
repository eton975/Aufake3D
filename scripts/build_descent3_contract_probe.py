#!/usr/bin/env python3
"""Build the stand-alone, game-free Win32 Descent 3 A3D2 COM probe.

Uses Clang/lld-link only. No retail files, game patches, registry writes,
original Aureal binaries or GPL sources are included or modified. Creates
exactly one console PE32 in dist/experimental-descent3. The A3D2 DLL itself is
built by the existing main build system and deliberately left untouched.
"""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "Source" / "Engine" / "win32"
DEST = ROOT / "dist" / "experimental-descent3"
NAME = "a3d-descent3-contract-probe.exe"
IMPORTS = (
    "LoadLibraryA@4", "GetProcAddress@8", "FreeLibrary@4",
    "ExitProcess@4", "GetStdHandle@4", "WriteFile@20",
    "Sleep@4", "GetCommandLineA@0",
)


def build(tempdir: Path, clang: str, linker: str) -> bytes:
    def run(cmd: list[str]) -> None:
        subprocess.run(cmd, cwd=SRC, check=True)

    lib = tempdir / "kernel32-probe.lib"
    run([
        linker, "/dll", "/noentry", "/machine:x86",
        "/def:" + str(SRC / "descent3_probe_kernel32.def"),
        "/out:" + str(tempdir / "kernel32-stub.dll"),
        "/implib:" + str(lib),
    ])
    obj = tempdir / "descent3-probe.obj"
    run([
        clang, "-target", "i686-pc-windows-msvc", "-ffreestanding",
        "-fno-stack-protector", "-fno-builtin", "-O2", "-Wall",
        "-Wextra", "-Werror", "-c", "descent3_contract_probe.c",
        "-o", str(obj),
    ])
    exe = tempdir / NAME
    run([
        linker, "/subsystem:console", "/machine:x86", "/nodefaultlib",
        "/entry:start@0", "/timestamp:0", "/out:" + str(exe),
        str(obj), str(lib),
        *[f"/alternatename:__imp__{name}=__imp__{name.split('@')[0]}"
          for name in IMPORTS],
    ])
    data = exe.read_bytes()
    if data[:2] != b"MZ" or len(data) < 256:
        raise RuntimeError("not a PE executable")
    off = struct.unpack_from("<I", data, 0x3C)[0]
    if data[off:off+4] != b"PE\x00\x00" or struct.unpack_from("<H", data, off+4)[0] != 0x14c:
        raise RuntimeError("not a Windows PE32/x86 executable")
    return data


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--clang", default=os.environ.get("CC", "clang"))
    ap.add_argument("--linker", default=os.environ.get("LINK", "lld-link"))
    ap.add_argument("--out", type=Path, default=DEST / NAME)
    args = ap.parse_args()
    for tool in (args.clang, args.linker):
        if not shutil.which(tool) and not Path(tool).is_file():
            ap.error(f"missing compiler/linker: {tool}")
    with tempfile.TemporaryDirectory(prefix="aufake3d-descent3-a-") as aa, \
         tempfile.TemporaryDirectory(prefix="aufake3d-descent3-b-") as bb:
        a = build(Path(aa), args.clang, args.linker)
        b = build(Path(bb), args.clang, args.linker)
    if a != b:
        raise RuntimeError("probe builds differ byte-for-byte")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(a)
    print("PASS: two independent PE32/i386 probe builds are identical")
    print(f"{hashlib.sha256(a).hexdigest()}  {args.out}")
    print("NOTE: this proves neither Wine runtime success nor Descent 3 gameplay compatibility")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
