#!/usr/bin/env python3
"""Create auditable, separate v0.7.2 development distributions.

The normal runtime contains only four PE32 binaries. The legacy bridge goes
in a *different* ZIP so it cannot accidentally be installed as part of the
standard configuration. Hash-verified stable ZIPs avoid build-tree clutter.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import zipfile

from security_audit_v072 import audit_runtime

ROOT=Path(__file__).resolve().parents[1]
DEST=Path('/mnt/data')
EPOCH=(2026,11,1,0,0,0)
RUNTIME_FILES=('a3dapi.dll','a3d.dll','a3d-direct.exe','a3d-abi-survey.exe')
SOURCE_DIRS=('win32','experimental','classic2000','remaster2011','native','tools',
             'config','dropin','portable','acoustics','research','docs','release-docs',
             'validation','tests_v070')
EXTS={'.c','.h','.cpp','.hpp','.inc','.def','.py','.sh','.md','.txt','.json',
      '.ps1','.cmd','.cmake','.yml','.yaml','.csv','.in'}
ROOT_FILES=('VERSION','native_activation.inc','README.md','THIRD_PARTY_NOTICES.md',
    'LICENSE_ACOUSTICS.txt','build_and_test_v060.sh','build_from_recipe.py',
    'build_native_windows.ps1','run_alpha_checks.py','run_native_tests.py',
    'verify_alpha_runtime.py','DEBIAN13_PREFLIGHT.sh','DEBIAN13_ABI_SMOKE.sh',
    'SECURITY_AND_SETUP_V072.md','RELEASE_NOTES_V072.md',
    'LEGACY_OFFLINE_ONLY_V072.md','GENERIC_V071_README.md')

def sha256(body):return hashlib.sha256(body).hexdigest()

def write_archive(target:Path, rootname:str,entries:dict[str,bytes]):
    if 'SHA256SUMS.txt' in entries:raise RuntimeError('checksum name collision')
    entries=dict(entries)
    entries['SHA256SUMS.txt']=''.join(
        f'{sha256(data)}  {name}\n' for name,data in sorted(entries.items())).encode()
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,data in sorted(entries.items()):
            info=zipfile.ZipInfo(rootname+'/'+name,EPOCH)
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=((0o100755 if name.endswith('.sh') or name.endswith('.exe') else 0o100644)<<16)
            z.writestr(info,data,compresslevel=9)
    with zipfile.ZipFile(target) as z:
        if z.testzip() is not None:raise RuntimeError('Bad CRC: '+target.name)
        for line in z.read(rootname+'/SHA256SUMS.txt').decode().splitlines():
            digest,name=line.split('  ',1)
            if sha256(z.read(rootname+'/'+name))!=digest:raise RuntimeError('bad packaged hash: '+name)
    return target

def runtime():
    files={n:(ROOT/'runtime-v072'/n).read_bytes() for n in RUNTIME_FILES}
    audit=audit_runtime(files)
    if not audit['passed']:raise RuntimeError('Standard runtime rejected by PE audit: '+str(audit['issues']))
    # Re-run against source-built direct launcher; its byte-equivalence to the
    # pinned reference is demonstrated but not required of all DSP DLLs.
    if (ROOT/'experimental/build/a3d-direct.exe').read_bytes()!=files['a3d-direct.exe']:
        raise RuntimeError('direct launcher build differs from pinned standard launcher')
    return files,audit

def main():
    files,audit=runtime()
    docs={n:(ROOT/n).read_bytes() for n in ('SECURITY_AND_SETUP_V072.md','RELEASE_NOTES_V072.md')}
    tools={f'tools/{n}':(ROOT/'tools'/n).read_bytes() for n in (
        'stage_safe_candidate_v072.py','security_audit_v072.py',
        'scan_a3d_clients.py','inspect_game_v070.py','inspect_alice.py')}
    # Audit JSON is content-derived and is checked with same exact hashes.
    report=(json.dumps(audit,indent=2)+'\n').encode()
    good={'Runtime/'+n:b for n,b in files.items()}
    good.update(docs);good.update(tools);good['SECURITY_AUDIT_v072.json']=report
    std=write_archive(DEST/'A3D_v072_Standard_Runtime.zip','A3D_v072_Standard_Runtime',good)
    # Legacy option is intentionally NOT inside the normal runtime archive.
    legacy={'a3d-launch.exe':(ROOT/'experimental/build/a3d-launch.exe').read_bytes(),
            'LEGACY_OFFLINE_ONLY_V072.md':(ROOT/'LEGACY_OFFLINE_ONLY_V072.md').read_bytes()}
    legacy_file=write_archive(DEST/'A3D_v072_Legacy_Offline_Bridge.zip',
        'A3D_v072_Legacy_Offline_Bridge',legacy)
    src={n:(ROOT/n).read_bytes() for n in ROOT_FILES if (ROOT/n).is_file()}
    for dirname in SOURCE_DIRS:
        for p in (ROOT/dirname).rglob('*'):
            if not p.is_file() or p.is_symlink():continue
            rel=p.relative_to(ROOT).as_posix()
            if any(item in rel.split('/') for item in ('build','__pycache__','bin','.git','history','_dist_v071')):continue
            if p.suffix.lower() not in EXTS and p.name not in ('CMakeLists.txt','LICENSE'):continue
            if p.stat().st_size>8*1024*1024:continue
            src[rel]=p.read_bytes()
    src['BUILD_FROM_SOURCE_V072.md']=b'''# v0.7.2 build and verification (Clang + lld-link, Linux host)

From the extracted source tree:

```sh
bash win32/build.sh
bash win32/build_generic_probe.sh
python3 tools/build_generic_v071.py
```

These produce PE32 DLLs in `win32/build/`, and direct/legacy launcher
EXEs in `experimental/build/`.

For testing the standard runtime audit and staging, place the compiled files
into `runtime-v072/` with exactly these names:
- `a3dapi.dll` and `a3d.dll` from win32/build
- `a3d-direct.exe` from experimental/build
- `a3d-abi-survey.exe` from win32/build

Then:

```sh
python3 tools/security_audit_v072.py runtime-v072
python3 -m unittest discover -s tools -p test_security_v072.py -v
```

The normal kit pins known v0.7.0-alpha engine DLL binaries unchanged, so its
DLL hashes need NOT equal independent rebuilds. The direct launcher matched
byte-for-byte in the original development environment. The entire old 116-
test historical suite expects earlier deploy snapshots not included in the
curated source package. The new six tests can run with rebuilt fixture/runtime.

Neither passing a PE import audit nor bit-reproducibility of any binary
certifies it as malware-free or approved for multiplayer servers.
'''
    source_file=write_archive(DEST/'A3D_v072_Full_Source.zip','A3D_v072_Full_Source',src)
    for p in (std,legacy_file,source_file):
        print(p.name,p.stat().st_size,'bytes', 'SHA256='+sha256(p.read_bytes()))
    with zipfile.ZipFile(std) as z:
        names=z.namelist()
        assert not any('launch.exe' in x or 'BRIDGE' in x for x in names), 'legacy bridge contaminated standard runtime'
        binary=[n for n in names if n.endswith(('.dll','.exe'))]
        assert len(binary)==4,binary

if __name__=='__main__':main()
