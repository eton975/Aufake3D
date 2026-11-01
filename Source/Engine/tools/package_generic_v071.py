#!/usr/bin/env python3
"""Build portable v0.7.1 discovery kit and curated complete project source archive.

Not a claim of gameplay compatibility. Do not include legacy game binaries,
third-party asset rips, transient compiled build stubs or source recordings.
Requires a verified local source tree with compiled Win32 generic binaries.
"""
from pathlib import Path
import hashlib, zipfile, os

ROOT=Path(__file__).resolve().parents[1]
OUT=Path('/mnt/data')
BIN={
    'Generic-A3D2/a3dapi.dll':ROOT/'deploy-v070-alpha/Generic-A3D2/a3dapi.dll',
    'Generic-A3D2/a3d.dll':ROOT/'deploy-v070-alpha/Generic-A3D2/a3d.dll',
    'Generic-A3D2/a3d-launch.exe':ROOT/'experimental/build/a3d-launch.exe',
    'Generic-A3D2/a3d-direct.exe':ROOT/'experimental/build/a3d-direct.exe',
    'Generic-A3D2/a3d-abi-survey.exe':ROOT/'win32/build/a3d-abi-survey.exe',
}
SCRIPTS=['inspect_alice.py','inspect_game_v070.py','scan_a3d_clients.py','stage_generic_candidate.py']
DOCS=['GENERIC_V071_README.md','GENERIC_V071_RELEASE_NOTES.md']
SOURCE_DIRS=['win32','experimental','classic2000','remaster2011','native','tools','config','dropin','portable','acoustics','research','docs','release-docs','validation','tests_v070']
SOURCE_EXTS={'.c','.h','.cpp','.hpp','.inc','.def','.py','.sh','.md','.txt','.json','.ps1','.cmd','.cmake','.yml','.yaml','.csv','.in'}
ROOT_SOURCE=[
    'VERSION','native_activation.inc','GENERIC_V071_README.md','GENERIC_V071_RELEASE_NOTES.md',
    'README.md','THIRD_PARTY_NOTICES.md','LICENSE_ACOUSTICS.txt',
    'build_and_test_v060.sh','build_from_recipe.py','build_native_windows.ps1',
    'run_alpha_checks.py','run_native_tests.py','verify_alpha_runtime.py',
    'DEBIAN13_WINE.md','DEBIAN13_ABI_SMOKE.sh','DEBIAN13_PREFLIGHT.sh',
]

def zput(z, member, body):
    info=zipfile.ZipInfo(member, (2026, 11, 1, 0, 0, 0))
    info.compress_type=zipfile.ZIP_DEFLATED
    info.external_attr=(0o100644<<16)
    z.writestr(info,body,compresslevel=8)

def create_kit():
    target=OUT/'A3D_v071_Generic_DevKit.zip'
    entries={}
    for key,p in BIN.items():
        if not p.is_file(): raise RuntimeError(f'Missing binary: {p}')
        entries[key]=p.read_bytes()
    for name in DOCS:entries[name]=(ROOT/name).read_bytes()
    for name in SCRIPTS:entries['tools/'+name]=(ROOT/'tools'/name).read_bytes()
    # Research target CSV previously generated in package; retain metadata
    # if present but never require it for the runtime.
    csv=ROOT/'_dist_v071/A3D_v071_GenericDev/CANDIDATE_RESEARCH_TARGETS.csv'
    if csv.is_file():entries['CANDIDATE_RESEARCH_TARGETS.csv']=csv.read_bytes()
    checks=''.join(hashlib.sha256(v).hexdigest()+'  '+k+'\n' for k,v in sorted(entries.items()))
    entries['SHA256SUMS.txt']=checks.encode()
    with zipfile.ZipFile(target,'w') as z:
        for k,v in sorted(entries.items()):zput(z,'A3D_v071_Generic_DevKit/'+k,v)
    return target

def create_source():
    target=OUT/'A3D_v071_Generic_Full_Source.zip'
    entries={}
    for name in ROOT_SOURCE:
        p=ROOT/name
        if p.is_file():entries[name]=p.read_bytes()
    for directory in SOURCE_DIRS:
        for p in (ROOT/directory).rglob('*'):
            if not p.is_file() or p.is_symlink():continue
            rel=p.relative_to(ROOT).as_posix()
            if any(x in rel.split('/') for x in ('build','__pycache__','bin','.git','history')):continue
            if p.suffix.lower() not in SOURCE_EXTS and p.name not in ('CMakeLists.txt','LICENSE'):continue
            if p.stat().st_size>8*1024*1024:continue
            entries[rel]=p.read_bytes()
    info="""A3D v0.7.1-dev — FULL SOURCE SNAPSHOT

This is a development tree, NOT a promise of universal A3D support.
The historic A3D1 DirectSound spatial path and A3D3 extensions remain
unimplemented. Existing A3D2 audio game configurations are preserved.

Build (Linux host with Clang + lld-link):
  bash win32/build.sh
  bash win32/build_generic_probe.sh
  python3 tools/build_generic_v071.py

Run the generic development tests using only this source archive:
  python3 -m unittest discover -s tools -p 'test_generic_v071.py' -q

The broader 116-test historical regression suite additionally expects
prior deployment folders and test utilities from the complete project
workspace, which are intentionally omitted from this curated source ZIP.
The full workspace suite was executed separately on the source tree.

This ZIP includes source, not the installed original games or their assets.
The separate DevKit ZIP contains prebuilt PE32/x86 runtime files.
No proprietary game WAV/PK3 assets are distributed.
"""
    entries['SOURCE_README_v071.txt']=info.encode()
    checks=''.join(hashlib.sha256(v).hexdigest()+'  '+k+'\n' for k,v in sorted(entries.items()))
    entries['SHA256SUMS.txt']=checks.encode()
    with zipfile.ZipFile(target,'w') as z:
        for k,v in sorted(entries.items()):zput(z,'A3D_v071_Generic_Source/'+k,v)
    return target

def verify(path):
    with zipfile.ZipFile(path) as z:
        if z.testzip():raise RuntimeError('Archive CRC failure')
        prefix='A3D_v071_Generic_DevKit/' if 'DevKit' in path.name else 'A3D_v071_Generic_Source/'
        lines=z.read(prefix+'SHA256SUMS.txt').decode().splitlines()
        for line in lines:
            hexsum,member=line.split('  ',1)
            if hashlib.sha256(z.read(prefix+member)).hexdigest()!=hexsum:
                raise RuntimeError('Bad hash: '+member)
        print(path.name,len(z.namelist()),'files',path.stat().st_size,'bytes, sha256 verified')

if __name__=='__main__':
    for path in (create_kit(),create_source()):verify(path)
