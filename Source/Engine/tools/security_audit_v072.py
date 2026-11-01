#!/usr/bin/env python3
"""Audit PE32 imports and ZIP composition for the A3D transparent runtime.

This is a *static* import inventory, not a malware scan, code signature, or
anti-cheat compatibility certification. An imported API is a useful clue,
but dynamic resolution, other modules, and actual runtime behavior remain
outside this test. Fail closed for malformed PE import tables.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import struct
import zipfile

# Remote modification and code-execution APIs are deliberately not needed by
# the normal app-local audio DLLs or their conventional process launcher.
# Presence in these binaries is grounds to reject a 'standard runtime' build.
RESTRICTED = frozenset(s.casefold() for s in (
    'OpenProcess','WriteProcessMemory','ReadProcessMemory','VirtualAllocEx',
    'VirtualProtectEx','GetThreadContext','SetThreadContext',
    'CreateRemoteThread','CreateRemoteThreadEx','QueueUserAPC',
    'NtWriteVirtualMemory','NtReadVirtualMemory','NtCreateThreadEx',
    'RtlCreateUserThread','DebugActiveProcess','SetWindowsHookExA',
    'SetWindowsHookExW','ResumeThread',
))

class PEError(ValueError): pass


def import_table(blob: bytes) -> tuple[str, list[str]]:
    """Return architecture and named import functions from a Windows PE.

    No third-party Python packages or external command-line tools required.
    Both PE32 and PE32+ can be inspected; runtime release is intentionally x86.
    """
    def need(off: int, size: int):
        if off < 0 or size < 0 or off + size > len(blob):
            raise PEError('truncated or out-of-range PE structure')
    def u16(off: int) -> int:
        need(off,2);return struct.unpack_from('<H',blob,off)[0]
    def u32(off: int) -> int:
        need(off,4);return struct.unpack_from('<I',blob,off)[0]
    def u64(off: int) -> int:
        need(off,8);return struct.unpack_from('<Q',blob,off)[0]
    def cstr(off: int) -> str:
        need(off,1)
        end=blob.find(b'\0',off,min(len(blob),off+2048))
        if end < 0: raise PEError('unterminated string')
        return blob[off:end].decode('ascii','replace')
    if len(blob)<0x100 or blob[:2]!=b'MZ':raise PEError('not a PE file')
    pe=u32(0x3c);need(pe,24)
    if blob[pe:pe+4]!=b'PE\0\0':raise PEError('missing PE signature')
    machine=u16(pe+4); sections=u16(pe+6); opt_size=u16(pe+20)
    opt=pe+24;need(opt,opt_size)
    magic=u16(opt)
    if magic==0x10b:
        arch='x86' if machine==0x14c else f'PE32 machine {machine:04x}'
        directory=opt+96;count=u32(opt+92);step=4;ordinal_mask=0x80000000
    elif magic==0x20b:
        arch='x64' if machine==0x8664 else f'PE32+ machine {machine:04x}'
        directory=opt+112;count=u32(opt+108);step=8;ordinal_mask=0x8000000000000000
    else:raise PEError('unknown PE optional header magic')
    sec=[]
    for i in range(sections):
        at=opt+opt_size+i*40;need(at,40)
        vsize=u32(at+8);va=u32(at+12);rawsz=u32(at+16);raw=u32(at+20)
        sec.append((va,max(vsize,rawsz),raw,rawsz))
    def rva(r:int) -> int:
        for va,span,raw,rawsz in sec:
            if va<=r<va+span and r-va<rawsz:
                off=raw+(r-va);need(off,1);return off
        raise PEError(f'unmapped PE RVA 0x{r:x}')
    if count<2 or directory+16>opt+opt_size:
        return arch,[]
    import_rva=u32(directory+8)
    if not import_rva:return arch,[]
    out=[]
    pos=rva(import_rva)
    for j in range(2048):
        need(pos+j*20,20)
        desc=pos+j*20
        lookup=u32(desc);name=u32(desc+12);iat=u32(desc+16)
        if not (lookup or name or iat):break
        dll=cstr(rva(name))
        table=rva(lookup or iat)
        for n in range(8192):
            thunk=u32(table+n*step) if step==4 else u64(table+n*step)
            if thunk==0:break
            if thunk & ordinal_mask:continue
            fname=cstr(rva(thunk)+2)
            out.append(f'{dll}!{fname}')
        else:raise PEError('import lookup table too large')
    else:raise PEError('import descriptor table too large')
    return arch,out


def audit_runtime(files: dict[str,bytes]) -> dict:
    issues=[];report=[]
    expected={'a3dapi.dll','a3d.dll','a3d-direct.exe','a3d-abi-survey.exe'}
    names={Path(k).name.lower() for k in files}
    if names!=expected:
        issues.append(f'expected exactly {sorted(expected)}, got {sorted(names)}')
    for name,blob in sorted(files.items()):
        try:arch, imports=import_table(blob)
        except PEError as err:
            issues.append(f'{name}: {err}');continue
        if arch!='x86':issues.append(f'{name}: runtime must be PE32 x86, got {arch}')
        hits=sorted(x for x in imports if x.split('!',1)[-1].casefold() in RESTRICTED)
        if hits:issues.append(f'{name}: prohibited imports {hits}')
        report.append({'file':name,'arch':arch,'sha256':hashlib.sha256(blob).hexdigest(),
                       'import_count':len(imports),'imports':imports,'restricted_imports':hits})
    return {'policy':'A3D v0.7.2 standard runtime (static imports only)',
            'passed':not issues,'issues':issues,'files':report,
            'disclaimer':'Not a malware, behavior, or anti-cheat approval test.'}


def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('directory',type=Path,help='directory with exactly four standard PE32 runtime files')
    a.add_argument('--output',type=Path)
    args=a.parse_args()
    files={p.name:p.read_bytes() for p in args.directory.iterdir() if p.is_file() and p.suffix.lower() in ('.exe','.dll')}
    result=audit_runtime(files)
    output=json.dumps(result,indent=2)+'\n'
    if args.output:args.output.write_text(output,encoding='utf-8')
    else:print(output)
    raise SystemExit(0 if result['passed'] else 1)

if __name__=='__main__':main()
